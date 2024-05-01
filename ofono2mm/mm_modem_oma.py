from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.constants import PropertyAccess
from dbus_next import Variant, DBusError

from ofono2mm.logging import ofono2mm_print

class MMModemOmaInterface(ServiceInterface):
    def __init__(self, verbose=False):
        super().__init__('org.freedesktop.ModemManager1.Modem.Oma')
        ofono2mm_print("Initializing OMA interface", verbose)
        self.verbose = verbose
        self.props = {
            'Features': Variant('u', 0),
            'PendingNetworkInitiatedSessions': Variant('a(uu)', []),
            'SessionType': Variant('u', 0), # hardcoded dummy value unknown MM_OMA_SESSION_TYPE_UNKNOWN
            'SessionState': Variant('i', 0) # hardcoded dummy value unknown MM_OMA_SESSION_STATE_UNKNOWN
        }

    @method()
    def Setup(self, features: 'u'):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Cannot setup OMA: operation not supported')

    @method()
    def StartClientInitiatedSession(self, session_type: 'u'):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Cannot start client-initiated OMA session: operation not supported')

    @method()
    def AcceptNetworkInitiatedSession(self, session_id: 'u', accept: 'b'):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Cannot accept network-initiated OMA session: operation not supported')

    @method()
    def CancelSession(self):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Cannot cancel OMA session: operation not supported')

    @signal()
    def SessionStateChanged(self, old_session_state: 'i', new_session_state: 'i', session_state_failed_reason: 'u'):
        ofono2mm_print(f"Signal: Session state changed with old sttate {old_session_state} and new state {new_session_state}. failed reason (if any): {session_state_failed_reason}", self.verbose)

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
