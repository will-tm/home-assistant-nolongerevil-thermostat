from __future__ import annotations

import logging
from typing import Any

import paho.mqtt.client as mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_DEVICES,
    CONF_MQTT_BROKER,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_PORT,
    CONF_MQTT_USERNAME,
    CONF_TOPIC_PREFIX,
    DEFAULT_MQTT_PORT,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.FAN, Platform.BINARY_SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("Setting up No Longer Evil Thermostat integration")

    # Store config entry data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Set up MQTT connection
    mqtt_client = NoLongerEvilMQTTClient(hass, entry)
    await hass.async_add_executor_job(mqtt_client.connect)

    # Store the MQTT client for cleanup later
    hass.data[DOMAIN][f"{entry.entry_id}_mqtt_client"] = mqtt_client

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("Unloading No Longer Evil Thermostat integration")

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Disconnect MQTT client
        mqtt_client = hass.data[DOMAIN].get(f"{entry.entry_id}_mqtt_client")
        if mqtt_client:
            await hass.async_add_executor_job(mqtt_client.disconnect)
            hass.data[DOMAIN].pop(f"{entry.entry_id}_mqtt_client")

        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class NoLongerEvilMQTTClient:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.client: mqtt.Client | None = None
        self._callbacks: dict[str, list[callable]] = {}

        # Extract configuration
        self.broker = entry.data[CONF_MQTT_BROKER]
        self.port = entry.data.get(CONF_MQTT_PORT, DEFAULT_MQTT_PORT)
        self.username = entry.data.get(CONF_MQTT_USERNAME)
        self.password = entry.data.get(CONF_MQTT_PASSWORD)
        self.topic_prefix = entry.data.get(CONF_TOPIC_PREFIX, DEFAULT_TOPIC_PREFIX)
        self.devices = entry.data.get(CONF_DEVICES, [])

    def connect(self) -> None:
        client_id = f"ha-nolongerevil-{self.entry.entry_id}"
        self.client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)

        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        _LOGGER.info("Connecting to MQTT broker: %s:%s", self.broker, self.port)
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
        except Exception as err:
            _LOGGER.error("Failed to connect to MQTT broker: %s", err)
            raise

    def disconnect(self) -> None:
        if self.client:
            _LOGGER.info("Disconnecting from MQTT broker")
            self.client.loop_stop()
            self.client.disconnect()

    def _on_connect(
        self, client: mqtt.Client, userdata: Any, flags: dict, rc: int
    ) -> None:
        if rc == 0:
            _LOGGER.info("Connected to MQTT broker")
            # Subscribe to all device topics
            self._subscribe_to_topics()
        else:
            _LOGGER.error("Failed to connect to MQTT broker with code: %s", rc)

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int) -> None:
        if rc != 0:
            _LOGGER.warning("Unexpected MQTT disconnection. Reconnecting...")

    def _on_message(
        self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage
    ) -> None:
        topic = msg.topic
        payload = msg.payload.decode("utf-8")

        _LOGGER.debug("Received MQTT message: %s = %s", topic, payload)

        # Call registered callbacks for this topic
        if topic in self._callbacks:
            for callback in self._callbacks[topic]:
                callback(topic, payload)

    def _subscribe_to_topics(self) -> None:
        if not self.client:
            return

        for device in self.devices:
            serial = device.get("serial")
            if not serial:
                continue

            topics = [
                f"{self.topic_prefix}/{serial}/device/current_temperature",
                f"{self.topic_prefix}/{serial}/shared/target_temperature",
                f"{self.topic_prefix}/{serial}/shared/target_temperature_low",
                f"{self.topic_prefix}/{serial}/shared/target_temperature_high",
                f"{self.topic_prefix}/{serial}/shared/target_temperature_type",
                f"{self.topic_prefix}/{serial}/device/fan_timer_active",
                f"{self.topic_prefix}/{serial}/device/away",
                f"{self.topic_prefix}/{serial}/availability",
            ]

            for topic in topics:
                result = self.client.subscribe(topic)
                if result[0] == mqtt.MQTT_ERR_SUCCESS:
                    _LOGGER.debug("Subscribed to topic: %s", topic)
                else:
                    _LOGGER.error("Failed to subscribe to topic: %s", topic)

    def subscribe(self, topic: str, callback: callable) -> None:
        if topic not in self._callbacks:
            self._callbacks[topic] = []
        self._callbacks[topic].append(callback)

    def publish(self, topic: str, payload: str | int | float | bool) -> None:
        if not self.client:
            _LOGGER.error("MQTT client not connected")
            return

        payload_str = str(payload) if not isinstance(payload, str) else payload

        _LOGGER.debug("Publishing MQTT message: %s = %s", topic, payload_str)

        result = self.client.publish(topic, payload_str, qos=1)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            _LOGGER.error("Failed to publish to topic %s: %s", topic, result.rc)

    def get_topic(self, serial: str, object_type: str, field: str) -> str:
        return f"{self.topic_prefix}/{serial}/{object_type}/{field}"

    def get_set_topic(self, serial: str, object_type: str, field: str) -> str:
        return f"{self.topic_prefix}/{serial}/{object_type}/{field}/set"
