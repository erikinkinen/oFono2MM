from dbus_next.service import ServiceInterface, method, dbus_property
from dbus_next.constants import PropertyAccess
from dbus_next import Variant, DBusError

class MMModemSarInterface(ServiceInterface):
    def __init__(self):
        super().__init__('org.freedesktop.ModemManager1.Modem.Sar')
        self.props = {
            'State': Variant('b', False),
            'PowerLevel': Variant('u', 0)
        }

    @dbus_property(access=PropertyAccess.READ)
    def State(self) -> 'b':
        return self.props['State'].value

    @dbus_property(access=PropertyAccess.READ)
    def PowerLevel(self) -> 'u':
        return self.props['PowerLevel'].value

    @method()
    def Enable(self, enable: 'b'):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', f'Cannot setup SAR: operation not supported')

    @method()
    def SetPowerLevel(self, level: 'u'):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', f'Cannot set SAR power level: SAR is disabled')
