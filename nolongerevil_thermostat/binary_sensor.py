"""Binary sensor platform for No Longer Evil Thermostat."""
from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up No Longer Evil Thermostat binary sensor entities."""
    mqtt_client = hass.data[DOMAIN][f"{entry.entry_id}_mqtt_client"]
    devices = entry.data.get(CONF_DEVICES, [])

    entities = []
    for device in devices:
        entities.append(NoLongerEvilOccupancySensor(hass, mqtt_client, device, entry))

    async_add_entities(entities, True)


class NoLongerEvilOccupancySensor(BinarySensorEntity):
    """Representation of a No Longer Evil Thermostat occupancy sensor."""

    _attr_has_entity_name = True
    _attr_name = "Occupancy"
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    def __init__(
        self,
        hass: HomeAssistant,
        mqtt_client: Any,
        device: dict[str, Any],
        entry: ConfigEntry,
    ) -> None:
        """Initialize the occupancy sensor."""
        self.hass = hass
        self._mqtt_client = mqtt_client
        self._device = device
        self._entry = entry

        # Device info
        self._serial = device[CONF_DEVICE_SERIAL]
        self._device_name = device[CONF_DEVICE_NAME]

        # State - default to occupied (not away)
        self._is_occupied: bool = True

        # Subscribe to MQTT topic
        self._subscribe_to_topic()

    def _subscribe_to_topic(self) -> None:
        """Subscribe to MQTT topic for away/occupancy state."""
        topic = self._mqtt_client.get_topic(self._serial, "device", "away")
        self._mqtt_client.subscribe(topic, self._handle_away_state)

    def _handle_away_state(self, topic: str, payload: str) -> None:
        """Handle away state update."""
        try:
            value = json.loads(payload) if payload.startswith(("{", "[")) else payload

            # Convert to boolean
            if isinstance(value, bool):
                is_away = value
            elif isinstance(value, str):
                is_away = value.lower() in ("true", "1", "on")
            else:
                is_away = bool(value)

            # Invert: away=True means occupancy=False
            self._is_occupied = not is_away

            self.schedule_update_ha_state()
            _LOGGER.debug(
                "Updated occupancy for %s: %s",
                self._serial,
                "occupied" if self._is_occupied else "not occupied",
            )
        except (ValueError, TypeError) as err:
            _LOGGER.error("Failed to parse away state: %s", err)

    @property
    def unique_id(self) -> str:
        """Return unique ID for this device."""
        return f"{self._serial}_occupancy"

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
    def is_on(self) -> bool:
        """Return true if occupancy is detected."""
        return self._is_occupied
