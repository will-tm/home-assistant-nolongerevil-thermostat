"""Config flow for No Longer Evil Thermostat integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_DEVICE_NAME,
    CONF_DEVICE_SERIAL,
    CONF_DEVICES,
    CONF_MQTT_BROKER,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_PORT,
    CONF_MQTT_USERNAME,
    CONF_TEMPERATURE_UNIT,
    CONF_TOPIC_PREFIX,
    DEFAULT_MQTT_PORT,
    DEFAULT_TEMPERATURE_UNIT,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MQTT_BROKER): cv.string,
        vol.Optional(CONF_MQTT_PORT, default=DEFAULT_MQTT_PORT): cv.port,
        vol.Optional(CONF_MQTT_USERNAME): cv.string,
        vol.Optional(CONF_MQTT_PASSWORD): cv.string,
        vol.Optional(CONF_TOPIC_PREFIX, default=DEFAULT_TOPIC_PREFIX): cv.string,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for No Longer Evil Thermostat."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}
        self._devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Store MQTT broker configuration
            self._data = user_input

            # Move to device configuration
            return await self.async_step_device()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate device data
            if not user_input.get(CONF_DEVICE_NAME):
                errors[CONF_DEVICE_NAME] = "name_required"
            elif not user_input.get(CONF_DEVICE_SERIAL):
                errors[CONF_DEVICE_SERIAL] = "serial_required"
            elif len(user_input[CONF_DEVICE_SERIAL]) != 8:
                errors[CONF_DEVICE_SERIAL] = "serial_invalid"
            else:
                # Add device to list
                self._devices.append(
                    {
                        CONF_DEVICE_NAME: user_input[CONF_DEVICE_NAME],
                        CONF_DEVICE_SERIAL: user_input[CONF_DEVICE_SERIAL].upper(),
                        CONF_TEMPERATURE_UNIT: user_input.get(
                            CONF_TEMPERATURE_UNIT, DEFAULT_TEMPERATURE_UNIT
                        ),
                    }
                )

                # Check if user wants to add another device
                if user_input.get("add_another"):
                    return await self.async_step_device()

                # Create the config entry
                self._data[CONF_DEVICES] = self._devices
                return self.async_create_entry(
                    title=f"No Longer Evil Thermostat ({len(self._devices)} device{'s' if len(self._devices) > 1 else ''})",
                    data=self._data,
                )

        # Schema for device configuration
        device_schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_NAME): cv.string,
                vol.Required(CONF_DEVICE_SERIAL): cv.string,
                vol.Optional(
                    CONF_TEMPERATURE_UNIT, default=DEFAULT_TEMPERATURE_UNIT
                ): vol.In(["celsius", "fahrenheit"]),
                vol.Optional("add_another", default=False): cv.boolean,
            }
        )

        return self.async_show_form(
            step_id="device",
            data_schema=device_schema,
            errors=errors,
            description_placeholders={
                "device_count": str(len(self._devices)),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for No Longer Evil Thermostat."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Update the config entry with new options
            return self.async_create_entry(title="", data=user_input)

        # Get current configuration
        current_broker = self.config_entry.data.get(CONF_MQTT_BROKER, "")
        current_port = self.config_entry.data.get(CONF_MQTT_PORT, DEFAULT_MQTT_PORT)
        current_username = self.config_entry.data.get(CONF_MQTT_USERNAME, "")
        current_password = self.config_entry.data.get(CONF_MQTT_PASSWORD, "")
        current_prefix = self.config_entry.data.get(
            CONF_TOPIC_PREFIX, DEFAULT_TOPIC_PREFIX
        )

        options_schema = vol.Schema(
            {
                vol.Required(CONF_MQTT_BROKER, default=current_broker): cv.string,
                vol.Optional(CONF_MQTT_PORT, default=current_port): cv.port,
                vol.Optional(CONF_MQTT_USERNAME, default=current_username): cv.string,
                vol.Optional(CONF_MQTT_PASSWORD, default=current_password): cv.string,
                vol.Optional(CONF_TOPIC_PREFIX, default=current_prefix): cv.string,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )
