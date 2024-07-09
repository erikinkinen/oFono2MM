from dbus_next.service import (ServiceInterface,
                               method, dbus_property)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant, DBusError

from ofono2mm.logging import ofono2mm_print

class MMSimInterface(ServiceInterface):
    def __init__(self, modem_name, ofono_props, ofono_interfaces, ofono_interface_props, verbose=False):
        super().__init__('org.freedesktop.ModemManager1.Sim')
        self.modem_name = modem_name
        ofono2mm_print("Initializing SIM interface", verbose)
        self.ofono_props = ofono_props
        self.ofono_interfaces = ofono_interfaces
        self.ofono_interface_props = ofono_interface_props
        self.verbose = verbose
        self.props = {
            'Active': Variant('b', True),
            'SimIdentifier': Variant('s', ''),
            'IMSI': Variant('s', '0'),
            'Eid': Variant('s', ''),
            'OperatorIdentifier': Variant('s', '0'),
            'OperatorName': Variant('s', ''),
            'EmergencyNumbers': Variant('as', []),
            'PreferredNetworks': Variant('a(su)', []),
            'Gid1': Variant('ay', bytes()),
            'Gid2': Variant('ay', bytes()),
            'SimType': Variant('u', 1), # hardcoded value physical MM_SIM_TYPE_PHYSICAL
            'EsimStatus': Variant('u', 0), # hardcoded value unknown MM_SIM_ESIM_STATUS_UNKNOWN
            'Removability': Variant('u', 1) # hardcoded value MM_SIM_REMOVABILITY_REMOVABLE
        }

    def set_props(self):
        ofono2mm_print("Setting properties", self.verbose)

        old_props = self.props

        if 'org.ofono.SimManager' in self.ofono_interface_props:
            if 'Present' in self.ofono_interface_props['org.ofono.SimManager']:
                if self.ofono_interface_props['org.ofono.SimManager']:
                    self.props['Active'] = Variant('b', True)
                else:
                    self.props['Active'] = Variant('b', False)
            else:
                self.props['Active'] = Variant('b', False)
            if 'CardIdentifier' in self.ofono_interface_props['org.ofono.SimManager']:
                self.props['SimIdentifier'] = Variant('s', self.ofono_interface_props['org.ofono.SimManager']['CardIdentifier'].value)
            else:
                self.props['SimIdentifier'] = Variant('s', '')
            if 'SubscriberIdentity' in self.ofono_interface_props['org.ofono.SimManager']:
                self.props['IMSI'] = Variant('s', self.ofono_interface_props['org.ofono.SimManager']['SubscriberIdentity'].value)
            else:
                self.props['IMSI'] = Variant('s', '')

            
            if 'MobileCountryCode' in self.ofono_interface_props['org.ofono.SimManager']:
                MCC = self.ofono_interface_props['org.ofono.SimManager']['MobileCountryCode'].value
            else:
                MCC = ''

            if 'MobileNetworkCode' in self.ofono_interface_props['org.ofono.SimManager']:
                MNC = self.ofono_interface_props['org.ofono.SimManager']['MobileNetworkCode'].value
            else:
                MNC = ''

            self.props['OperatorIdentifier'] = Variant('s', f"{MCC}{MNC}" if MCC != '' else '')
            self.props['PreferredNetworks'] = Variant('a(su)', [[f"{MCC}{MNC}", 19]])
        else:
            self.props['Active'] = Variant('b', False)
            self.props['SimIdentifier'] = Variant('s', '')
            self.props['IMSI'] = Variant('s', '')
            self.props['OperatorIdentifier'] = Variant('s', '')
            self.props['PreferredNetworks'] = Variant('a(su)', [])

        if 'org.ofono.VoiceCallManager' in self.ofono_interface_props:
            self.props['EmergencyNumbers'] = Variant('as', self.ofono_interface_props['org.ofono.VoiceCallManager']['EmergencyNumbers'].value if 'EmergencyNumbers' in self.ofono_interface_props['org.ofono.VoiceCallManager'] else [])

        for prop in self.props:
            if self.props[prop].value != old_props[prop].value:
                self.emit_properties_changed({prop: self.props[prop].value})

    @method()
    async def SendPin(self, pin: 's'):
        ofono2mm_print(f"Sending pin {pin}", self.verbose)

        if 'org.ofono.SimManager' in self.ofono_interfaces:
            await self.ofono_interfaces['org.ofono.SimManager'].call_enter_pin('pin', pin)
        else:
            raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Cannot send PIN: SIM not currently active')

    @method()
    async def SendPuk(self, puk: 's', pin: 's'):
        ofono2mm_print(f"Sending puk {puk} pin {pin}", self.verbose)

        if 'org.ofono.SimManager' in self.ofono_interfaces:
            await self.ofono_interfaces['org.ofono.SimManager'].call_reset_pin('pin', puk, pin)
        else:
            raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Cannot send PUK: SIM not currently active')

    @method()
    async def EnablePin(self, pin: 's', enabled: 'b'):
        ofono2mm_print(f"Enabling pin: {enabled} set pin to {pin}", self.verbose)

        if 'org.ofono.SimManager' in self.ofono_interfaces:
            if enabled:
                await self.ofono_interfaces['org.ofono.SimManager'].call_lock_pin('pin', pin)
            else:
                await self.ofono_interfaces['org.ofono.SimManager'].call_unlock_pin('pin', pin)
        else:
            raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Cannot enable/disable PIN: SIM not currently active')

    @method()
    async def ChangePin(self, old_pin: 's', new_pin: 's'):
        ofono2mm_print(f"Change pin from {old_pin} to {new_pin}", self.verbose)

        if 'org.ofono.SimManager' in self.ofono_interfaces:
            await self.ofono_interfaces['org.ofono.SimManager'].call_change_pin('pin', old_pin, new_pin)
        else:
            raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Cannot change PIN: SIM not currently active')

    @method()
    async def SetPreferredNetworks(self, preferred_networks: 'a(su)'):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'setting preferred networks is unsupported')

    @dbus_property(access=PropertyAccess.READ)
    def Active(self) -> 'b':
        return self.props['Active'].value

    @dbus_property(access=PropertyAccess.READ)
    def SimIdentifier(self) -> 's':
        return self.props['SimIdentifier'].value

    @dbus_property(access=PropertyAccess.READ)
    def IMSI(self) -> 's':
        return self.props['IMSI'].value

    @dbus_property(access=PropertyAccess.READ)
    def Eid(self) -> 's':
        return self.props['Eid'].value

    @dbus_property(access=PropertyAccess.READ)
    def OperatorIdentifier(self) -> 's':
        return self.props['OperatorIdentifier'].value

    @dbus_property(access=PropertyAccess.READ)
    def OperatorName(self) -> 's':
        return self.props['OperatorName'].value

    @dbus_property(access=PropertyAccess.READ)
    def EmergencyNumbers(self) -> 'as':
        return self.props['EmergencyNumbers'].value

    @dbus_property(access=PropertyAccess.READ)
    def PreferredNetworks(self) -> 'a(su)':
        return self.props['PreferredNetworks'].value

    @dbus_property(access=PropertyAccess.READ)
    def Gid1(self) -> 'ay':
        return self.props['Gid1'].value

    @dbus_property(access=PropertyAccess.READ)
    def Gid2(self) -> 'ay':
        return self.props['Gid2'].value

    @dbus_property(access=PropertyAccess.READ)
    def SimType(self) -> 'u':
        return self.props['SimType'].value

    @dbus_property(access=PropertyAccess.READ)
    def EsimStatus(self) -> 'u':
        return self.props['EsimStatus'].value

    @dbus_property(access=PropertyAccess.READ)
    def Removability(self) -> 'u':
        return self.props['Removability'].value

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
