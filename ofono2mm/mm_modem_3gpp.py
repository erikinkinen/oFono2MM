import asyncio

from dbus_next.service import ServiceInterface, method, dbus_property
from dbus_next.constants import PropertyAccess
from dbus_next import Variant, DBusError

from ofono2mm.logging import ofono2mm_print

class MMModem3gppInterface(ServiceInterface):
    def __init__(self, ofono_client, modem_name, ofono_props, ofono_interfaces, ofono_interface_props, verbose=False):
        super().__init__('org.freedesktop.ModemManager1.Modem.Modem3gpp')
        ofono2mm_print("Initializing 3GPP interface", verbose)
        self.ofono_client = ofono_client
        self.modem_name = modem_name
        self.ofono_props = ofono_props
        self.ofono_interfaces = ofono_interfaces
        self.ofono_interface_props = ofono_interface_props
        self.verbose = verbose
        self.props = {
            'Imei': Variant('s', ''),
            'RegistrationState': Variant('u', 0), # on runtime idle MM_MODEM_3GPP_REGISTRATION_STATE_IDLE
            'OperatorCode': Variant('s', ''),
            'OperatorName': Variant('s', ''),
            'EnabledFacilityLocks': Variant('u', 0), # on runtime none MM_MODEM_3GPP_FACILITY_NONE
            'SubscriptionState': Variant('u', 0), # on runtime unknown MM_MODEM_3GPP_SUBSCRIPTION_STATE_UNKNOWN
            'EpsUeModeOperation': Variant('u', 4), # on runtime CSPS2 MM_MODEM_3GPP_EPS_UE_MODE_OPERATION_CSPS_2
            'Pco': Variant('a(ubay)', []),
            'InitialEpsBearer': Variant('o', '/org/freedesktop/ModemManager1/Bearer/0'),
            'InitialEpsBearerSettings': Variant('a{sv}', {
                'profile-id': Variant('u', 1),
                'profile-name': Variant('s', ''),
                'apn': Variant('s', ''),
                'allowed-auth': Variant('u', 1),
                'ip-type': Variant('u', 4)
            }),
            'PacketServiceState': Variant('u', 0), # on runtime unknown MM_MODEM_3GPP_PACKET_SERVICE_STATE_UNKNOWN
            'Nr5gRegistrationSettings': Variant('a{sv}', {
                'mico-mode': Variant('u', 0), # hardcoded value unknown MM_MODEM_3GPP_MICO_MODE_UNKNOWN
                'dtx-cycle': Variant('u', 0) # hardcoded value unknown MM_MODEM_3GPP_DRX_CYCLE_UNKNOWN
            })
        }

    async def set_props(self):
        ofono2mm_print("Setting properties", self.verbose)

        old_props = self.props.copy()

        if 'org.ofono.NetworkRegistration' in self.ofono_interface_props:
            self.props['OperatorName'] = Variant('s', self.ofono_interface_props['org.ofono.NetworkRegistration']['Name'].value if "Name" in self.ofono_interface_props['org.ofono.NetworkRegistration'] else '')

            if 'MobileCountryCode' in self.ofono_interface_props['org.ofono.NetworkRegistration']:
                MCC = self.ofono_interface_props['org.ofono.NetworkRegistration']['MobileCountryCode'].value
            else:
                MCC = ''

            if 'MobileNetworkCode' in self.ofono_interface_props['org.ofono.NetworkRegistration']:
                MNC = self.ofono_interface_props['org.ofono.NetworkRegistration']['MobileNetworkCode'].value
            else:
                MNC = ''

            self.props['OperatorCode'] = Variant('s', f'{MCC}{MNC}')

            if 'Status' in self.ofono_interface_props['org.ofono.NetworkRegistration']:
                if self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "unregistered":
                    self.props['RegistrationState'] = Variant('u', 0) # idle MM_MODEM_3GPP_REGISTRATION_STATE_IDLE
                    self.props['PacketServiceState'] = Variant('u', 1) # detached MM_MODEM_3GPP_PACKET_SERVICE_STATE_DETACHED
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "registered":
                    self.props['RegistrationState'] = Variant('u', 1) # home MM_MODEM_3GPP_REGISTRATION_STATE_HOME
                    self.props['PacketServiceState'] = Variant('u', 2) # attached MM_MODEM_3GPP_PACKET_SERVICE_STATE_ATTACHED
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "searching":
                    self.props['RegistrationState'] = Variant('u', 2) # searching MM_MODEM_3GPP_REGISTRATION_STATE_SEARCHING
                    self.props['PacketServiceState'] = Variant('u', 0) # unknown MM_MODEM_3GPP_PACKET_SERVICE_STATE_UNKNOWN
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "denied":
                    self.props['RegistrationState'] = Variant('u', 3) # denied MM_MODEM_3GPP_REGISTRATION_STATE_DENIED
                    self.props['PacketServiceState'] = Variant('u', 0) # unknown MM_MODEM_3GPP_PACKET_SERVICE_STATE_UNKNOWN
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "unknown":
                    self.props['RegistrationState'] = Variant('u', 4) # unknown MM_MODEM_3GPP_REGISTRATION_STATE_UNKNOWN
                    self.props['PacketServiceState'] = Variant('u', 0) # unknown MM_MODEM_3GPP_PACKET_SERVICE_STATE_UNKNOWN
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "roaming":
                    self.props['RegistrationState'] = Variant('u', 5) # MM_MODEM_3GPP_REGISTRATION_STATE_ROAMING
                    self.props['PacketServiceState'] = Variant('u', 2) # attached MM_MODEM_3GPP_PACKET_SERVICE_STATE_ATTACHED
            else:
                self.props['RegistrationState'] = Variant('u', 4) # unknown MM_MODEM_3GPP_REGISTRATION_STATE_UNKNOWN
        else:
            self.props['OperatorName'] = Variant('s', '')
            self.props['OperatorCode'] = Variant('s', '')
            self.props['RegistrationState'] = Variant('u', 4) # unknown MM_MODEM_3GPP_REGISTRATION_STATE_UNKNOWN

        self.props['Imei'] = Variant('s', self.ofono_props['Serial'].value if 'Serial' in self.ofono_props else '')
        self.props['EnabledFacilityLocks'] = Variant('u', 0) # none MM_MODEM_3GPP_FACILITY_NONE

        try:
            contexts = await self.ofono_interfaces['org.ofono.ConnectionManager'].call_get_contexts()
            for ctx in contexts:
                ctx_type = ctx[1].get('Type', Variant('s', '')).value
                if ctx_type.lower() == "internet":
                    apn = ctx[1].get('AccessPointName', Variant('s', '')).value
                    auth_method = ctx[1].get('AuthenticationMethod', Variant('s', '')).value

                    self.props['InitialEpsBearerSettings'].value['apn'] = Variant('s', f'{apn}')
                    if auth_method == 'none':
                        self.props['InitialEpsBearerSettings'].value['allowed-auth'] = Variant('u', 1) # none MM_BEARER_ALLOWED_AUTH_NONE
                    elif auth_method == 'pap':
                        self.props['InitialEpsBearerSettings'].value['allowed-auth'] = Variant('u', 2) # pap MM_BEARER_ALLOWED_AUTH_PAP
                    elif auth_method == 'chap':
                        self.props['InitialEpsBearerSettings'].value['allowed-auth'] = Variant('u', 3) # chap MM_BEARER_ALLOWED_AUTH_CHAP
                    else:
                        self.props['InitialEpsBearerSettings'].value['allowed-auth'] = Variant('u', 0) # unknown MM_BEARER_ALLOWED_AUTH_UNKNOWN
        except Exception as e:
            ofono2mm_print(f"Failed to set eps bearer settings: {e}", self.verbose)

        changed_props = {}
        for prop in self.props:
            if self.props[prop].value != old_props[prop].value:
                changed_props.update({ prop: self.props[prop].value })

        self.emit_properties_changed(changed_props)

    @method()
    async def Register(self, operator_id: 's'):
        ofono2mm_print(f"Register with operator id '{operator_id}'", self.verbose)

        if 'org.ofono.NetworkRegistration' in self.ofono_interface_props and 'Status' in self.ofono_interface_props['org.ofono.NetworkRegistration']:
            if self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "unknown":
                raise DBusError('org.freedesktop.ModemManager1.Error.Core.WrongState', 'Device not yet enabled')
        else:
            raise DBusError('org.freedesktop.ModemManager1.Error.Core.WrongState', 'Device not yet enabled')

        if operator_id == "":
            if 'org.ofono.NetworkRegistration' in self.ofono_interfaces:
                try:
                    await self.ofono_interfaces['org.ofono.NetworkRegistration'].call_register()
                except DBusError:
                    ofono2mm_print(f"Failed to register to default operator", self.verbose)
            return
        try:
            ofono_operator_interface = self.ofono_client["ofono_operator"][f"{self.modem_name}/operator/{operator_id}"]['org.ofono.NetworkOperator']
            await ofono_operator_interface.call_register()
        except DBusError:
            ofono2mm_print(f"Failed to register to operator_id {operator_id}", self.verbose)

    @method()
    async def Scan(self) -> 'aa{sv}':
        ofono2mm_print("Scanning the network", self.verbose)

        operators = []
        ofono_operators = await self.ofono_interfaces['org.ofono.NetworkRegistration'].call_scan()
        for ofono_operator in ofono_operators:
            mm_operator = {}
            if ofono_operator[1]['Status'].value == "unknown":
                mm_operator.update({'status': Variant('u', 0)})
            if ofono_operator[1]['Status'].value == "available":
                mm_operator.update({'status': Variant('u', 1)})
            if ofono_operator[1]['Status'].value == "current":
                mm_operator.update({'status': Variant('u', 2)})
            if ofono_operator[1]['Status'].value == "forbidden":
                mm_operator.update({'status': Variant('u', 3)})

            mm_operator.update({'operator-long': ofono_operator[1]['Name']})
            mm_operator.update({'operator-short': ofono_operator[1]['Name']})
            mm_operator.update({'operator-code': Variant('s', ofono_operator[1]['MobileCountryCode'].value + ofono_operator[1]['MobileNetworkCode'].value)})

            current_tech = 0
            for tech in ofono_operator[1]['Technologies'].value:
                if tech == "nr":
                    current_tech |= 1 << 15
                elif tech == "lte":
                    current_tech |= 1 << 14
                elif tech == "umts":
                    current_tech |= 1 << 5
                elif tech == "gsm":
                    current_tech |= 1 << 1

            mm_operator.update({'access-technology': Variant('u', current_tech)})
            operators.append(mm_operator)

        return operators

    @method()
    async def SetEpsUeModeOperation(self, mode: 'u'):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Cannot set UE mode of operation for EPS: operation not supported')

    @method()
    async def SetInitialEpsBearerSettings(self, settings: 'a{sv}'):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Operation not supported')

    @method()
    async def SetNr5gRegistrationSettings(self, properties: 'a{sv}'):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Operation not supported')

    @method()
    async def DisableFacilityLock(self, properties: '(us)'):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Operation not supported')

    @method()
    async def SetCarrierLock(self, data: 'ay'):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Cannot send set carrier lock request to modem: operation not supported')

    @method()
    async def SetPacketServiceState(self, state: 'u'):
        raise DBusError('org.freedesktop.ModemManager1.Error.Core.Unsupported', 'Explicit packet service attach/detach operation not supported')

    @dbus_property(access=PropertyAccess.READ)
    def Imei(self) -> 's':
        return self.props['Imei'].value

    @dbus_property(access=PropertyAccess.READ)
    def RegistrationState(self) -> 'u':
        return self.props['RegistrationState'].value

    @dbus_property(access=PropertyAccess.READ)
    def OperatorCode(self) -> 's':
        return self.props['OperatorCode'].value

    @dbus_property(access=PropertyAccess.READ)
    def OperatorName(self) -> 's':
        return self.props['OperatorName'].value

    @dbus_property(access=PropertyAccess.READ)
    def EnabledFacilityLocks(self) -> 'u':
        return self.props['EnabledFacilityLocks'].value

    @dbus_property(access=PropertyAccess.READ)
    def SubscriptionState(self) -> 'u':
        return self.props['SubscriptionState'].value

    @dbus_property(access=PropertyAccess.READ)
    def EpsUeModeOperation(self) -> 'u':
        return self.props['EpsUeModeOperation'].value

    @dbus_property(access=PropertyAccess.READ)
    def Pco(self) -> 'a(ubay)':
        return self.props['Pco'].value

    @dbus_property(access=PropertyAccess.READ)
    def InitialEpsBearer(self) -> 'o':
        return self.props['InitialEpsBearer'].value

    @dbus_property(access=PropertyAccess.READ)
    def InitialEpsBearerSettings(self) -> 'a{sv}':
        return self.props['InitialEpsBearerSettings'].value

    @dbus_property(access=PropertyAccess.READ)
    def PacketServiceState(self) -> 'u':
        return self.props['PacketServiceState'].value

    @dbus_property(access=PropertyAccess.READ)
    def Nr5gRegistrationSettings(self) -> 'a{sv}':
        return self.props['Nr5gRegistrationSettings'].value

    def ofono_changed(self, name, varval):
        self.ofono_props[name] = varval
        asyncio.create_task(self.set_props())

    def ofono_interface_changed(self, iface):
        def ch(name, varval):
            if iface in self.ofono_interface_props:
                self.ofono_interface_props[iface][name] = varval
            asyncio.create_task(self.set_props())

        return ch
