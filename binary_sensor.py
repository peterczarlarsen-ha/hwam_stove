"""
Support for HWAM Stove binary sensors.

For more details about this platform, please refer to the documentation at
https://github.com/mvn23/hwam_stove
"""

import logging

from homeassistant.components.binary_sensor import (
    ENTITY_ID_FORMAT,
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import async_generate_entity_id

from custom_components.hwam_stove import DATA_HWAM_STOVE, DATA_PYSTOVE, DATA_STOVES

DEPENDENCIES = ["hwam_stove"]

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the HWAM Stove sensors."""
    if discovery_info is None:
        return
    pystove = hass.data[DATA_HWAM_STOVE][DATA_PYSTOVE]
    binary_sensor_info = {
        # {name: [device_class, friendly_name format]}
        pystove.DATA_REFILL_ALARM: [None, "Refill Alarm {}"],
    }
    alarm_sensor_info = {
        # {name: [device_class, friendly_name format, alarm_name]}}
        pystove.DATA_MAINTENANCE_ALARMS: [
            # General (any) maintenance alarm
            [BinarySensorDeviceClass.PROBLEM, "Maintenance Alarm {}", None],
            # Stove Backup Battery Low
            [
                BinarySensorDeviceClass.BATTERY,
                "Stove Backup Battery Low {}",
                pystove.MAINTENANCE_ALARMS[0],
            ],
            # O2 Sensor Fault
            [
                BinarySensorDeviceClass.PROBLEM,
                "O2 Sensor Fault {}",
                pystove.MAINTENANCE_ALARMS[1],
            ],
            # O2 Sensor Offset
            [
                BinarySensorDeviceClass.PROBLEM,
                "O2 Sensor Offset {}",
                pystove.MAINTENANCE_ALARMS[2],
            ],
            # Stove Temperature Sensor Fault
            [
                BinarySensorDeviceClass.PROBLEM,
                "Stove Temperature Sensor Fault {}",
                pystove.MAINTENANCE_ALARMS[3],
            ],
            # Room Temperature Sensor Fault
            [
                BinarySensorDeviceClass.PROBLEM,
                "Room Temperature Sensor Fault {}",
                pystove.MAINTENANCE_ALARMS[4],
            ],
            # Communication Fault
            [
                BinarySensorDeviceClass.PROBLEM,
                "Communication Fault {}",
                pystove.MAINTENANCE_ALARMS[5],
            ],
            # Room Temperature Sensor Battery Low
            [
                BinarySensorDeviceClass.PROBLEM,
                "Room Temperature Sensor Battery Low {}",
                pystove.MAINTENANCE_ALARMS[6],
            ],
        ],
        pystove.DATA_SAFETY_ALARMS: [
            # General (any) safety alarm
            [BinarySensorDeviceClass.SAFETY, "Safety Alarm {}", None],
            # Valve Fault, same as [1] and [2].
            [
                BinarySensorDeviceClass.SAFETY,
                "Valve Fault {}",
                pystove.SAFETY_ALARMS[0],
            ],
            # Bad Configuration
            [
                BinarySensorDeviceClass.SAFETY,
                "Bad Configuration {}",
                pystove.SAFETY_ALARMS[3],
            ],
            # Valve Disconnect, same as [5] and [6]
            [
                BinarySensorDeviceClass.SAFETY,
                "Valve Disconnect {}",
                pystove.SAFETY_ALARMS[4],
            ],
            # Valve Calibration Error, same as [8] and [9]
            [
                BinarySensorDeviceClass.SAFETY,
                "Valve Calibration Error {}",
                pystove.SAFETY_ALARMS[7],
            ],
            # Overheating
            [
                BinarySensorDeviceClass.SAFETY,
                "Stove Overheat {}",
                pystove.SAFETY_ALARMS[10],
            ],
            # Door Open Too Long
            [
                BinarySensorDeviceClass.SAFETY,
                "Door Open Too Long {}",
                pystove.SAFETY_ALARMS[11],
            ],
            # Manual Safety Alarm
            [
                BinarySensorDeviceClass.SAFETY,
                "Manual Safety Alarm {}",
                pystove.SAFETY_ALARMS[12],
            ],
            # Stove Sensor Fault
            [
                BinarySensorDeviceClass.SAFETY,
                "Stove Sensor Fault {}",
                pystove.SAFETY_ALARMS[13],
            ],
        ],
    }
    stove_name = discovery_info["stove_name"]
    stove_device = hass.data[DATA_HWAM_STOVE][DATA_STOVES][stove_name]
    sensor_list = discovery_info["sensors"]
    binary_sensors = []
    for var in sensor_list:
        if var in binary_sensor_info:
            device_class = binary_sensor_info[var][0]
            name_format = binary_sensor_info[var][1]
            entity_id = async_generate_entity_id(
                ENTITY_ID_FORMAT, "{}_{}".format(var, stove_device.name), hass=hass
            )
            binary_sensors.append(
                HwamStoveBinarySensor(
                    entity_id, stove_device, var, device_class, name_format
                )
            )
        elif var in alarm_sensor_info:
            for data in alarm_sensor_info[var]:
                device_class = data[0]
                name_format = data[1]
                alarm_name = data[2]
                if alarm_name is None:
                    entity_id = async_generate_entity_id(
                        ENTITY_ID_FORMAT,
                        "{}_{}".format(var, stove_device.name),
                        hass=hass,
                    )
                else:
                    entity_id = async_generate_entity_id(
                        ENTITY_ID_FORMAT,
                        "{}_{}_{}".format(var, alarm_name, stove_device.name),
                        hass=hass,
                    )
                binary_sensors.append(
                    HwamStoveAlarmSensor(
                        entity_id,
                        stove_device,
                        var,
                        device_class,
                        name_format,
                        alarm_name,
                    )
                )
    async_add_entities(binary_sensors)


class HwamStoveBinarySensor(BinarySensorEntity):
    """Representation of a HWAM Stove binary sensor."""

    def __init__(self, entity_id, stove_device, var, device_class, name_format):
        """Initialize the binary sensor."""
        self._stove_device = stove_device
        self.entity_id = entity_id
        self._var = var
        self._state = None
        self._device_class = device_class
        self._name_format = name_format

    async def async_added_to_hass(self):
        """Subscribe to updates from the component."""
        _LOGGER.debug("Added HWAM Stove binary sensor %s", self.entity_id)
        async_dispatcher_connect(
            self.hass, self._stove_device.signal, self.receive_report
        )

    async def receive_report(self, status):
        """Handle status updates from the component."""
        self._state = bool(status.get(self._var))
        self.async_schedule_update_ha_state()

    @property
    def name(self):
        """Return the friendly name."""
        return self._name_format.format(self._stove_device.stove.name)

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._state

    @property
    def device_class(self):
        """Return the class of this device."""
        return self._device_class

    @property
    def should_poll(self):
        """Return False because entity pushes its state."""
        return False


class HwamStoveAlarmSensor(HwamStoveBinarySensor):
    """Representation of a HWAM Stove Alarm binary sensor."""

    def __init__(
        self, entity_id, stove_device, var, device_class, name_format, alarm_name
    ):
        super().__init__(entity_id, stove_device, var, device_class, name_format)
        self._alarm_name = alarm_name

    async def receive_report(self, status):
        """Handle status updates from the component."""
        if self._alarm_name:
            self._state = self._alarm_name in status.get(self._var, [])
        else:
            self._state = status.get(self._var, []) != []
        self.async_schedule_update_ha_state()
