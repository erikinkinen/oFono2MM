from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

from ofono2mm.logging import ofono2mm_print

class MMModem3gppUssdInterface(ServiceInterface):
    def __init__(self, ofono_interfaces, verbose=False):
        super().__init__('org.freedesktop.ModemManager1.Modem.Modem3gpp.Ussd')
        ofono2mm_print("Initializing 3GPP USSD interface", verbose)
        self.ofono_interfaces = ofono_interfaces
        self.verbose = verbose
        self.props = {
            'State': Variant('u', 0), # on runtime unknown MM_MODEM_3GPP_USSD_SESSION_STATE_UNKNOWN
            'NetworkNotification': Variant('s', ''),
            'NetworkRequest': Variant('s', ''),
        }

    @method()
    async def Initiate(self, command: 's') -> 's':
        ofono2mm_print(f"Initiaate USSD with command {command}", self.verbose)

        result = await self.ofono_interfaces['org.ofono.SupplementaryServices'].call_initiate(command)
        return result[1].value

    @method()
    async def Respond(self, response: 's') -> 's':
        ofono2mm_print(f"Respond to 3GPP with command {response}", self.verbose)

        result = await self.ofono_interfaces['org.ofono.SupplementaryServices'].call_respond(response)
        return result

    @method()
    async def Cancel(self):
        ofono2mm_print("Cancelling USSD request", self.verbose)

        try:
            await self.ofono_interfaces['org.ofono.SupplementaryServices'].call_cancel()
        except Exception as e:
            ofono2mm_print(f"Failed to cancel USSD: {e}", self.verbose)

    @dbus_property(access=PropertyAccess.READ)
    async def State(self) -> 'u':
        try:
            result = await self.ofono_interfaces['org.ofono.SupplementaryServices'].call_get_properties()
            result_str = result['State'].value

            if result_str == 'idle':
                self.props['State'] = Variant('u', 1) # idle MM_MODEM_3GPP_USSD_SESSION_STATE_IDLE
            elif result_str == "active":
                self.props['State'] = Variant('u', 2) # active MM_MODEM_3GPP_USSD_SESSION_STATE_ACTIVE
            elif result_str == "user-response":
                self.props['State'] = Variant('u', 3) # user response MM_MODEM_3GPP_USSD_SESSION_STATE_USER_RESPONSE
            else:
                self.props['State'] = Variant('u', 0) # unknown MM_MODEM_3GPP_USSD_SESSION_STATE_UNKNOWN

            self.ofono_interfaces['org.ofono.SupplementaryServices'].on_notification_received(self.save_notification_received)
            self.ofono_interfaces['org.ofono.SupplementaryServices'].on_request_received(self.save_request_received)
        except Exception as e:
            ofono2mm_print(f"Failed to get state, marking as unknown: {e}", self.verbose)
            self.props['State'] = Variant('u', 0) # unknown MM_MODEM_3GPP_USSD_SESSION_STATE_UNKNOWN

        return self.props['State'].value

    def save_notification_received(self, message):
        ofono2mm_print(f"Save notification with message {message}", self.verbose)
        self.props['NetworkNotification'] = Variant('s', message)

    @dbus_property(access=PropertyAccess.READ)
    def NetworkNotification(self) -> 's':
        return self.props['NetworkNotification'].value

    def save_request_received(self, message):
        ofono2mm_print(f"Save request with message {message}", self.verbose)
        self.props['NetworkNotification'] = Variant('s', message)

    @dbus_property(access=PropertyAccess.READ)
    async def NetworkRequest(self) -> 's':
        return self.props['NetworkRequest'].value
