from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.constants import PropertyAccess
from dbus_next import Variant, DBusError

class MMModemOmaInterface(ServiceInterface):
    def __init__(self, mm_modem):
        super().__init__('org.freedesktop.ModemManager1.Modem.Oma')
        self.mm_modem = mm_modem
        self.props = {
            'Features': Variant('u', 0),
            'PendingNetworkInitiatedSessions': Variant('a(uu)', []),
            'SessionType': Variant('u', 0), # hardcoded dummy value unknown MM_OMA_SESSION_TYPE_UNKNOWN
            'SessionState': Variant('i', 0) # hardcoded dummy value unknown MM_OMA_SESSION_STATE_UNKNOWN
        }

    @method()
    def Setup(self, features: 'u'):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', f'Cannot setup OMA: operation not supported')

    @method()
    def StartClientInitiatedSession(self, session_type: 'u'):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', f'Cannot start client-initiated OMA session: operation not supported')

    @method()
    def AcceptNetworkInitiatedSession(self, session_id: 'u', accept: 'b'):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', f'Cannot accept network-initiated OMA session: operation not supported')

    @method()
    def CancelSession(self):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', f'Cannot cancel OMA session: operation not supported')

    @signal()
    def SessionStateChanged(self, old_session_state: 'i', new_session_state: 'i', session_state_failed_reason: 'u'):
        pass

    @dbus_property(access=PropertyAccess.READ)
    def Features(self) -> 'u':
        return self.props['Features'].value

    @dbus_property(access=PropertyAccess.READ)
    def PendingNetworkInitiatedSessions(self) -> 'a(uu)':
        return self.props['PendingNetworkInitiatedSessions'].value

    @dbus_property(access=PropertyAccess.READ)
    def SessionType(self) -> 'u':
        return self.props['SessionType'].value

    @dbus_property(access=PropertyAccess.READ)
    def SessionState(self) -> 'i':
        return self.props['SessionState'].value
