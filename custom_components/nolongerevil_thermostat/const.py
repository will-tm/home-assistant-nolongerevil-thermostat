DOMAIN = "nolongerevil_thermostat"

# Configuration keys
CONF_MQTT_BROKER = "mqtt_broker"
CONF_MQTT_PORT = "mqtt_port"
CONF_MQTT_USERNAME = "mqtt_username"
CONF_MQTT_PASSWORD = "mqtt_password"
CONF_TOPIC_PREFIX = "topic_prefix"
CONF_DEVICES = "devices"
CONF_DEVICE_NAME = "name"
CONF_DEVICE_SERIAL = "serial"
CONF_TEMPERATURE_UNIT = "temperature_unit"

# Default values
DEFAULT_MQTT_PORT = 1883
DEFAULT_TOPIC_PREFIX = "nest"
DEFAULT_TEMPERATURE_UNIT = "celsius"

# MQTT Topics (format: {prefix}/{serial}/{object_type}/{field})
TOPIC_CURRENT_TEMP = "device/current_temperature"
TOPIC_TARGET_TEMP = "shared/target_temperature"
TOPIC_TARGET_TEMP_LOW = "shared/target_temperature_low"
TOPIC_TARGET_TEMP_HIGH = "shared/target_temperature_high"
TOPIC_TARGET_TEMP_TYPE = "shared/target_temperature_type"
TOPIC_FAN_TIMER_ACTIVE = "device/fan_timer_active"
TOPIC_AWAY = "device/away"
TOPIC_AVAILABILITY = "availability"

# HVAC modes mapping
NEST_MODE_OFF = "off"
NEST_MODE_HEAT = "heat"
NEST_MODE_COOL = "cool"
NEST_MODE_RANGE = "range"

# Manufacturer info
MANUFACTURER = "Google Nest"
MODEL = "Nest Thermostat"
