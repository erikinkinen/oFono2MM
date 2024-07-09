from dbus_next.service import (ServiceInterface,
                               method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

from ofono2mm.mm_sms import MMSmsInterface
from ofono2mm.logging import ofono2mm_print

message_i = 1

class MMModemMessagingInterface(ServiceInterface):
    def __init__(self, bus, modem_name, ofono_props, ofono_interfaces, ofono_interface_props, verbose=False):
        super().__init__('org.freedesktop.ModemManager1.Modem.Messaging')
        self.modem_name = modem_name
        ofono2mm_print("Initializing Messaging interface", verbose)
        self.bus = bus
        self.ofono_props = ofono_props
        self.ofono_interfaces = ofono_interfaces
        self.ofono_interface_props = ofono_interface_props
        self.verbose = verbose
        self.props = {
            'Messages': Variant('ao', []),
            'SupportedStorages': Variant('au', []),
            'DefaultStorage': Variant('u', 0) # hardcoded value unknown MM_SMS_STORAGE_UNKNOWN
        }

    def set_props(self):
        ofono2mm_print("Setting properties", self.verbose)

        old_props = self.props

        for prop in self.props:
            if self.props[prop].value != old_props[prop].value:
                self.emit_properties_changed({prop: self.props[prop].value})

    async def init_messages(self):
        ofono2mm_print("Initializing signals", self.verbose)

        if 'org.ofono.MessageManager' in self.ofono_interfaces:
            self.ofono_interfaces['org.ofono.MessageManager'].on_incoming_message(self.add_incoming_message)

        if 'org.ofono.MessageManager' in self.ofono_interfaces:
            self.ofono_interfaces['org.ofono.MessageManager'].on_immediate_message(self.add_incoming_message)

    def add_incoming_message(self, msg, props):
        ofono2mm_print(f"Add incoming message {msg} with properties {props}", self.verbose)

        global message_i
        mm_sms_interface = MMSmsInterface(self.verbose)
        mm_sms_interface.props.update({
            'State': Variant('u', 3), # hardcoded value received MM_SMS_STATE_RECEIVED
            'PduType': Variant('u', 1), # hardcoded value deliver MM_SMS_PDU_TYPE_DELIVER
            'Number': props['Sender'],
            'Text': Variant('s', msg),
            'Timestamp': props['SentTime']
        })

        self.bus.export(f'/org/freedesktop/ModemManager1/SMS/{message_i}', mm_sms_interface)
        self.props['Messages'].value.append(f'/org/freedesktop/ModemManager1/SMS/{message_i}')
        self.emit_properties_changed({'Messages': self.props['Messages'].value})
        self.Added(f'/org/freedesktop/ModemManager1/SMS/{message_i}', True)
        message_i += 1

    @method()
    async def List(self) -> 'ao':
        ofono2mm_print("Returning list of messages", self.verbose)
        return self.props['Messages'].value

    @method()
    async def Delete(self, path: 'o'):
        ofono2mm_print(f"Delete message with object path {path}", self.verbose)

        if path in self.props['Messages'].value:
            self.props['Messages'].value.remove(path)
            self.bus.unexport(path)
            self.emit_properties_changed({'Messages': self.props['Messages'].value})
            self.Deleted(path)

    @method()
    async def Create(self, properties: 'a{sv}') -> 'o':
        ofono2mm_print(f"Create message with properties {properties}", self.verbose)

        global message_i
        if 'number' not in properties or 'text' not in properties:
            return

        mm_sms_interface = MMSmsInterface(self.verbose)
        mm_sms_interface.props.update({
            'Text': properties['text'],
            'Number': properties['number'],
            'DeliveryReportRequest': properties['delivery-report-request'] if 'delivery-report-request' in properties else Variant('b', False)
        })

        self.bus.export(f'/org/freedesktop/ModemManager1/SMS/{message_i}', mm_sms_interface)
        self.props['Messages'].value.append(f'/org/freedesktop/ModemManager1/SMS/{message_i}')
        self.emit_properties_changed({'Messages': self.props['Messages'].value})
        self.Added(f'/org/freedesktop/ModemManager1/SMS/{message_i}', True)
        message_i_old = message_i
        message_i += 1

        if 'org.ofono.MessageManager' in self.ofono_interfaces:
            await self.ofono_interfaces['org.ofono.MessageManager'].call_send_message(properties['number'].value, properties['text'].value)

        return f'/org/freedesktop/ModemManager1/SMS/{message_i_old}'

    @signal()
    def Added(self, path, received) -> 'ob':
        ofono2mm_print(f"Signal: Message added at object path {path} and received state {received}", self.verbose)
        return [path, received]

    @signal()
    def Deleted(self, path) -> 'o':
        ofono2mm_print(f"Signal: Message deleted at object path {path}", self.verbose)
        return path

    @dbus_property(access=PropertyAccess.READ)
    def Messages(self) -> 'ao':
        return self.props['Messages'].value

    @dbus_property(access=PropertyAccess.READ)
    def SupportedStorages(self) -> 'au':
        return self.props['SupportedStorages'].value

    @dbus_property(access=PropertyAccess.READ)
    def DefaultStorage(self) -> 'u':
        return self.props['DefaultStorage'].value

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
