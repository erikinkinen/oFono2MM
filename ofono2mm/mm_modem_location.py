from datetime import datetime
from os import seteuid, getuid
import asyncio

import gi
gi.require_version('Geoclue', '2.0')
from gi.repository import Gio, GLib, GObject, Geoclue

from dbus_next.service import ServiceInterface, method, dbus_property
from dbus_next.constants import PropertyAccess
from dbus_next import Variant, DBusError

from ofono2mm.logging import ofono2mm_print

simple = None
main_loop = None
location_data = None

def on_simple_ready(source_object, result, user_data):
    global simple, main_loop, location_data
    simple = Geoclue.Simple.new_with_thresholds_finish(result)

    location = simple.get_location()
    longitude = location.get_property('longitude')
    latitude = location.get_property('latitude')
    altitude = location.get_property('altitude')

    location_data = (latitude, longitude, altitude)

    if main_loop:
        main_loop.quit()

def geoclue_get_location():
    global simple, main_loop, location_data

    def on_timeout(user_data):
        global simple, main_loop
        if simple:
            simple = None
        if main_loop:
            main_loop.quit()
        return False

    seteuid(32011)

    GLib.timeout_add_seconds(30, on_timeout, None)

    Geoclue.Simple.new_with_thresholds("ModemManager", Geoclue.AccuracyLevel.EXACT, 0, 0, None, on_simple_ready, None)

    main_loop = GLib.MainLoop()
    main_loop.run()

    if getuid() == 0:
        seteuid(0)

    if location_data:
        latitude, longitude, altitude = location_data
        return latitude, longitude, altitude
    else:
        raise Exception("Failed to get location data.")

class MMModemLocationInterface(ServiceInterface):
    def __init__(self, verbose=False):
        super().__init__('org.freedesktop.ModemManager1.Modem.Location')
        ofono2mm_print("Initializing Location interface", verbose)
        self.verbose = verbose
        utc_time = datetime.utcnow().isoformat()

        self.location = {
            2: Variant('a{sv}', { # 2 is MM_MODEM_LOCATION_SOURCE_GPS_RAW
                'utc-time': Variant('s', utc_time),
                'latitude': Variant('d', 0),
                'longitude': Variant('d', 0),
                'altitude': Variant('d', 0)
            })
        }

        self.props = {
            'Capabilities': Variant('u', 1), # hardcoded dummy value 3gpp location area code and cell id MM_MODEM_LOCATION_SOURCE_3GPP_LAC_CI
            'SupportedAssistanceData': Variant('u', 0), # hardcoded dummy value none MM_MODEM_LOCATION_ASSISTANCE_DATA_TYPE_NONE
            'Enabled': Variant('u', 2), # hardcoded dummy value raw MM_MODEM_LOCATION_SOURCE_GPS_RAW
            'SignalsLocation': Variant('b', False),
            'SuplServer': Variant('s', ''),
            'AssistanceDataServers': Variant('as', []),
            'GpsRefreshRate': Variant('u', 0)
        }

    async def async_geoclue_get_location(self):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, geoclue_get_location)

    @method()
    def Setup(self, sources: 'u', signal_location: 'b') -> None:
        ofono2mm_print(f"Setup location with source flag {sources} and signal location {signal_location}", self.verbose)
        self.props['Enabled'] = Variant('u', sources)
        self.props['SignalsLocation'] = Variant('b', signal_location)

    @method()
    async def GetLocation(self) -> 'a{uv}':
        ofono2mm_print("Returning current location", self.verbose)

        try:
            latitude, longitude, altitude = await async_geoclue_get_location()
        except Exception as e:
            ofono2mm_print(f"Failed to get location from geoclue: {e}", self.verbose)
            longitude = 0
            latitude = 0
            altitude = 0

        utc_time = datetime.utcnow().isoformat()

        ofono2mm_print(f"Location is longitude: {longitude}, latitude: {latitude}, altitude: {altitude}", self.verbose)

        location_variant = self.location[2].value
        location_variant['utc-time'] = Variant('s', utc_time)
        location_variant['latitude'] = Variant('d', latitude)
        location_variant['longitude'] = Variant('d', longitude)
        location_variant['altitude'] = Variant('d', altitude)

        return self.location

    @method()
    def SetSuplServer(self, supl: 's') -> None:
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Cannot set SUPL server: A-GPS not supported')

    @method()
    def InjectAssistanceData(self, data: 'ay') -> None:
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Cannot inject assistance data: ununsupported')

    @method()
    def SetGpsRefreshRate(self, rate: 'u') -> None:
        ofono2mm_print(f"Setting GPS refresh rate to {rate}", self.verbose)
        self.props['GpsRefreshRate'] = Variant('u', rate)

    @dbus_property(access=PropertyAccess.READ)
    def Capabilities(self) -> 'u':
        return self.props['Capabilities'].value

    @dbus_property(access=PropertyAccess.READ)
    def SupportedAssistanceData(self) -> 'u':
        return self.props['SupportedAssistanceData'].value

    @dbus_property(access=PropertyAccess.READ)
    def Enabled(self) -> 'u':
        return self.props['Enabled'].value

    @dbus_property(access=PropertyAccess.READ)
    def SignalsLocation(self) -> 'b':
        return self.props['SignalsLocation'].value

    @dbus_property(access=PropertyAccess.READ)
    def Location(self) -> 'a{uv}':
        return self.location

    @dbus_property(access=PropertyAccess.READ)
    def SuplServer(self) -> 's':
        return self.props['SuplServer'].value

    @dbus_property(access=PropertyAccess.READ)
    def AssistanceDataServers(self) -> 'as':
        return self.props['AssistanceDataServers'].value

    @dbus_property(access=PropertyAccess.READ)
    def GpsRefreshRate(self) -> 'u':
        return self.props['GpsRefreshRate'].value
