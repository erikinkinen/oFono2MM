from dbus_next.service import (ServiceInterface,
                               method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

from ofono2mm.mm_sms import MMSmsInterface

message_i = 1

class MMModemMessagingInterface(ServiceInterface):
    def __init__(self, bus, ofono_props, ofono_interfaces, ofono_interface_props):
        super().__init__('org.freedesktop.ModemManager1.Modem.Messaging')
        self.bus = bus
        self.ofono_props = ofono_props
        self.ofono_interfaces = ofono_interfaces
        self.ofono_interface_props = ofono_interface_props
        self.props = {
            'Messages': Variant('ao', []),
            'SupportedStorages': Variant('au', []),
            'DefaultStorage': Variant('u', 0) # hardcoded value unknown MM_SMS_STORAGE_UNKNOWN
        }

    def set_props(self):
        old_props = self.props

        for prop in self.props:
            if self.props[prop].value != old_props[prop].value:
                self.emit_properties_changed({prop: self.props[prop].value})

    async def init_messages(self):
        if 'org.ofono.MessageManager' in self.ofono_interfaces:
            self.ofono_interfaces['org.ofono.MessageManager'].on_incoming_message(self.add_incoming_message)

    def add_incoming_message(self, msg, props):
        global message_i
        mm_sms_interface = MMSmsInterface()
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
        return self.props['Messages'].value

    @method()
    async def Delete(self, path: 'o'):
        if path in self.props['Messages'].value:
            self.props['Messages'].value.remove(path)
            self.bus.unexport(path)
            self.emit_properties_changed({'Messages': self.props['Messages'].value})
            self.Deleted(path)

    @method()
    async def Create(self, properties: 'a{sv}') -> 'o':
        global message_i
        if 'number' not in properties or 'text' not in properties:
            return

        mm_sms_interface = MMSmsInterface()
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
            ofono_sms_path = await self.ofono_interfaces['org.ofono.MessageManager'].call_send_message(properties['number'].value, properties['text'].value)

        return f'/org/freedesktop/ModemManager1/SMS/{message_i_old}'

    @signal()
    def Added(self, path, received) -> 'ob':
        return [path, received]

    @signal()
    def Deleted(self, path) -> 'o':
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

    def ofono_interface_changed(self, iface):
        def ch(name, varval):
            if iface in self.ofono_interface_props:
                self.ofono_interface_props[iface][name] = varval
            self.set_props()

        return ch
