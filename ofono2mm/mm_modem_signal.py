import asyncio

from dbus_next.service import ServiceInterface, method, dbus_property
from dbus_next.constants import PropertyAccess
from dbus_next import Variant, DBusError

from ofono2mm.logging import ofono2mm_print

class MMModemSignalInterface(ServiceInterface):
    def __init__(self, ofono_props, ofono_interfaces, ofono_interface_props, verbose=False):
        super().__init__('org.freedesktop.ModemManager1.Modem.Signal')
        ofono2mm_print("Initializing Signal interface", verbose)
        self.ofono_props = ofono_props
        self.ofono_interfaces = ofono_interfaces
        self.ofono_interface_props = ofono_interface_props
        self.verbose = verbose
        self.props = {
            'Rate': Variant('u', 0),
            'RssiThreshold': Variant('u', 0),
            'ErrorRateThreshold': Variant('b', False),
            'Gsm': Variant('a{sv}', {
                'rssi': Variant('d', 0),
                'error-rate': Variant('d', 0)
            }),
            'Umts': Variant('a{sv}', {
                'rssi': Variant('d', 0),
                'rscp': Variant('d', 0),
                'ecio': Variant('d', 0),
                'error-rate': Variant('d', 0)
            }),
            'Lte': Variant('a{sv}', {
                'rssi': Variant('d', 0),
                'rsrq': Variant('d', 0),
                'rsrp': Variant('d', 0),
                'snr': Variant('d', 0),
                'error-rate': Variant('d', 0)
            }),
            'Nr5g': Variant('a{sv}', {
                'rsrq': Variant('d', 0),
                'rsrp': Variant('d', 0),
                'snr': Variant('d', 0),
                'error-rate': Variant('d', 0)
            })
        }

    async def set_props(self):
        ofono2mm_print("Setting properties", self.verbose)

        old_props = self.props
        if 'org.ofono.NetworkMonitor' in self.ofono_interfaces:
            cellinfo = []
            try:
                cellinfo = await self.ofono_interfaces['org.ofono.NetworkMonitor'].call_get_serving_cell_information()
            except Exception as e:
                ofono2mm_print(f"Failed to get cell info from NetworkMonitor: {e}", self.verbose)

            if 'Technology' in cellinfo:
                if cellinfo['Technology'].value == 'nr':
                    self.props['Nr5g'].value['rssi'] = Variant('d', cellinfo['ChannelQualityIndicator'].value if "ChannelQualityIndicator" in cellinfo else 0)
                    self.props['Nr5g'].value['rsrq'] = Variant('d', cellinfo['ReferenceSignalReceivedQuality'].value if "ReferenceSignalReceivedQuality" in cellinfo else 0)
                    self.props['Nr5g'].value['rsrp'] = Variant('d', cellinfo['ReferenceSignalReceivedPower'].value if "ReferenceSignalReceivedPower" in cellinfo else 0)
                if cellinfo['Technology'].value == 'lte':
                    self.props['Lte'].value['rssi'] = Variant('d', cellinfo['ChannelQualityIndicator'].value if "ChannelQualityIndicator" in cellinfo else 0)
                    self.props['Lte'].value['rsrq'] = Variant('d', cellinfo['ReferenceSignalReceivedQuality'].value if "ReferenceSignalReceivedQuality" in cellinfo else 0)
                    self.props['Lte'].value['rsrp'] = Variant('d', cellinfo['ReferenceSignalReceivedPower'].value if "ReferenceSignalReceivedPower" in cellinfo else 0)
                if cellinfo['Technology'].value == 'umts':
                    self.props['Umts'].value['rscp'] = Variant('d', cellinfo['ReceivedSignalCodePower'].value if "ReceivedSignalCodePower" in cellinfo else 0)
                if cellinfo['Technology'].value == 'gsm':
                    self.props['Gsm'].value['error-rate'] = Variant('d', cellinfo['BitErrorRate'].value if "BitErrorRate" in cellinfo else 0)

        for prop in self.props:
            if self.props[prop].value != old_props[prop].value:
                self.emit_properties_changed({prop: self.props[prop].value})

    @method()
    async def Setup(self, rate: 'u'):
        ofono2mm_print(f"Setup with rate {rate}", self.verbose)
        self.set_props()
        self.props['Rate'] = Variant('u', rate)

    @method()
    def SetupThresholds(self, settings: 'a{sv}'):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Cannot setup thresholds: operation not supported')

    @dbus_property(access=PropertyAccess.READ)
    def Rate(self) -> 'u':
        return self.props['Rate'].value

    @dbus_property(access=PropertyAccess.READ)
    def RssiThreshold(self) -> 'u':
        return self.props['RssiThreshold'].value

    @dbus_property(access=PropertyAccess.READ)
    def ErrorRateThreshold(self) -> 'b':
        return self.props['ErrorRateThreshold'].value

    @dbus_property(access=PropertyAccess.READ)
    def Gsm(self) -> 'a{sv}':
        return self.props['Gsm'].value

    @dbus_property(access=PropertyAccess.READ)
    def Umts(self) -> 'a{sv}':
        return self.props['Umts'].value

    @dbus_property(access=PropertyAccess.READ)
    def Lte(self) -> 'a{sv}':
        return self.props['Lte'].value

    @dbus_property(access=PropertyAccess.READ)
    def Nr5g(self) -> 'a{sv}':
        return self.props['Nr5g'].value

    def ofono_changed(self, name, varval):
        self.ofono_props[name] = varval
        asyncio.create_task(self.set_props())

    def ofono_client_changed(self, ofono_client):
        self.ofono_client = ofono_client

    def ofono_interface_changed(self, iface):
        def ch(name, varval):
            if iface in self.ofono_interface_props:
                self.ofono_interface_props[iface][name] = varval
            asyncio.create_task(self.set_props())

        return ch
