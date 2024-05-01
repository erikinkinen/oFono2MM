from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

from ofono2mm.logging import ofono2mm_print

class MMCallInterface(ServiceInterface):
    def __init__(self, ofono_client, ofono_interfaces, verbose=False):
        super().__init__('org.freedesktop.ModemManager1.Call')
        ofono2mm_print("Initializing Call interface", verbose)
        self.ofono_client = ofono_client
        self.ofono_interfaces = ofono_interfaces
        self.verbose = verbose
        self.voicecall = '/'
        self.props = {
            'State': Variant('u', 0), # on runtime unknown MM_CALL_STATE_UNKNOWN
            'StateReason': Variant('u', 0), # on runtime unknown MM_CALL_STATE_REASON_UNKNOWN
            'Direction': Variant('u', 0), # on runtime unknown MM_CALL_DIRECTION_UNKNOWN
            'Number': Variant('s', ''),
            'Multiparty': Variant('b', False),
            'AudioPort': Variant('s', ''),
            'AudioFormat': Variant('a{sv}', {
                "encoding": Variant('s', 'pcm'),
                "resolution": Variant('s', 's16le'),
                "rate": Variant('u', 48000),
            })
        }

    @method()
    def Start(self):
        ofono2mm_print("Starting call", self.verbose)
        self.props['State'] = Variant('u', 4) # active MM_CALL_STATE_ACTIVE
        self.props['StateReason'] = Variant('u', 1) # accepted MM_CALL_STATE_REASON_OUTGOING_STARTED

    @method()
    async def Accept(self):
        ofono2mm_print("Accepting call", self.verbose)
        ofono_interface = self.ofono_client["ofono_modem"][self.voicecall]['org.ofono.VoiceCall']
        await ofono_interface.call_answer()
        self.props['State'] = Variant('u', 4) # active MM_CALL_STATE_ACTIVE
        self.props['StateReason'] = Variant('u', 3) # accepted MM_CALL_STATE_REASON_ACCEPTED

    @method()
    async def Deflect(self, number: 's'):
        ofono2mm_print(f"Deflecting number {number}", self.verbose)
        ofono_interface = self.ofono_client["ofono_modem"][self.voicecall]['org.ofono.VoiceCall']
        await ofono_interface.call_deflect(number)
        self.props['StateReason'] = Variant('u', 10) # deflected MM_CALL_STATE_REASON_DEFLECTED

    @method()
    async def JoinMultiparty(self):
        ofono2mm_print("Joining multiparty", self.verbose)
        await self.ofono_interfaces['org.ofono.VoiceCallManager'].call_create_multiparty()
        self.props['Multiparty'] = Variant('b', True)

    @method()
    async def LeaveMultiparty(self):
        ofono2mm_print("Leaving multiparty", self.verbose)
        await self.ofono_interfaces['org.ofono.VoiceCallManager'].call_hangup_multiparty()
        self.props['Multiparty'] = Variant('b', False)

    @method()
    async def Hangup(self):
        ofono2mm_print("Hanging up call", self.verbose)

        try:
            ofono_interface = self.ofono_client["ofono_modem"][self.voicecall]['org.ofono.VoiceCall']
            await ofono_interface.call_hangup()
        except Exception as e:
            ofono2mm_print(f"Failed to hang up call: {e}", self.verbose)
            ofono2mm_print("Calling hang up all instead", self.verbose)
            await self.ofono_interfaces['org.ofono.VoiceCallManager'].call_hangup_all()

        self.props['State'] = Variant('u', 7) # terminated MM_CALL_STATE_TERMINATED
        self.props['StateReason'] = Variant('u', 4) # terminated MM_CALL_STATE_REASON_TERMINATED

    @method()
    async def SendDtmf(self, dtmf: 's'):
        ofono2mm_print("Send dtmf {dtmf}", self.verbose)
        await self.ofono_interfaces['org.ofono.VoiceCallManager'].call_send_tones(dtmf)

    @signal()
    def DtmfReceived(self, dtmf) -> 's':
        ofono2mm_print("Dtmf {dtmf} received", self.verbose)
        return dtmf

    @signal()
    def StateChanged(self, old, new, reason) -> 'iiu':
        ofono2mm_print("State changed from {old} to {new} for reason {reason}", self.verbose)
        return [old, new, reason]

    @dbus_property(access=PropertyAccess.READ)
    def State(self) -> 'i':
        return self.props['State'].value

    @dbus_property(access=PropertyAccess.READ)
    def StateReason(self) -> 'i':
        return self.props['StateReason'].value

    @dbus_property(access=PropertyAccess.READ)
    def Direction(self) -> 'i':
        return self.props['Direction'].value

    @dbus_property(access=PropertyAccess.READ)
    def Number(self) -> 's':
        return self.props['Number'].value

    @dbus_property(access=PropertyAccess.READ)
    def Multiparty(self) -> 'b':
        return self.props['Multiparty'].value

    @dbus_property(access=PropertyAccess.READ)
    def AudioPort(self) -> 's':
        return self.props['AudioPort'].value

    @dbus_property(access=PropertyAccess.READ)
    def AudioFormat(self) -> 'a{sv}':
        return self.props['AudioFormat'].value
