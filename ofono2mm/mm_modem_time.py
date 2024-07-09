from datetime import datetime, timezone
from dbus_next.service import (ServiceInterface, method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

from ofono2mm.logging import ofono2mm_print

class MMModemTimeInterface(ServiceInterface):
    def __init__(self, ofono_client, modem_name, ofono_interfaces, verbose=False):
        super().__init__('org.freedesktop.ModemManager1.Modem.Time')
        self.modem_name = modem_name
        ofono2mm_print("Initializing Time interface", verbose)
        self.ofono_client = ofono_client
        self.ofono_interfaces = ofono_interfaces
        self.verbose = verbose
        self.network_time = datetime.now().isoformat()
        self.network_timezone = {
            'offset': Variant('i', 0),
            'dst-offset': Variant('i', 0),
            'leap-seconds': Variant('i', 0)
        }

    async def init_time(self):
        ofono2mm_print("Initializing signals", self.verbose)

        if 'org.ofono.NetworkTime' in self.ofono_interfaces:
            self.ofono_interfaces['org.ofono.NetworkTime'].on_network_time_changed(self.update_time)

    async def update_time(self, time):
        ofono2mm_print(f"Updating time to {time}", self.verbose)
        utc_time = time['UTC'].value
        network_time = datetime.fromtimestamp(utc_time, tz=timezone.utc)
        self.network_time = network_time.isoformat()

        timezone_offset = time['Timezone'].value // 60
        dst_offset = time['DST'].value // 60

        self.update_network_timezone(timezone_offset, dst_offset, 0)

    @dbus_property(access=PropertyAccess.READ)
    def NetworkTimezone(self) -> 'a{sv}':
        return self.network_timezone

    @method()
    async def GetNetworkTime(self) -> 's':
        ofono2mm_print("Returning network time", self.verbose)

        if 'org.ofono.NetworkTime' in self.ofono_interfaces:
            ofono_interface = self.ofono_client["ofono_modem"][self.modem_name]['org.ofono.NetworkTime']
            output = await ofono_interface.call_get_network_time()

            if 'UTC' in output:
                utc_time = output['UTC'].value
                network_time = datetime.fromtimestamp(utc_time, tz=timezone.utc)
                self.network_time = network_time.isoformat()

                timezone_offset = output['Timezone'].value // 60
                dst_offset = output['DST'].value // 60

                self.update_network_timezone(timezone_offset, dst_offset, 0)
            else:
                self.network_time = datetime.now().isoformat()
        else:
            ofono2mm_print("oFono NetworkTime is unavailable, using system time", self.verbose)
            self.network_time = datetime.now().isoformat()

        return self.network_time

    @signal()
    def NetworkTimeChanged(self, time: 's') -> 's':
        ofono2mm_print(f"Signal: Network time changed to time {time}", self.verbose)
        self.network_time = time
        return time

    def update_network_timezone(self, offset, dst_offset, leap_seconds):
        ofono2mm_print(f"Update network timezone with offset {offset} dst offset {dst_offset} and leap_seconds {leap_seconds}", self.verbose)

        self.network_timezone = {
            'offset': Variant('i', offset),
            'dst-offset': Variant('i', dst_offset),
            'leap-seconds': Variant('i', leap_seconds)
        }

        self.NetworkTimeChanged(self.network_time)
