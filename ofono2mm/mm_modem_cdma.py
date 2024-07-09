from dbus_next.service import ServiceInterface, method, dbus_property
from dbus_next.constants import PropertyAccess
from dbus_next import Variant, DBusError

from ofono2mm.logging import ofono2mm_print

class MMModemCDMAInterface(ServiceInterface):
    def __init__(self, modem_name, verbose=False):
        super().__init__('org.freedesktop.ModemManager1.Modem.ModemCdma')
        self.modem_name = modem_name
        ofono2mm_print("Initializing CDMA interface", verbose)
        self.verbose = verbose
        self.props = {
            'ActivationState': Variant('u', 0), # hardcoded dummy value unknown MM_MODEM_CDMA_ACTIVATION_STATE_UNKNOWN
            'Meid': Variant('s', ''),
            'Esn': Variant('s', ''),
            'Sid': Variant('u', 0),
            'Nid': Variant('u', 0),
            'Cdma1xRegistrationState': Variant('u', 0), # hardcoded dummy value MM_MODEM_CDMA_REGISTRATION_STATE_UNKNOWN
            'EvdoRegistrationState': Variant('u', 0) # hardcoded dummy value MM_MODEM_CDMA_REGISTRATION_STATE_UNKNOWN
        }

    @method()
    def Activate(self, carrier_code: 's'):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Cannot perform OTA activation: operation not supported')

    @method()
    def ActivateManuel(self, properties: 'a{sv}') -> 'o':
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Cannot perform manual activation: operation not supported')

    @dbus_property(access=PropertyAccess.READ)
    def ActivationState(self) -> 'u':
        return self.props['ActivationState'].value

    @dbus_property(access=PropertyAccess.READ)
    def Meid(self) -> 's':
        return self.props['Meid'].value

    @dbus_property(access=PropertyAccess.READ)
    def Esn(self) -> 's':
        return self.props['Esn'].value

    @dbus_property(access=PropertyAccess.READ)
    def Sid(self) -> 'u':
        return self.props['Sid'].value

    @dbus_property(access=PropertyAccess.READ)
    def Nid(self) -> 'u':
        return self.props['Nid'].value

    @dbus_property(access=PropertyAccess.READ)
    def Cdma1xRegistrationState(self) -> 'u':
        return self.props['Cdma1xRegistrationState'].value

    @dbus_property(access=PropertyAccess.READ)
    def EvdoRegistrationState(self) -> 'u':
        return self.props['Cdma1xRegistrationState'].value
