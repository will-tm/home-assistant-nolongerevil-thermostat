"""Climate platform for No Longer Evil Thermostat."""
from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_NAME,
    CONF_DEVICE_SERIAL,
    CONF_DEVICES,
    CONF_TEMPERATURE_UNIT,
    DEFAULT_TEMPERATURE_UNIT,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    NEST_MODE_COOL,
    NEST_MODE_HEAT,
    NEST_MODE_OFF,
    NEST_MODE_RANGE,
    TOPIC_CURRENT_TEMP,
    TOPIC_TARGET_TEMP,
    TOPIC_TARGET_TEMP_HIGH,
    TOPIC_TARGET_TEMP_LOW,
    TOPIC_TARGET_TEMP_TYPE,
)

_LOGGER = logging.getLogger(__name__)

# Temperature threshold for determining if actively heating/cooling
TEMP_THRESHOLD = 0.5

# HVAC mode mapping
NEST_TO_HA_MODE = {
    NEST_MODE_OFF: HVACMode.OFF,
    NEST_MODE_HEAT: HVACMode.HEAT,
    NEST_MODE_COOL: HVACMode.COOL,
    NEST_MODE_RANGE: HVACMode.HEAT_COOL,
}

HA_TO_NEST_MODE = {
    HVACMode.OFF: NEST_MODE_OFF,
    HVACMode.HEAT: NEST_MODE_HEAT,
    HVACMode.COOL: NEST_MODE_COOL,
    HVACMode.HEAT_COOL: NEST_MODE_RANGE,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up No Longer Evil Thermostat climate entities."""
    mqtt_client = hass.data[DOMAIN][f"{entry.entry_id}_mqtt_client"]
    devices = entry.data.get(CONF_DEVICES, [])

    entities = []
    for device in devices:
        entities.append(NoLongerEvilClimate(hass, mqtt_client, device, entry))

    async_add_entities(entities, True)


class NoLongerEvilClimate(ClimateEntity):
    """Representation of a No Longer Evil Thermostat climate device."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        hass: HomeAssistant,
        mqtt_client: Any,
        device: dict[str, Any],
        entry: ConfigEntry,
    ) -> None:
        """Initialize the climate device."""
        self.hass = hass
        self._mqtt_client = mqtt_client
        self._device = device
        self._entry = entry

        # Device info
        self._serial = device[CONF_DEVICE_SERIAL]
        self._device_name = device[CONF_DEVICE_NAME]
        temp_unit = device.get(CONF_TEMPERATURE_UNIT, DEFAULT_TEMPERATURE_UNIT)
        self._temp_unit = (
            UnitOfTemperature.FAHRENHEIT
            if temp_unit.lower() == "fahrenheit"
            else UnitOfTemperature.CELSIUS
        )

        # State
        self._current_temperature: float | None = None
        self._target_temperature: float | None = None
        self._target_temperature_low: float | None = None
        self._target_temperature_high: float | None = None
        self._hvac_mode: HVACMode = HVACMode.OFF
        self._hvac_action: HVACAction = HVACAction.OFF

        # Features
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        )
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.HEAT,
            HVACMode.COOL,
            HVACMode.HEAT_COOL,
        ]
        self._attr_temperature_unit = self._temp_unit

        # Subscribe to MQTT topics
        self._subscribe_to_topics()

    def _subscribe_to_topics(self) -> None:
        """Subscribe to MQTT topics for this device."""
        # Current temperature
        topic = self._mqtt_client.get_topic(self._serial, "device", "current_temperature")
        self._mqtt_client.subscribe(topic, self._handle_current_temperature)

        # Target temperature
        topic = self._mqtt_client.get_topic(self._serial, "shared", "target_temperature")
        self._mqtt_client.subscribe(topic, self._handle_target_temperature)

        # Target temperature low
        topic = self._mqtt_client.get_topic(self._serial, "shared", "target_temperature_low")
        self._mqtt_client.subscribe(topic, self._handle_target_temperature_low)

        # Target temperature high
        topic = self._mqtt_client.get_topic(self._serial, "shared", "target_temperature_high")
        self._mqtt_client.subscribe(topic, self._handle_target_temperature_high)

        # HVAC mode
        topic = self._mqtt_client.get_topic(self._serial, "shared", "target_temperature_type")
        self._mqtt_client.subscribe(topic, self._handle_hvac_mode)

    def _handle_current_temperature(self, topic: str, payload: str) -> None:
        """Handle current temperature update."""
        try:
            value = json.loads(payload) if payload.startswith(("{", "[")) else float(payload)
            self._current_temperature = float(value)
            self._update_hvac_action()
            self.schedule_update_ha_state()
            _LOGGER.debug(
                "Updated current temperature for %s: %s°C",
                self._serial,
                self._current_temperature,
            )
        except (ValueError, TypeError) as err:
            _LOGGER.error("Failed to parse current temperature: %s", err)

    def _handle_target_temperature(self, topic: str, payload: str) -> None:
        """Handle target temperature update."""
        try:
            value = json.loads(payload) if payload.startswith(("{", "[")) else float(payload)
            self._target_temperature = float(value)
            self.schedule_update_ha_state()
            _LOGGER.debug(
                "Updated target temperature for %s: %s°C",
                self._serial,
                self._target_temperature,
            )
        except (ValueError, TypeError) as err:
            _LOGGER.error("Failed to parse target temperature: %s", err)

    def _handle_target_temperature_low(self, topic: str, payload: str) -> None:
        """Handle target temperature low update."""
        try:
            value = json.loads(payload) if payload.startswith(("{", "[")) else float(payload)
            self._target_temperature_low = float(value)
            self.schedule_update_ha_state()
            _LOGGER.debug(
                "Updated target temperature low for %s: %s°C",
                self._serial,
                self._target_temperature_low,
            )
        except (ValueError, TypeError) as err:
            _LOGGER.error("Failed to parse target temperature low: %s", err)

    def _handle_target_temperature_high(self, topic: str, payload: str) -> None:
        """Handle target temperature high update."""
        try:
            value = json.loads(payload) if payload.startswith(("{", "[")) else float(payload)
            self._target_temperature_high = float(value)
            self.schedule_update_ha_state()
            _LOGGER.debug(
                "Updated target temperature high for %s: %s°C",
                self._serial,
                self._target_temperature_high,
            )
        except (ValueError, TypeError) as err:
            _LOGGER.error("Failed to parse target temperature high: %s", err)

    def _handle_hvac_mode(self, topic: str, payload: str) -> None:
        """Handle HVAC mode update."""
        try:
            value = json.loads(payload) if payload.startswith(("{", "[")) else payload
            mode = str(value)
            self._hvac_mode = NEST_TO_HA_MODE.get(mode, HVACMode.OFF)
            self._update_hvac_action()
            self.schedule_update_ha_state()
            _LOGGER.debug("Updated HVAC mode for %s: %s", self._serial, mode)
        except (ValueError, TypeError) as err:
            _LOGGER.error("Failed to parse HVAC mode: %s", err)

    def _update_hvac_action(self) -> None:
        """Update the HVAC action based on current and target temperatures."""
        if self._hvac_mode == HVACMode.OFF:
            self._hvac_action = HVACAction.OFF
        elif (
            self._current_temperature is not None
            and self._target_temperature is not None
        ):
            diff = self._target_temperature - self._current_temperature

            if abs(diff) < TEMP_THRESHOLD:
                self._hvac_action = HVACAction.IDLE
            elif diff > TEMP_THRESHOLD and self._hvac_mode in (
                HVACMode.HEAT,
                HVACMode.HEAT_COOL,
            ):
                self._hvac_action = HVACAction.HEATING
            elif diff < -TEMP_THRESHOLD and self._hvac_mode in (
                HVACMode.COOL,
                HVACMode.HEAT_COOL,
            ):
                self._hvac_action = HVACAction.COOLING
            else:
                self._hvac_action = HVACAction.IDLE
        else:
            self._hvac_action = HVACAction.IDLE

    @property
    def unique_id(self) -> str:
        """Return unique ID for this device."""
        return f"{self._serial}_climate"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._serial)},
            "name": self._device_name,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "serial_number": self._serial,
        }

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        return self._target_temperature

    @property
    def target_temperature_low(self) -> float | None:
        """Return the low target temperature (for HEAT_COOL mode)."""
        return self._target_temperature_low

    @property
    def target_temperature_high(self) -> float | None:
        """Return the high target temperature (for HEAT_COOL mode)."""
        return self._target_temperature_high

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        return self._hvac_mode

    @property
    def hvac_action(self) -> HVACAction:
        """Return current HVAC action."""
        return self._hvac_action

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if temp := kwargs.get(ATTR_TEMPERATURE):
            topic = self._mqtt_client.get_set_topic(
                self._serial, "shared", "target_temperature"
            )
            await self.hass.async_add_executor_job(
                self._mqtt_client.publish, topic, temp
            )
            _LOGGER.debug("Set target temperature for %s: %s°C", self._serial, temp)

        if temp_low := kwargs.get("target_temp_low"):
            topic = self._mqtt_client.get_set_topic(
                self._serial, "shared", "target_temperature_low"
            )
            await self.hass.async_add_executor_job(
                self._mqtt_client.publish, topic, temp_low
            )
            _LOGGER.debug(
                "Set target temperature low for %s: %s°C", self._serial, temp_low
            )

        if temp_high := kwargs.get("target_temp_high"):
            topic = self._mqtt_client.get_set_topic(
                self._serial, "shared", "target_temperature_high"
            )
            await self.hass.async_add_executor_job(
                self._mqtt_client.publish, topic, temp_high
            )
            _LOGGER.debug(
                "Set target temperature high for %s: %s°C", self._serial, temp_high
            )

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        nest_mode = HA_TO_NEST_MODE.get(hvac_mode, NEST_MODE_OFF)
        topic = self._mqtt_client.get_set_topic(
            self._serial, "shared", "target_temperature_type"
        )
        await self.hass.async_add_executor_job(
            self._mqtt_client.publish, topic, nest_mode
        )
        _LOGGER.debug("Set HVAC mode for %s: %s", self._serial, nest_mode)
