from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_NAME,
    CONF_DEVICE_SERIAL,
    CONF_DEVICES,
    DOMAIN,
    MANUFACTURER,
    MODEL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    mqtt_client = hass.data[DOMAIN][f"{entry.entry_id}_mqtt_client"]
    devices = entry.data.get(CONF_DEVICES, [])

    entities = []
    for device in devices:
        entities.append(NoLongerEvilFan(hass, mqtt_client, device, entry))

    async_add_entities(entities, True)


class NoLongerEvilFan(FanEntity):
    _attr_has_entity_name = True
    _attr_name = "Fan"

    def __init__(
        self,
        hass: HomeAssistant,
        mqtt_client: Any,
        device: dict[str, Any],
        entry: ConfigEntry,
    ) -> None:
        self.hass = hass
        self._mqtt_client = mqtt_client
        self._device = device
        self._entry = entry

        # Device info
        self._serial = device[CONF_DEVICE_SERIAL]
        self._device_name = device[CONF_DEVICE_NAME]

        # State
        self._is_on: bool = False

        # Features
        self._attr_supported_features = (
            FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        )

        # Subscribe to MQTT topic
        self._subscribe_to_topic()

    def _subscribe_to_topic(self) -> None:
        topic = self._mqtt_client.get_topic(self._serial, "device", "fan_timer_active")
        self._mqtt_client.subscribe(topic, self._handle_fan_state)

    def _handle_fan_state(self, topic: str, payload: str) -> None:
        try:
            value = json.loads(payload) if payload.startswith(("{", "[")) else payload
            # Convert to boolean
            if isinstance(value, bool):
                self._is_on = value
            elif isinstance(value, str):
                self._is_on = value.lower() in ("true", "1", "on")
            else:
                self._is_on = bool(value)

            self.schedule_update_ha_state()
            _LOGGER.debug(
                "Updated fan state for %s: %s",
                self._serial,
                "on" if self._is_on else "off",
            )
        except (ValueError, TypeError) as err:
            _LOGGER.error("Failed to parse fan state: %s", err)

    @property
    def unique_id(self) -> str:
        return f"{self._serial}_fan"

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._serial)},
            "name": self._device_name,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "serial_number": self._serial,
        }

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        topic = self._mqtt_client.get_set_topic(
            self._serial, "device", "fan_timer_active"
        )
        await self.hass.async_add_executor_job(self._mqtt_client.publish, topic, True)
        _LOGGER.debug("Set fan on for %s", self._serial)

    async def async_turn_off(self, **kwargs: Any) -> None:
        topic = self._mqtt_client.get_set_topic(
            self._serial, "device", "fan_timer_active"
        )
        await self.hass.async_add_executor_job(self._mqtt_client.publish, topic, False)
        _LOGGER.debug("Set fan off for %s", self._serial)
