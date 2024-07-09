import asyncio

from dbus_next.service import ServiceInterface, method, dbus_property
from dbus_next.constants import PropertyAccess
from dbus_next import Variant, DBusError

from ofono2mm.logging import ofono2mm_print

class MMModem3gppUssdInterface(ServiceInterface):
    def __init__(self, ofono_interfaces, modem_name, verbose=False):
        super().__init__('org.freedesktop.ModemManager1.Modem.Modem3gpp.Ussd')
        self.modem_name = modem_name
        ofono2mm_print("Initializing 3GPP USSD interface", verbose)
        self.ofono_interfaces = ofono_interfaces
        self.verbose = verbose
        self.network_notification_event = asyncio.Event()
        self.props = {
            'State': Variant('u', 0), # on runtime unknown MM_MODEM_3GPP_USSD_SESSION_STATE_UNKNOWN
            'NetworkNotification': Variant('s', ''),
            'NetworkRequest': Variant('s', ''),
        }

    @method()
    async def Initiate(self, command: 's') -> 's':
        ofono2mm_print(f"Initiating USSD with command {command}", self.verbose)

        if self.props['State'].value in (2, 3): # 2: active, 3: user-response
            raise DBusError('org.freedesktop.ModemManager1.Error.Core.WrongState', 'Cannot initiate USSD: a session is already active')

        ret = await self.run_initiate(command)
        return ret

    async def run_initiate(self, command):
        self.initiate_task = asyncio.create_task(
            self.ofono_interfaces['org.ofono.SupplementaryServices'].call_initiate(command)
        )
        try:
            await self.network_notification_event.wait() # Wait for the network notification to change
            self.initiate_task.cancel() # Cancel the task when the event is triggered
            try:
                await self.initiate_task
            except asyncio.CancelledError:
                pass

            return self.props['NetworkNotification'].value
        except Exception as e:
            ofono2mm_print(f"Failed to initiate USSD: {e}", self.verbose)

    @method()
    async def Respond(self, response: 's') -> 's':
        ofono2mm_print(f"Respond to 3GPP with command {response}", self.verbose)

        if self.props['State'].value in (1, 2): # 1: idle, 2: active
            raise DBusError('org.freedesktop.ModemManager1.Error.Core.WrongState', 'Cannot respond USSD: no active session')

        # for some reason ofono refuses to respond for 20-30 seconds after it has been initiated
        retries = 10
        for attempt in range(retries):
            try:
                result = await self.ofono_interfaces['org.ofono.SupplementaryServices'].call_respond(response)
                return result
            except Exception as e:
                ofono2mm_print(f"Attempt {attempt + 1}: Failed to respond: {e}", self.verbose)
                if str(e) == "Operation already in progress" and attempt < retries - 1:
                    # there must be a better way...
                    await asyncio.sleep(5)
                else:
                    return ''
        return ''

    @method()
    async def Cancel(self):
        ofono2mm_print("Cancelling USSD request", self.verbose)

        try:
            await self.ofono_interfaces['org.ofono.SupplementaryServices'].call_cancel()
        except DBusError as e:
            if "Operation is not active or in progress" in str(e):
                raise DBusError('org.freedesktop.ModemManager1.Error.Core.WrongState', 'Cannot respond USSD: no active session')
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
        self.network_notification_event.set() # Signal that the notification has been received
        self.network_notification_event.clear() # Reset the event for the next notification

    @dbus_property(access=PropertyAccess.READ)
    async def NetworkRequest(self) -> 's':
        return self.props['NetworkRequest'].value
