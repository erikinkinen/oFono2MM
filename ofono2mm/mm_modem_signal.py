from dbus_next.service import ServiceInterface, method, dbus_property
from dbus_next.constants import PropertyAccess
from dbus_next import Variant, DBusError

from ofono2mm.logging import ofono2mm_print

class MMModemSignalInterface(ServiceInterface):
    def __init__(self, ofono_props, ofono_interface_props, verbose=False):
        super().__init__('org.freedesktop.ModemManager1.Modem.Signal')
        ofono2mm_print("Initializing Signal interface", verbose)
        self.ofono_props = ofono_props
        self.ofono_interface_props = ofono_interface_props
        self.verbose = verbose
        self.props = {
            'Rate': Variant('u', 0),
            'RssiThreshold': Variant('u', 0),
            'ErrorRateThreshold': Variant('b', False),
            'Cdma': Variant('a{sv}', {
                'rssi': Variant('d', 0),
                'ecio': Variant('d', 0),
                'error-rate': Variant('d', 0)
             }),
            'Evdo': Variant('a{sv}', {
                'rssi': Variant('d', 0),
                'ecio': Variant('d', 0),
                'sinr': Variant('d', 0),
                'io': Variant('d', 0),
                'error-rate': Variant('d', 0)
             }),
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

    def set_props(self):
        ofono2mm_print("Setting properties", self.verbose)

        old_props = self.props

        if 'org.ofono.NetworkMonitor' in self.ofono_interface_props:
            self.props['Cdma'].value['rssi'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReceivedSignalStrength'].value if "ReceivedSignalStrength" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Evdo'].value['rssi'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReceivedSignalStrength'].value if "ReceivedSignalStrength" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Gsm'].value['rssi'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReceivedSignalStrength'].value if "ReceivedSignalStrength" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Umts'].value['rssi'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReceivedSignalStrength'].value if "ReceivedSignalStrength" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Lte'].value['rssi'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReceivedSignalStrength'].value if "ReceivedSignalStrength" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)

            self.props['Cdma'].value['error-rate'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['BitErrorRate'].value if "BitErrorRate" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Evdo'].value['error-rate'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['BitErrorRate'].value if "BitErrorRate" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Gsm'].value['error-rate'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['BitErrorRate'].value if "BitErrorRate" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Umts'].value['error-rate'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['BitErrorRate'].value if "BitErrorRate" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Lte'].value['error-rate'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['BitErrorRate'].value if "BitErrorRate" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Nr5g'].value['error-rate'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['BitErrorRate'].value if "BitErrorRate" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)

            self.props['Lte'].value['rsrq'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReferenceSignalReceivedQuality'].value if "ReferenceSignalReceivedQuality" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Nr5g'].value['rsrq'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReferenceSignalReceivedQuality'].value if "ReferenceSignalReceivedQuality" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)

            self.props['Lte'].value['rsrp'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReferenceSignalReceivedPower'].value if "ReferenceSignalReceivedPower" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
            self.props['Nr5g'].value['rsrp'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReferenceSignalReceivedPower'].value if "ReferenceSignalReceivedPower" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)

            self.props['Umts'].value['rscp'] = Variant('d', self.ofono_interface_props['org.ofono.NetworkMonitor']['ReceivedSignalCodePower'].value if "ReceivedSignalCodePower" in self.ofono_interface_props['org.ofono.NetworkMonitor'] else 0)
        else:
            self.props['Cdma'].value['rssi'] = Variant('d', 0)
            self.props['Evdo'].value['rssi'] = Variant('d', 0)
            self.props['Gsm'].value['rssi'] = Variant('d', 0)
            self.props['Umts'].value['rssi'] = Variant('d', 0)
            self.props['Lte'].value['rssi'] = Variant('d', 0)

            self.props['Cdma'].value['error-rate'] = Variant('d', 0)
            self.props['Evdo'].value['error-rate'] = Variant('d', 0)
            self.props['Gsm'].value['error-rate'] = Variant('d', 0)
            self.props['Umts'].value['error-rate'] = Variant('d', 0)
            self.props['Lte'].value['error-rate'] = Variant('d', 0)
            self.props['Nr5g'].value['error-rate'] = Variant('d', 0)

            self.props['Lte'].value['rsrq'] = Variant('d', 0)
            self.props['Nr5g'].value['rsrq'] = Variant('d', 0)

            self.props['Lte'].value['rsrp'] = Variant('d', 0)
            self.props['Nr5g'].value['rsrp'] = Variant('d', 0)

            self.props['Umts'].value['rscp'] = Variant('d', 0)

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
    def Cdma(self) -> 'a{sv}':
        return self.props['Cdma'].value

    @dbus_property(access=PropertyAccess.READ)
    def Evdo(self) -> 'a{sv}':
        return self.props['Evdo'].value

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
        self.set_props()

    def ofono_client_changed(self, ofono_client):
        self.ofono_client = ofono_client

    def ofono_interface_changed(self, iface):
        def ch(name, varval):
            if iface in self.ofono_interface_props:
                self.ofono_interface_props[iface][name] = varval

            self.set_props()

        return ch
