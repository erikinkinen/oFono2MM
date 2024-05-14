from time import time
from uuid import uuid4

import NetworkManager

from dbus_next.service import ServiceInterface, method
from dbus_next import Variant

from ofono2mm.logging import ofono2mm_print
from ofono2mm.utils import save_setting, read_setting

from dbus import SystemBus, Interface
from dbus.mainloop.glib import DBusGMainLoop

class MMModemSimpleInterface(ServiceInterface):
    def __init__(self, mm_modem, ofono_props, ofono_interfaces, ofono_interface_props, verbose=False):
        super().__init__('org.freedesktop.ModemManager1.Modem.Simple')
        ofono2mm_print("Initializing Simple interface", verbose)
        self.mm_modem = mm_modem
        self.ofono_props = ofono_props
        self.ofono_interfaces = ofono_interfaces
        self.ofono_interface_props = ofono_interface_props
        self.verbose = verbose
        self.props = {
             'state': Variant('u', 7), # on runtime enabled MM_MODEM_STATE_ENABLED
             'signal-quality': Variant('(ub)', [0, True]),
             'current-bands': Variant('au', []),
             'access-technologies': Variant('u', 0), # on runtime unknown MM_MODEM_ACCESS_TECHNOLOGY_UNKNOWN
             'm3gpp-registration-state': Variant('u', 0), # on runtime idle MM_MODEM_3GPP_REGISTRATION_STATE_IDLE
             'm3gpp-operator-code': Variant('s', ''),
             'm3gpp-operator-name': Variant('s', ''),
             'cdma-cdma1x-registration-state': Variant('u', 0),
             'cdma-evdo-registration-state': Variant('u', 0),
             'cdma-sid': Variant('u', 0),
             'cdma-nid': Variant('u', 0)
        }

    def set_props(self):
        ofono2mm_print("Setting properties", self.verbose)

        old_props = self.props

        if 'org.ofono.NetworkRegistration' in self.ofono_interface_props:
            self.props['m3gpp-operator-name'] = Variant('s', self.ofono_interface_props['org.ofono.NetworkRegistration']['Name'].value if "Name" in self.ofono_interface_props['org.ofono.NetworkRegistration'] else '')

            if 'MobileCountryCode' in self.ofono_interface_props['org.ofono.NetworkRegistration']:
                MCC = self.ofono_interface_props['org.ofono.NetworkRegistration']['MobileCountryCode'].value
            else:
                MCC = ''

            if 'MobileNetworkCode' in self.ofono_interface_props['org.ofono.NetworkRegistration']:
                MNC = self.ofono_interface_props['org.ofono.NetworkRegistration']['MobileNetworkCode'].value
            else:
                MNC = ''

            self.props['m3gpp-operator-code'] = Variant('s', f'{MCC}{MNC}')

            if 'Strength' in self.ofono_interface_props['org.ofono.NetworkRegistration']:
                self.props['signal-quality'] = Variant('(ub)', [self.ofono_interface_props['org.ofono.NetworkRegistration']['Strength'].value, True])

            if 'Status' in self.ofono_interface_props['org.ofono.NetworkRegistration']:
                if self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == 'registered' or self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == 'roaming':
                    self.props['state'] = Variant('u', 9) # registered MM_MODEM_STATE_REGISTERED
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == 'searching':
                    self.props['state'] = Variant('u', 8) # searching MM_MODEM_STATE_SEARCHING
                else:
                    self.props['state'] = Variant('u', 7) # enabled MM_MODEM_STATE_ENABLED

            if 'Status' in self.ofono_interface_props['org.ofono.NetworkRegistration']:
                if self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "unregistered":
                    self.props['m3gpp-registration-state'] = Variant('u', 0) # idle MM_MODEM_3GPP_REGISTRATION_STATE_IDLE
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "registered":
                    self.props['m3gpp-registration-state'] = Variant('u', 1) # home MM_MODEM_3GPP_REGISTRATION_STATE_HOME
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "searching":
                    self.props['m3gpp-registration-state'] = Variant('u', 2) # searching MM_MODEM_3GPP_REGISTRATION_STATE_SEARCHING
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "denied":
                    self.props['m3gpp-registration-state'] = Variant('u', 3) # denied MM_MODEM_3GPP_REGISTRATION_STATE_DENIED
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "unknown":
                    self.props['m3gpp-registration-state'] = Variant('u', 4) # unknown MM_MODEM_3GPP_REGISTRATION_STATE_UNKNOWN
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == "roaming":
                    self.props['m3gpp-registration-state'] = Variant('u', 5) # roaming MM_MODEM_3GPP_REGISTRATION_STATE_ROAMING
            else:
                self.props['m3gpp-registration-state'] = Variant('u', 4) # unknown MM_MODEM_3GPP_REGISTRATION_STATE_UNKNOWN
        else:
            self.props['m3gpp-operator-name'] = Variant('s', '')
            self.props['m3gpp-operator-code'] = Variant('s', '')
            self.props['signal-quality'] = Variant('(ub)', [0, True])
            self.props['state'] = Variant('u', 7) # enabled MM_MODEM_STATE_ENABLED

        if 'org.ofono.NetworkRegistration' in self.ofono_interface_props and self.props['state'].value >= 7:
            if "Technology" in self.ofono_interface_props['org.ofono.NetworkRegistration']:
                current_tech = 0
                if self.ofono_interface_props['org.ofono.NetworkRegistration']["Technology"].value == "nr":
                    current_tech |= 1 << 15 # network is 5g MM_MODEM_ACCESS_TECHNOLOGY_5GNR
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']["Technology"].value == "lte":
                    current_tech |= 1 << 14 # network is lte MM_MODEM_ACCESS_TECHNOLOGY_LTE
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']["Technology"].value == "hspap":
                    current_tech |= 1 << 9 # network is hspa plus MM_MODEM_ACCESS_TECHNOLOGY_HSPA_PLUS
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']["Technology"].value == "hspa":
                    current_tech |= 1 << 8 # network is hspa MM_MODEM_ACCESS_TECHNOLOGY_HSPA
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']["Technology"].value == "hsupa":
                    current_tech |= 1 << 7 # network is hsupa MM_MODEM_ACCESS_TECHNOLOGY_HSUPA
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']["Technology"].value == "hsdpa":
                    current_tech |= 1 << 6 # network is hsdpa MM_MODEM_ACCESS_TECHNOLOGY_HSDPA
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']["Technology"].value == "umts":
                    current_tech |= 1 << 5 # network is umts MM_MODEM_ACCESS_TECHNOLOGY_UMTS
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']["Technology"].value == "edge":
                    current_tech |= 1 << 4 # network is edge MM_MODEM_ACCESS_TECHNOLOGY_EDGE
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']["Technology"].value == "gprs":
                    current_tech |= 1 << 3 # network is gprs MM_MODEM_ACCESS_TECHNOLOGY_GPRS
                elif self.ofono_interface_props['org.ofono.NetworkRegistration']["Technology"].value == "gsm":
                    current_tech |= 1 << 1 # network is gsm MM_MODEM_ACCESS_TECHNOLOGY_GSM

                self.props['access-technologies'] = Variant('u', current_tech)
            else:
                self.props['access-technologies'] = Variant('u', 0) # network is unknown MM_MODEM_ACCESS_TECHNOLOGY_UNKNOWN
        else:
            self.props['access-technologies'] = Variant('u', 0) # network is unknown MM_MODEM_ACCESS_TECHNOLOGY_UNKNOWN

        supported_bands = []
        gsm_bands = [1, 2, 3, 4, 14, 15, 16, 17, 18, 19, 20]
        umts_bands = [5, 6, 7, 8, 9, 10, 11, 12, 13, 210, 211, 212, 213, 214, 219, 220, 221, 222, 225, 226, 232]
        lte_bands = [31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 115]
        nr_bands = [301, 302, 303, 305, 307, 308, 312, 313, 314, 318, 320, 325, 326, 328, 329, 330, 334, 338, 339, 340, 341, 348, 350, 351, 353, 365, 366, 370, 371, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 386, 389, 390, 391, 392, 393, 394, 395, 557, 558, 560, 561]
        if 'org.ofono.RadioSettings' in self.ofono_interface_props:
            if 'AvailableTechnologies' in self.ofono_interface_props['org.ofono.RadioSettings']:
                ofono_techs = self.ofono_interface_props['org.ofono.RadioSettings']['AvailableTechnologies'].value
                if 'gsm' in ofono_techs:
                    supported_bands.extend(gsm_bands)
                if 'umts' in ofono_techs:
                    supported_bands.extend(umts_bands)
                if 'lte' in ofono_techs:
                    supported_bands.extend(lte_bands)
                if 'nr' in ofono_techs:
                    supported_bands.extend(nr_bands)

        self.props['current-bands'] = Variant('au', supported_bands)

        for prop in self.props:
            if self.props[prop].value != old_props[prop].value:
                self.emit_properties_changed({prop: self.props[prop].value})

    def check_signal_strength(self):
        ofono2mm_print("Checking network registration", self.verbose)

        try:
            if 'org.ofono.NetworkRegistration' in self.ofono_interface_props:
                if 'Strength' in self.ofono_interface_props['org.ofono.NetworkRegistration']:
                    strength = self.ofono_interface_props['org.ofono.NetworkRegistration']['Strength'].value
                    ofono2mm_print(f"Signal strength is available: {strength}", self.verbose)
                    return strength
                else:
                    return 0
            else:
                return 0
        except Exception as e:
            ofono2mm_print(f"Failed to get signal strength: {e}", self.verbose)
            return 0

    @method()
    async def Connect(self, properties: 'a{sv}') -> 'o':
        ofono2mm_print(f"Connecting with properties {properties}", self.verbose)

        self.set_props()

        try:
            await self.network_manager_set_apn()
        except Exception as e:
            ofono2mm_print(f"Failed to set Network Manager APN: {e}", self.verbose)

        for b in self.mm_modem.bearers:
            if self.mm_modem.bearers[b].props['Properties'].value['apn'] == properties['apn']:
                await self.mm_modem.bearers[b].add_auth_ofono(properties['username'].value if 'username' in properties else '',
                                                                properties['password'].value if 'password' in properties else '')
                self.mm_modem.bearers[b].props['Properties'] = Variant('a{sv}', properties)
                if self.mm_modem.bearers[b].active_connect == 0:
                    self.mm_modem.bearers[b].active_connect += 1
                    await self.mm_modem.bearers[b].doConnect()

                    if read_setting('data').strip() != 'True':
                        ofono2mm_print("Saving context toggle state during connection of existing bearers", self.verbose)
                        save_setting('data', 'True')

                    return b

        try:
            bearer = await self.mm_modem.doCreateBearer(properties)
            if self.mm_modem.bearers[bearer].active_connect == 0:
                self.mm_modem.bearers[bearer].active_connect += 1
                await self.mm_modem.bearers[bearer].doConnect()
            else:
                # 0 is always available so just fallback to that, whatever
                bearer = '/org/freedesktop/ModemManager/Bearer/0'
        except Exception:
            bearer = '/org/freedesktop/ModemManager/Bearer/0'

        if read_setting('data').strip() != 'True':
            ofono2mm_print("Saving context toggle state on bearer creation", self.verbose)
            save_setting('data', 'True')

        return bearer

    @method()
    async def Disconnect(self, path: 'o'):
        ofono2mm_print(f"Disconnecting object path {path}", self.verbose)

        if read_setting('data').strip() != 'False':
            ofono2mm_print("Saving context toggle state", self.verbose)
            save_setting('data', 'False')

        if path == '/':
            for b in self.mm_modem.bearers:
                try:
                    await self.mm_modem.bearers[b].doDisconnect()
                except Exception as e:
                    ofono2mm_print(f"Failed to disconnect bearer {path}: {e}", self.verbose)
        if path in self.mm_modem.bearers:
            try:
                await self.mm_modem.bearers[path].doDisconnect()
            except Exception as e:
                ofono2mm_print(f"Failed to disconnect bearer {path}: {e}", self.verbose)

    @method()
    async def GetStatus(self) -> 'a{sv}':
        ofono2mm_print("Returning status", self.verbose)
        self.set_props()
        return self.props

    async def network_manager_set_apn(self):
        ofono2mm_print("Generating Network Manager connection", self.verbose)

        DBusGMainLoop(set_as_default=True)

        current_timestamp = int(time())

        try:
            sim_id = self.ofono_interface_props['org.ofono.SimManager']['CardIdentifier'].value
        except Exception:
            return False

        try:
            carrier_name = self.ofono_interface_props['org.ofono.NetworkRegistration']['Name'].value
        except Exception:
            return False

        try:
            contexts = await self.ofono_interfaces['org.ofono.ConnectionManager'].call_get_contexts()
            for ctx in contexts:
                ctx_type = ctx[1].get('Type', Variant('s', '')).value
                if ctx_type.lower() == "internet":
                    apn = ctx[1].get('AccessPointName', Variant('s', '')).value
                    username = ctx[1].get('Username', Variant('s', '')).value
                    password = ctx[1].get('Password', Variant('s', '')).value
        except Exception:
            return False

        connection_settings = {
            'connection': {
                'id': f'{carrier_name}',
                'uuid': str(uuid4()),
                'type': 'gsm',
                'timestamp': current_timestamp
            },
            'gsm': {
                'apn': f'{apn}',
                'home-only': True,
                'sim-id': f'{sim_id}'
            },
            'ipv4': {
                'dns-priority': 120,
                'method': 'auto',
                'route-metric': 1050
            },
            'ipv6': {
                'method': 'auto'
            }
        }

        if username and password:
            connection_settings['gsm']['username'] = f'{username}'
            connection_settings['gsm']['password'] = f'{password}'

        try:
            if self.network_manager_connection_exists(f'{apn}') == False:
                conn = NetworkManager.Settings.AddConnection(connection_settings)
                ofono2mm_print(f"Connection '{conn.GetSettings()['connection']['id']}' created successfully with timestamp {current_timestamp}.", self.verbose)
            return True
        except Exception:
            return False

    def network_manager_connection_exists(self, target_apn):
        ofono2mm_print(f"Checking if Network Manager connection exists for {target_apn}", self.verbose)

        found = False

        DBusGMainLoop(set_as_default=True)

        # for some reason NetworkManager.NetworkManager.Reload doesn't work correctly
        bus = SystemBus()
        nm = bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager/Settings")

        nm_settings = Interface(nm, "org.freedesktop.NetworkManager.Settings")
        nm_settings.ReloadConnections()

        connections = NetworkManager.Settings.ListConnections()

        for conn in connections:
            conn_settings = conn.GetSettings()
            if 'gsm' in conn_settings:
                apn = conn_settings['gsm']['apn']
                if apn == target_apn:
                    found = True

        ofono2mm_print(f"Connection for APN {target_apn} exists: {found}", self.verbose)
        if found:
            return True
        else:
            return False

    def ofono_changed(self, name, varval):
        self.ofono_props[name] = varval
        self.set_props()

    def ofono_interface_changed(self, iface):
        def ch(name, varval):
            if iface in self.ofono_interface_props:
                self.ofono_interface_props[iface][name] = varval

            self.set_props()

        return ch
