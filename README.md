# Home Assistant No Longer Evil Thermostat

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]
[![Validate][validate-shield]][validate]
[![Lint][lint-shield]][lint]

![Project Maintenance][maintenance-shield]
[![Community Forum][forum-shield]][forum]

A Home Assistant custom integration that connects Google Nest thermostats to Home Assistant via MQTT, using the No Longer Evil Thermostat server.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.][my-hacs-badge]][my-hacs-url]

[releases-shield]: https://img.shields.io/github/release/will-tm/home-assistant-nolongerevil-thermostat.svg?style=for-the-badge
[releases]: https://github.com/will-tm/home-assistant-nolongerevil-thermostat/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/will-tm/home-assistant-nolongerevil-thermostat.svg?style=for-the-badge
[commits]: https://github.com/will-tm/home-assistant-nolongerevil-thermostat/commits/main
[license-shield]: https://img.shields.io/github/license/will-tm/home-assistant-nolongerevil-thermostat.svg?style=for-the-badge
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[validate-shield]: https://img.shields.io/github/actions/workflow/status/will-tm/home-assistant-nolongerevil-thermostat/validate.yaml?branch=main&label=Validate&style=for-the-badge
[validate]: https://github.com/will-tm/home-assistant-nolongerevil-thermostat/actions/workflows/validate.yaml
[lint-shield]: https://img.shields.io/github/actions/workflow/status/will-tm/home-assistant-nolongerevil-thermostat/lint.yaml?branch=main&label=Lint&style=for-the-badge
[lint]: https://github.com/will-tm/home-assistant-nolongerevil-thermostat/actions/workflows/lint.yaml
[maintenance-shield]: https://img.shields.io/badge/maintainer-Will%20TM-blue.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[my-hacs-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[my-hacs-url]: https://my.home-assistant.io/redirect/hacs_repository/?owner=will-tm&repository=home-assistant-nolongerevil-thermostat&category=integration

## Features

- Full climate entity support (thermostat control)
- Control target temperature and temperature ranges
- Switch between heating, cooling, auto (heat/cool), and off modes
- View current temperature readings
- Fan control entity (on/auto modes)
- Occupancy/presence detection (home/away status)
- Support for multiple thermostats
- Configurable MQTT broker connection
- Support for both Celsius and Fahrenheit temperature units
- UI-based configuration (Config Flow)
- Native Home Assistant integration (no bridge required)

## Installation

### Option 1: Manual Installation

1. Copy the `nolongerevil_thermostat` folder to your Home Assistant's `custom_components` directory.

   ```bash
   cd /config  # or wherever your Home Assistant configuration is located
   mkdir -p custom_components
   cp -r /path/to/home-assistant-nolongerevil-thermostat/custom_components/nolongerevil_thermostat custom_components/
   ```

2. Restart Home Assistant

3. Go to **Settings** → **Devices & Services** → **Add Integration**

4. Search for "No Longer Evil Thermostat"

### Option 2: HACS (Recommended)

**Via HACS Default (after approval):**
1. Click the button below to open HACS:

   [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.][my-hacs-badge]][my-hacs-url]

2. Click "Download"
3. Restart Home Assistant

**Via HACS Custom Repository (before approval):**
1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots (⋮) in the top right
4. Select "Custom repositories"
5. Add repository: `https://github.com/will-tm/home-assistant-nolongerevil-thermostat`
6. Category: "Integration"
7. Click "Add"
8. Find "No Longer Evil Thermostat" in the list
9. Click "Download"
10. Restart Home Assistant

## Configuration

### UI Configuration (Recommended)

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **No Longer Evil Thermostat**
4. Follow the configuration wizard:

   **Step 1: MQTT Broker Configuration**
   - MQTT Broker URL (e.g., `mqtt://192.168.1.100` or `mqtts://broker.example.com`)
   - MQTT Port (default: 1883)
   - MQTT Username (optional)
   - MQTT Password (optional)
   - Topic Prefix (default: `nest`)

   **Step 2: Add Devices**
   - Device Name (e.g., "Living Room Thermostat")
   - Device Serial Number (alphanumeric string, typically 8-16 characters)
   - Temperature Unit (celsius or fahrenheit)
   - Add Another Device (check to add more thermostats)

5. Click **Submit**

### YAML Configuration (Alternative)

While UI configuration is recommended, you can also configure via YAML if needed. Add to `configuration.yaml`:

```yaml
# Example configuration.yaml entry
nolongerevil_thermostat:
  mqtt_broker: mqtt://192.168.1.100
  mqtt_port: 1883
  mqtt_username: your_username
  mqtt_password: your_password
  topic_prefix: nest
  devices:
    - name: Living Room Thermostat
      serial: 02AA01AB501203EQ
      temperature_unit: celsius
    - name: Bedroom Thermostat
      serial: 02BB02AC601304FR
      temperature_unit: fahrenheit
```

## Entities Created

For each thermostat device, the integration creates:

### 1. Climate Entity
- **Entity ID**: `climate.{device_name}`
- **Features**:
  - Current temperature reading
  - Target temperature control
  - Target temperature range (for heat/cool mode)
  - HVAC modes: Off, Heat, Cool, Auto
  - Current HVAC action: Idle, Heating, Cooling

### 2. Fan Entity
- **Entity ID**: `fan.{device_name}_fan`
- **Features**:
  - Turn fan on (continuous)
  - Turn fan off (auto mode)

### 3. Binary Sensor (Occupancy)
- **Entity ID**: `binary_sensor.{device_name}_occupancy`
- **Features**:
  - Occupancy Detected (someone is home)
  - Occupancy Not Detected (away mode active)

## HVAC Mode Mapping

| Home Assistant Mode | Nest Mode | Description |
|---------------------|-----------|-------------|
| Off | `off` | System off |
| Heat | `heat` | Heating only |
| Cool | `cool` | Cooling only |
| Heat/Cool (Auto) | `range` | Automatic heating/cooling |

## Requirements

- Home Assistant >= 2023.1.0
- Python >= 3.11
- Running No Longer Evil Thermostat server
- MQTT broker (e.g., Mosquitto)
- `paho-mqtt` >= 1.6.1 (automatically installed)

## Finding Your Thermostat Serial Number

The serial number is an alphanumeric string (typically 16 characters) that uniquely identifies your Nest thermostat. You can find it:

1. In the No Longer Evil Thermostat web interface
2. On the back of your physical thermostat
3. In your Nest mobile app under device settings
4. In the Nest device information (pull the display off the base)

### Check Logs

Enable debug logging by adding to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.nolongerevil_thermostat: debug
```

Then check logs at **Settings** → **System** → **Logs**

## Development

### Testing Locally

1. Set up a Home Assistant development environment
2. Link this integration to your dev environment's `custom_components`
3. Restart Home Assistant
4. Configure via UI

## License

MIT License - See LICENSE file for details

## Related Projects

- [No Longer Evil Thermostat](https://github.com/codykociemba/NoLongerEvil-Thermostat) - MQTT bridge for Nest
