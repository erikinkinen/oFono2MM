from dbus_next.service import (ServiceInterface,
                               method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant, DBusError, BusType

from ofono2mm.mm_modem_3gpp import MMModem3gppInterface
from ofono2mm.mm_modem_3gpp_ussd import MMModem3gppUssdInterface
from ofono2mm.mm_modem_3gpp_profile_manager import MMModem3gppProfileManagerInterface
from ofono2mm.mm_modem_messaging import MMModemMessagingInterface
from ofono2mm.mm_modem_simple import MMModemSimpleInterface
from ofono2mm.mm_modem_firmware import MMModemFirmwareInterface
from ofono2mm.mm_modem_cdma import MMModemCDMAInterface
from ofono2mm.mm_modem_time import MMModemTimeInterface
from ofono2mm.mm_modem_sar import MMModemSarInterface
from ofono2mm.mm_modem_oma import MMModemOmaInterface
from ofono2mm.mm_modem_signal import MMModemSignalInterface
from ofono2mm.mm_modem_location import MMModemLocationInterface
from ofono2mm.mm_sim import MMSimInterface
from ofono2mm.mm_bearer import MMBearerInterface
from ofono2mm.mm_modem_voice import MMModemVoiceInterface
from ofono2mm.logger import Logger

import asyncio

bearer_i = 0

class ModemManagerState:
    FAILED        = -1
    UNKNOWN       = 0
    INITIALIZING  = 1
    LOCKED        = 2
    DISABLED      = 3
    DISABLING     = 4
    ENABLING      = 5
    ENABLED       = 6
    SEARCHING     = 7
    REGISTERED    = 8
    DISCONNECTING = 9
    CONNECTING    = 10
    CONNECTED     = 11

    def to_string(value):
        match value:
            case ModemManagerState.FAILED:
                return "Failed"
            case ModemManagerState.UNKNOWN:
                return "Unknown"
            case ModemManagerState.INITIALIZING:
                return "Initializing"
            case ModemManagerState.LOCKED:
                return "Locked"
            case ModemManagerState.DISABLED:
                return "Disabled"
            case ModemManagerState.DISABLING:
                return "Disabling"
            case ModemManagerState.ENABLING:
                return "Enabling"
            case ModemManagerState.ENABLED:
                return "Enabled"
            case ModemManagerState.SEARCHING:
                return "Searching"
            case ModemManagerState.REGISTERED:
                return "Registered"
            case ModemManagerState.DISCONNECTING:
                return "Disconnecting"
            case ModemManagerState.CONNECTING:
                return "Connecting"
            case _:
                return "Connected"

class ModemManagerStateFailedReason:
    NONE                  = 0
    UNKNOWN               = 1
    SIM_MISSING           = 2
    SIM_ERROR             = 3
    UNKNOWN_CAPABILITIES  = 4
    ESIM_WITHOUT_PROFILES = 5

class ModemManagerLock:
    UNKNOWN        = 0
    NONE           = 1
    SIM_PIN        = 2
    SIM_PIN2       = 3
    SIM_PUK        = 4
    SIM_PUK2       = 5
    PH_SP_PIN      = 6
    PH_SP_PUK      = 7
    PH_NET_PIN     = 8
    PH_NET_PUK     = 9
    PH_SIM_PIN     = 10
    PH_CORP_PIN    = 11
    PH_CORP_PUK    = 12
    PH_FSIM_PIN    = 13
    PH_FSIM_PUK    = 14
    PH_NETSUB_PIN  = 15
    PH_NETSUB_PUK  = 16

OFONO_RETRIES_LOCK = {
    'pin' : ModemManagerLock.SIM_PIN,
    'pin2': ModemManagerLock.SIM_PIN2,
    'puk': ModemManagerLock.SIM_PUK,
    'puk2': ModemManagerLock.SIM_PUK2,
    'service': ModemManagerLock.PH_SP_PIN,
    'servicepuk': ModemManagerLock.PH_SP_PUK,
    'network': ModemManagerLock.PH_NET_PIN,
    'networkpuk': ModemManagerLock.PH_NET_PUK,
    'corp': ModemManagerLock.PH_CORP_PIN,
    'corppuk': ModemManagerLock.PH_CORP_PUK,
    'netsub': ModemManagerLock.PH_NETSUB_PIN,
    'netsubpuk': ModemManagerLock.PH_NETSUB_PUK,
}

class ModemManagerAccessTechnology:
    UNKNOWN     = 0
    POTS        = 1 << 0
    GSM         = 1 << 1
    GSM_COMPACT = 1 << 2
    GPRS        = 1 << 3
    EDGE        = 1 << 4
    UMTS        = 1 << 5
    HSDPA       = 1 << 6
    HSUPA       = 1 << 7
    HSPA        = 1 << 8
    HSPA_PLUS   = 1 << 9
    _1XRTT      = 1 << 10
    EVDO0       = 1 << 11
    EVDOA       = 1 << 12
    EVDOB       = 1 << 13
    LTE         = 1 << 14
    _5GNR       = 1 << 15
    LTE_CAT_M   = 1 << 16
    LTE_NB_IOT  = 1 << 17
    ANY         = 0xFFFFFFFF

class ModemManagerCellType:
    UNKNOWN = 0
    CDMA    = 1
    GSM     = 2
    UMTS    = 3
    TDSCDMA = 4
    LTE     = 5
    _5GNR   = 6

OFONO_TECHNOLOGIES = {
    "nr": ModemManagerAccessTechnology._5GNR,
    "lte": ModemManagerAccessTechnology.LTE,
    "hspa": ModemManagerAccessTechnology.HSPA,
    "hsupa": ModemManagerAccessTechnology.HSUPA,
    "hsdpa": ModemManagerAccessTechnology.HSDPA,
    "umts": ModemManagerAccessTechnology.UMTS,
    "edge": ModemManagerAccessTechnology.GSM,
    "gprs": ModemManagerAccessTechnology.GSM,
    "gsm": ModemManagerAccessTechnology.GSM
}

OFONO_CELL_TYPES = {
    "nr": ModemManagerCellType._5GNR,
    "lte": ModemManagerCellType.LTE,
    "hspa": ModemManagerCellType.UMTS,
    "hsupa": ModemManagerCellType.UMTS,
    "hsdpa": ModemManagerCellType.UMTS,
    "umts": ModemManagerCellType.UMTS,
    "edge": ModemManagerCellType.GSM,
    "gprs": ModemManagerCellType.GSM,
    "gsm": ModemManagerCellType.GSM
}

class ModemManagerMode:
    NONE = 0
    CS   = 1 << 0
    _2G  = 1 << 1
    _3G  = 1 << 2
    _4G  = 1 << 3
    _5G  = 1 << 4
    ANY  = 0xFFFFFFFF

class ModemManagerCapability:
    NONE         = 0
    POTS         = 1 << 0
    CDMA_EVDO    = 1 << 1
    GSM_UMTS     = 1 << 2
    LTE          = 1 << 3
    IRIDIUM      = 1 << 5
    _5GNR        = 1 << 6
    TDS          = 1 << 7
    ANY          = 0xFFFFFFFF

OFONO_MODES = {
    "gsm": ModemManagerMode._2G,
    "umts": ModemManagerMode._3G,
    "lte": ModemManagerMode._4G,
    "nr": ModemManagerMode._5G
}

OFONO_CAPS = {
    "gsm": ModemManagerCapability.GSM_UMTS,
    "umts": ModemManagerCapability.GSM_UMTS,
    "lte": ModemManagerCapability.LTE,
    "nr": ModemManagerCapability._5GNR
}

MM_MODES = {
    ModemManagerMode._2G | ModemManagerMode._3G | ModemManagerMode._4G | ModemManagerMode._5G: [
        [ModemManagerMode._2G | ModemManagerMode._3G | ModemManagerMode._4G | ModemManagerMode._5G, ModemManagerMode._5G],
        [ModemManagerMode._2G | ModemManagerMode._3G | ModemManagerMode._4G, ModemManagerMode._4G],
        [ModemManagerMode._2G | ModemManagerMode._3G, ModemManagerMode._3G],
        [ModemManagerMode._2G, ModemManagerMode.ANY]
    ],
    ModemManagerMode._3G | ModemManagerMode._4G | ModemManagerMode._5G: [
        [ModemManagerMode._3G | ModemManagerMode._4G | ModemManagerMode._5G, ModemManagerMode.ANY]
    ],
    ModemManagerMode._2G | ModemManagerMode._4G | ModemManagerMode._5G: [
        [ModemManagerMode._2G | ModemManagerMode._4G | ModemManagerMode._5G, ModemManagerMode.ANY]
    ],
    ModemManagerMode._4G | ModemManagerMode._5G: [
        [ModemManagerMode._4G | ModemManagerMode._5G, ModemManagerMode.ANY]
    ],
    ModemManagerMode._3G | ModemManagerMode._5G: [
        [ModemManagerMode._3G | ModemManagerMode._5G, ModemManagerMode.ANY]
    ],
    ModemManagerMode._2G | ModemManagerMode._5G: [
        [ModemManagerMode._2G | ModemManagerMode._5G, ModemManagerMode.ANY]
    ],
    ModemManagerMode._5G: [
        [ModemManagerMode._5G, ModemManagerMode.ANY]
    ],
    ModemManagerMode._2G | ModemManagerMode._3G | ModemManagerMode._4G: [
        [ModemManagerMode._2G | ModemManagerMode._3G | ModemManagerMode._4G, ModemManagerMode._4G],
        [ModemManagerMode._2G | ModemManagerMode._3G, ModemManagerMode._3G],
        [ModemManagerMode._2G, ModemManagerMode.ANY]
    ],
    ModemManagerMode._3G | ModemManagerMode._4G: [
        [ModemManagerMode._3G | ModemManagerMode._4G, ModemManagerMode._4G],
        [ModemManagerMode._3G, ModemManagerMode.ANY]
    ],
    ModemManagerMode._2G | ModemManagerMode._4G: [
        [ModemManagerMode._2G | ModemManagerMode._4G, ModemManagerMode._4G],
        [ModemManagerMode._2G, ModemManagerMode.ANY]
    ],
    ModemManagerMode._3G: [
        [ModemManagerMode._3G, ModemManagerMode.ANY]
    ],
    ModemManagerMode._2G: [
        [ModemManagerMode._2G, ModemManagerMode.ANY]
    ],
    ModemManagerMode.NONE: []
}

class MMModemInterface(ServiceInterface):
    def __init__(self, loop, index, bus, ofono_client, modem_name):
        super().__init__('org.freedesktop.ModemManager1.Modem')
        self.loop = loop
        self.index = index
        self.bus = bus
        self.ofono_client = ofono_client
        self.ofono_proxy = self.ofono_client["ofono_modem"][modem_name]
        self.modem_name = modem_name
        self.ofono_modem = self.ofono_proxy['org.ofono.Modem']
        self.ofono_props = {}
        self.ofono_interfaces = {}
        self.ofono_interface_props = {}
        self.mm_cell_type = ModemManagerCellType.UNKNOWN
        self.mm_modem3gpp_interface = False
        self.mm_modem_messaging_interface = False
        self.mm_sim_interface = False
        self.sim = Variant('o', f'/org/freedesktop/ModemManager/SIM/{self.index}')
        self.bearers = {}
        self.props = {
            'Sim': Variant('o', '/'),
            'SimSlots': Variant('ao', [f'/org/freedesktop/ModemManager/SIM/{self.index}']),
            'PrimarySimSlot': Variant('u', 0),
            'Bearers': Variant('ao', []),
            'SupportedCapabilities': Variant('au', [ModemManagerCapability.NONE]),
            'CurrentCapabilities': Variant('u', ModemManagerCapability.NONE),
            'MaxBearers': Variant('u', 4),
            'MaxActiveBearers': Variant('u', 2),
            'MaxActiveMultiplexedBearers': Variant('u', 2),
            'Manufacturer': Variant('s', 'ofono'),
            'Model': Variant('s', ''),
            'Revision': Variant('s', '10000'),
            'CarrierConfiguration': Variant('s', ''),
            'CarrierConfigurationRevision': Variant('s', '0'),
            'HardwareRevision': Variant('s', '1000'),
            'DeviceIdentifier': Variant('s', self.modem_name),
            'Device': Variant('s', self.modem_name),
            'Physdev': Variant('s', '/dev/binder'),
            'Drivers': Variant('as', ['binder']),
            'Plugin': Variant('s', 'ofono2mm'),
            'PrimaryPort': Variant('s', self.modem_name),
            'Ports': Variant('a(su)', [[self.modem_name, 0]]), # on runtime unknown MM_MODEM_PORT_TYPE_UNKNOWN
            'EquipmentIdentifier': Variant('s', ''),
            'UnlockRequired': Variant('u', ModemManagerLock.UNKNOWN),
            'UnlockRetries': Variant('a{uu}', {}),
            'State': Variant('i', ModemManagerState.UNKNOWN),
            'StateFailedReason': Variant('u', ModemManagerStateFailedReason.UNKNOWN),
            'AccessTechnologies': Variant('u', ModemManagerAccessTechnology.UNKNOWN),
            'SignalQuality': Variant('(ub)', [0, False]),
            'OwnNumbers': Variant('as', []),
            'PowerState': Variant('u', 3), # on runtime power on MM_MODEM_POWER_STATE_ON
            'SupportedModes': Variant('a(uu)', [[ModemManagerMode.NONE, ModemManagerMode.NONE]]),
            'CurrentModes': Variant('(uu)', [ModemManagerMode.NONE, ModemManagerMode.NONE]),
            'SupportedBands': Variant('au', []),
            'CurrentBands': Variant('au', []),
            'SupportedIpFamilies': Variant('u', 3) # hardcoded value ipv4 and ipv6 MM_BEARER_IP_FAMILY_IPV4V6
        }

    async def init_ofono_interfaces(self):
        for iface in self.ofono_props['Interfaces'].value:
            await self.add_ofono_interface(iface)

        await self.check_ofono_contexts()

    async def add_ofono_interface(self, iface):
        self.ofono_interfaces.update({
            iface: self.ofono_proxy[iface]
        })

        try:
            self.ofono_interface_props.update({
                iface: await self.ofono_interfaces[iface].call_get_properties()
            })

            if self.mm_modem3gpp_interface:
                self.mm_modem3gpp_interface.ofono_interface_props = self.ofono_interface_props.copy()
            if self.mm_sim_interface:
                self.mm_sim_interface.ofono_interface_props = self.ofono_interface_props.copy()

            self.ofono_interfaces[iface].on_property_changed(self.ofono_interface_changed(iface))
        except DBusError:
            self.ofono_interface_props.update({
                iface: {}
            })

            if self.mm_modem3gpp_interface:
                self.mm_modem3gpp_interface.ofono_interface_props = self.ofono_interface_props.copy()
            if self.mm_sim_interface:
                self.mm_sim_interface.ofono_interface_props = self.ofono_interface_props.copy()

            self.ofono_interfaces[iface].on_property_changed(self.ofono_interface_changed(iface))
        except AttributeError:
            pass

        if self.mm_modem3gpp_interface:
            self.mm_modem3gpp_interface.set_props()
        if self.mm_sim_interface:
            self.mm_sim_interface.set_props()
        if self.mm_modem_messaging_interface and iface == "org.ofono.MessageManager":
            self.mm_modem_messaging_interface.set_props()
            await self.mm_modem_messaging_interface.init_messages()
        if iface == "org.ofono.ConnectionManager":
            await self.check_ofono_contexts()

    async def remove_ofono_interface(self, iface):
        if iface in self.ofono_interfaces:
            self.ofono_interfaces.pop(iface)
        if iface in self.ofono_interface_props:
            self.ofono_interface_props.pop(iface)

        self.set_props()

        if self.mm_modem3gpp_interface:
            self.mm_modem3gpp_interface.ofono_interface_props = self.ofono_interface_props.copy()
            self.mm_modem3gpp_interface.set_props()
        if self.mm_sim_interface:
            self.mm_sim_interface.ofono_interface_props = self.ofono_interface_props.copy()
            self.mm_sim_interface.set_props()

    async def init_mm_sim_interface(self):
        self.mm_sim_interface = MMSimInterface(self.index, self.bus, self.ofono_client, self.modem_name, self.ofono_modem, self.ofono_props, self.ofono_interfaces, self.ofono_interface_props)
        self.bus.export(f'/org/freedesktop/ModemManager/SIM/{self.index}', self.mm_sim_interface)
        self.mm_sim_interface.set_props()

    async def init_mm_3gpp_interface(self):
        self.mm_modem3gpp_interface = MMModem3gppInterface(self.index, self.bus, self.ofono_client, self.modem_name, self.ofono_modem, self.ofono_props, self.ofono_interfaces, self.ofono_interface_props)
        self.bus.export(f'/org/freedesktop/ModemManager1/Modem/{self.index}', self.mm_modem3gpp_interface)
        self.mm_modem3gpp_interface.set_props()

    async def init_mm_3gpp_ussd_interface(self):
        self.mm_modem3gpp_ussd_interface = MMModem3gppUssdInterface(self.index, self.bus, self.ofono_client, self.modem_name, self.ofono_modem, self.ofono_props, self.ofono_interfaces, self.ofono_interface_props)
        self.bus.export(f'/org/freedesktop/ModemManager1/Modem/{self.index}', self.mm_modem3gpp_ussd_interface)

    async def init_mm_3gpp_profile_manager_interface(self):
        self.mm_modem3gpp_profile_manager_interface = MMModem3gppProfileManagerInterface(self.index, self.bus, self.ofono_client, self.modem_name, self.ofono_modem, self.ofono_props, self.ofono_interfaces, self.ofono_interface_props)
        self.bus.export(f'/org/freedesktop/ModemManager1/Modem/{self.index}', self.mm_modem3gpp_profile_manager_interface)

    async def init_mm_simple_interface(self):
        self.mm_modem_simple_interface = MMModemSimpleInterface(self, self.ofono_interfaces, self.ofono_interface_props)
        self.bus.export(f'/org/freedesktop/ModemManager1/Modem/{self.index}', self.mm_modem_simple_interface)

    async def init_mm_firmware_interface(self):
        self.mm_modem_firmware_interface = MMModemFirmwareInterface(self)
        self.bus.export(f'/org/freedesktop/ModemManager1/Modem/{self.index}', self.mm_modem_firmware_interface)
        self.mm_modem_firmware_interface.set_props()

    async def init_mm_time_interface(self):
        self.mm_modem_time_interface = MMModemTimeInterface(self.index, self.bus, self.ofono_client, self.modem_name, self.ofono_modem, self.ofono_props, self.ofono_interfaces, self.ofono_interface_props)
        self.bus.export(f'/org/freedesktop/ModemManager1/Modem/{self.index}', self.mm_modem_time_interface)

        if 'org.ofono.NetworkTime' in self.ofono_interfaces:
            await self.mm_modem_time_interface.init_time()

    async def init_mm_cdma_interface(self):
        self.mm_modem_cdma_interface = MMModemCDMAInterface(self)
        self.bus.export(f'/org/freedesktop/ModemManager1/Modem/{self.index}', self.mm_modem_cdma_interface)

    async def init_mm_sar_interface(self):
        self.mm_modem_sar_interface = MMModemSarInterface(self)
        self.bus.export(f'/org/freedesktop/ModemManager1/Modem/{self.index}', self.mm_modem_sar_interface)

    async def init_mm_oma_interface(self):
        self.mm_modem_oma_interface = MMModemOmaInterface(self)
        self.bus.export(f'/org/freedesktop/ModemManager1/Modem/{self.index}', self.mm_modem_oma_interface)

    async def init_mm_signal_interface(self):
        self.mm_modem_signal_interface = MMModemSignalInterface(self, self.ofono_interfaces, self.ofono_interface_props)
        self.bus.export(f'/org/freedesktop/ModemManager1/Modem/{self.index}', self.mm_modem_signal_interface)

    async def init_mm_location_interface(self):
        self.mm_modem_location_interface = MMModemLocationInterface(self)
        self.bus.export(f'/org/freedesktop/ModemManager1/Modem/{self.index}', self.mm_modem_location_interface)

    async def init_mm_voice_interface(self):
        self.mm_modem_voice_interface = MMModemVoiceInterface(self.index, self.bus, self.ofono_client, self.modem_name, self.ofono_modem, self.ofono_props, self.ofono_interfaces, self.ofono_interface_props)
        self.bus.export(f'/org/freedesktop/ModemManager1/Modem/{self.index}', self.mm_modem_voice_interface)

        if 'org.ofono.VoiceCallManager' in self.ofono_interfaces:
            self.mm_modem_voice_interface.set_props()
            await self.mm_modem_voice_interface.init_calls()

    async def init_mm_messaging_interface(self):
        self.mm_modem_messaging_interface = MMModemMessagingInterface(self.index, self.bus, self.ofono_client, self.modem_name, self.ofono_modem, self.ofono_props, self.ofono_interfaces, self.ofono_interface_props)
        self.bus.export(f'/org/freedesktop/ModemManager1/Modem/{self.index}', self.mm_modem_messaging_interface)

        if 'org.ofono.MessageManager' in self.ofono_interfaces:
            self.mm_modem_messaging_interface.set_props()
            await self.mm_modem_messaging_interface.init_messages()

    async def check_ofono_contexts(self):
        global bearer_i
        if not 'org.ofono.ConnectionManager' in self.ofono_interfaces:
            return

        contexts = await self.ofono_interfaces['org.ofono.ConnectionManager'].call_get_contexts();
        old_bearer_list = self.props['Bearers'].value
        for ctx in contexts:
            if ctx[1]['Type'].value == "internet":
                mm_bearer_interface = MMBearerInterface(self.index, self.bus, self.ofono_client, self.modem_name, self.ofono_modem, self.ofono_props, self.ofono_interfaces, self.ofono_interface_props, self)

                ip_method = 0
                if 'Method' in ctx[1]['Settings'].value:
                    if ctx[1]['Settings'].value['Method'].value == "static":
                        ip_method = 2
                    if ctx[1]['Settings'].value['Method'].value == "dhcp":
                        ip_method = 3

                ip_address = ''
                if 'Address' in ctx[1]['Settings'].value:
                    ip_address = ctx[1]['Settings'].value['Address'].value

                ip_dns = []
                if 'DomainNameServers' in ctx[1]['Settings'].value:
                    ip_dns = ctx[1]['Settings'].value['DomainNameServers'].value

                ip_gateway = ''
                if 'Gateway' in ctx[1]['Settings'].value:
                    ip_gateway = ctx[1]['Settings'].value['Gateway'].value

                mm_bearer_interface.props.update({
                    "Interface": ctx[1]['Settings'].value.get("Interface", Variant('s', '')),
                    "Connected": ctx[1]['Active'],
                    "Ip4Config": Variant('a{sv}', {
                        "method": Variant('u', ip_method),
                        "dns1": Variant('s', ip_dns[0] if len(ip_dns) > 0 else ''),
                        "dns2": Variant('s', ip_dns[1] if len(ip_dns) > 1 else ''),
                        "dns3": Variant('s', ip_dns[2] if len(ip_dns) > 2 else ''),
                        "gateway": Variant('s', ip_gateway)
                    }),
                    "Properties": Variant('a{sv}', {
                        "apn": ctx[1]['AccessPointName']
                    })
                })

                if 'Interface' in ctx[1]['Settings'].value:
                    self.props['Ports'].value.append([ctx[1]['Settings'].value['Interface'].value, 2]) # port type AT MM_MODEM_PORT_TYPE_AT
                    self.emit_properties_changed({'Ports': self.props['Ports'].value})

                ofono_ctx_interface = self.ofono_client["ofono_context"][ctx[0]]["org.ofono.ConnectionContext"]
                ofono_ctx_interface.on_property_changed(mm_bearer_interface.ofono_context_changed)
                ofono_ctx_interface.on_property_changed(self.ofono_context_changed)
                mm_bearer_interface.ofono_ctx = ctx[0]
                self.bus.export(f'/org/freedesktop/ModemManager/Bearer/{bearer_i}', mm_bearer_interface)
                self.props['Bearers'].value.append(f'/org/freedesktop/ModemManager/Bearer/{bearer_i}')
                self.bearers[f'/org/freedesktop/ModemManager/Bearer/{bearer_i}'] = mm_bearer_interface
                bearer_i += 1

        if self.props['Bearers'].value == old_bearer_list:
            self.emit_properties_changed({'Bearers': self.props['Bearers'].value})

        self.ofono_interfaces['org.ofono.ConnectionManager'].on_context_added(self.ofono_context_added)

    def ofono_context_added(self, path, properties):
        global bearer_i
        if properties['Type'] == "internet":
            mm_bearer_interface = MMBearerInterface(self.index, self.bus, self.ofono_client, self.modem_name, self.ofono_modem, self.ofono_props, self.ofono_interfaces, self.ofono_interface_props, self)

            ip_method = 0
            if 'Method' in properties['Settings'].value:
                if properties['Settings'].value['Method'].value == "static":
                    ip_method = 2
                elif properties['Settings'].value['Method'].value == "dhcp":
                    ip_method = 3

            ip_address = ''
            if 'Address' in properties['Settings'].value:
                ip_address = properties['Settings'].value['Address'].value

            ip_dns = []
            if 'DomainNameServers' in properties['Settings'].value:
                ip_dns = properties['Settings'].value['DomainNameServers'].value

            ip_gateway = ''
            if 'Gateway' in properties['Settings'].value:
                ip_gateway = properties['Settings'].value['Gateway'].value

            mm_bearer_interface.props.update({
                "Interface": properties['Settings'].value['Interface'] if 'Interface' in properties['Settings'].value else Variant('s', ''),
                "Connected": properties['Active'],
                "Ip4Config": Variant('a{sv}', {
                    "method": Variant('u', ip_method),
                    "dns1": Variant('s', ip_dns[0] if len(ip_dns) > 0 else ''),
                    "dns2": Variant('s', ip_dns[1] if len(ip_dns) > 1 else ''),
                    "dns3": Variant('s', ip_dns[2] if len(ip_dns) > 2 else ''),
                    "gateway": Variant('s', ip_gateway)
                }),
                "Properties": Variant('a{sv}', {
                    "apn": properties['AccessPointName']
                })
            })

            if 'Interface' in properties['Settings'].value:
                self.props['Ports'].value.append([properties['Settings'].value['Interface'].value, 2])
                self.emit_properties_changed({'Ports': self.props['Ports'].value})

            ofono_ctx_interface = self.ofono_client["ofono_context"][path]['org.ofono.ConnectionContext']
            ofono_ctx_interface.on_property_changed(mm_bearer_interface.ofono_context_changed)
            ofono_ctx_interface.on_property_changed(self.ofono_context_changed)
            mm_bearer_interface.ofono_ctx = path
            self.bus.export(f'/org/freedesktop/ModemManager/Bearer/{bearer_i}', mm_bearer_interface)
            self.props['Bearers'].value.append(f'/org/freedesktop/ModemManager/Bearer/{bearer_i}')
            self.bearers[f'/org/freedesktop/ModemManager/Bearer/{bearer_i}'] = mm_bearer_interface
            bearer_i += 1
            self.emit_properties_changed({'Bearers': self.props['Bearers'].value})

    def set_modem_state(self):
        #############
        # MODEM OFF #
        #############
        if not self.ofono_props['Powered'].value or 'org.ofono.SimManager' not in self.ofono_interface_props:
            self.props['State'] = Variant('i', ModemManagerState.DISABLED)
            self.props['PowerState'] = Variant('i', 1) # power is off MM_MODEM_POWER_STATE_OFF
            return

        #############
        # MODEM ON  #
        #############
        self.props['PowerState'] = Variant('i', 3) # power is on MM_MODEM_POWER_STATE_ON

        if 'Present' not in self.ofono_interface_props['org.ofono.SimManager'] or \
                not self.ofono_interface_props['org.ofono.SimManager']['Present'].value:
            self.props['Sim'] = Variant('o', '/')
            self.props['State'] = Variant('i', ModemManagerState.FAILED)
            self.props['StateFailedReason'] = Variant('i', ModemManagerStateFailedReason.SIM_MISSING)
            return

        #################
        # SIM AVAILABLE #
        #################
        self.props['Sim'] = self.sim
        self.props['StateFailedReason'] = Variant('i', ModemManagerStateFailedReason.NONE)

        if self.ofono_interface_props['org.ofono.SimManager']['PinRequired'].value == 'none':
            self.props['UnlockRequired'] = Variant('u', ModemManagerLock.NONE)
        else:
            self.props['UnlockRequired'] = Variant('u', ModemManagerLock.SIM_PIN)
            self.props['State'] = Variant('i', ModemManagerState.LOCKED)
            return

        #################
        # SIM UNLOCKED  #
        #################
        if not self.ofono_props['Online'].value:
            self.props['State'] = Variant('i', ModemManagerState.DISABLED)
            return

        #################
        # MODEM ENABLED #
        #################
        if 'org.ofono.NetworkRegistration' not in self.ofono_interface_props:
            self.props['State'] = Variant('i', ModemManagerState.ENABLED)
            return

        if "Status" not in self.ofono_interface_props['org.ofono.NetworkRegistration']:
            self.props['State'] = Variant('i', ModemManagerState.ENABLED)
            return

        if self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == 'denied':
            self.props['State'] = Variant('i', ModemManagerState.ENABLED)
            return

        ###################
        # MODEM SEARCHING #
        ###################
        if self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value == 'searching':
            self.props['State'] = Variant('i', ModemManagerState.SEARCHING)
            return

        if 'Strength' in self.ofono_interface_props['org.ofono.NetworkRegistration']:
            self.props['SignalQuality'] = Variant('(ub)',
                                                  [self.ofono_interface_props['org.ofono.NetworkRegistration']
                                                                             ['Strength'].value,
                                                  True])
        ###################
        # MODEM CONNECTED #
        ###################
        for bearer in self.bearers.values():
            if bearer.Connected:
                self.props['State'] = Variant('i', ModemManagerState.CONNECTED)
                return

        ####################
        # MODEM REGISTERED #
        ####################
        if self.ofono_interface_props['org.ofono.NetworkRegistration']['Status'].value in ['registered', 'roaming']:
            self.props['State'] = Variant('i', ModemManagerState.REGISTERED)

    def set_sim_state(self):
        if 'org.ofono.SimManager' not in self.ofono_interface_props:
            return

        try:
            self.props['OwnNumbers'] = Variant('as', self.ofono_interface_props['org.ofono.SimManager']['SubscriberNumbers'].value)
        except:
            self.props['OwnNumbers'] = Variant('as', [])

        unlock_retries = {}
        for key in OFONO_RETRIES_LOCK.keys():
            try:
                value = self.ofono_interface_props['org.ofono.SimManager']['Retries'].value[key]
                unlock_retries[OFONO_RETRIES_LOCK[key]] = value
            except:
                pass
        self.props['UnlockRetries'] = Variant('a{uu}', unlock_retries)

    def set_access_technology(self):
        if 'org.ofono.NetworkRegistration' not in self.ofono_interface_props or \
                self.props['State'].value not in [ModemManagerState.REGISTERED,
                                                  ModemManagerState.CONNECTED]:
            self.props['AccessTechnologies'] = Variant('u', ModemManagerAccessTechnology.UNKNOWN)
            self.props['SignalQuality'] = Variant('(ub)', [0, False])
            return

        if "Technology" not in self.ofono_interface_props['org.ofono.NetworkRegistration']:
            self.props['AccessTechnologies'] = Variant('u', ModemManagerAccessTechnology.UNKNOWN)
            return

        ofono_tech = self.ofono_interface_props['org.ofono.NetworkRegistration']["Technology"].value
        Logger.debug ("AccessTechnologies: %s -> %s", ofono_tech, OFONO_TECHNOLOGIES[ofono_tech])
        self.props['AccessTechnologies'] = Variant('u', OFONO_TECHNOLOGIES[ofono_tech])
        self.mm_cell_type = OFONO_CELL_TYPES[ofono_tech]

    def set_capabilities(self):
        caps = 0
        try:
            for ofono_tech in self.ofono_interface_props['org.ofono.RadioSettings']['AvailableTechnologies'].value:
                caps |= OFONO_CAPS[ofono_tech]
        except KeyError:
            caps =  ModemManagerCapability.LTE
        except Exception as e:
            Logger.error("%s", e)

        Logger.debug ("SupportedCapabilities: %s", caps)
        self.props['CurrentCapabilities'] = Variant('u', caps)
        self.props['SupportedCapabilities'] = Variant('au', [caps])

    def set_supported_modes(self):
        try:
            ofono_pref =  self.ofono_interface_props['org.ofono.RadioSettings']['TechnologyPreference'].value
            mm_pref = OFONO_MODES[ofono_pref]
            mm_modes = 0;

            for ofono_tech in self.ofono_interface_props['org.ofono.RadioSettings']['AvailableTechnologies'].value:
                mm_modes |= OFONO_MODES[ofono_tech]
            Logger.debug ("SupportedModes: %s -> %s", mm_modes, MM_MODES[mm_modes])
            self.props['SupportedModes'] = Variant('a(uu)', MM_MODES[mm_modes])

            for mode in MM_MODES[mm_modes]:
                if mode[1] == mm_pref:
                    self.props['CurrentModes'] = Variant('(uu)', [mode[0], mm_pref])
                    break
                elif mode[1] & mm_pref != 0:
                    self.props['CurrentModes'] = Variant('(uu)', [mm_pref, ModemManagerMode.NONE])
                    break
            Logger.debug ("CurrentModes: %s", self.props['CurrentModes'].value)
        except KeyError:
            self.props['SupportedModes'] = Variant('a(uu)', [[ModemManagerMode.NONE, ModemManagerMode.NONE]])
            self.props['CurrentModes'] = Variant('(uu)', [ModemManagerMode.NONE, ModemManagerMode.NONE])
        except Exception as e:
            Logger.error("%s", e)

    def set_props(self):
        old_props = self.props.copy()
        old_state = self.props['State'].value

        self.set_modem_state()

        if old_state != self.props['State'].value:
            Logger.info("Modem state: %s", ModemManagerState.to_string(self.props['State'].value))

        self.set_sim_state()
        self.set_access_technology()
        self.set_capabilities()
        self.set_supported_modes()

        self.props['EquipmentIdentifier'] = Variant('s', self.ofono_props['Serial'].value if 'Serial' in self.ofono_props else '')
        self.props['HardwareRevision'] = Variant('s', self.ofono_props['Revision'].value if 'Revision' in self.ofono_props else '')
        self.props['Revision'] = Variant('s', self.ofono_props['SoftwareVersionNumber'].value if 'SoftwareVersionNumber' in self.ofono_props else '')
        self.props['Manufacturer'] = Variant('s', self.ofono_props['Manufacturer'].value if 'Manufacturer' in self.ofono_props else 'ofono')
        self.props['Model'] = Variant('s', self.ofono_props['Model'].value if 'Model' in self.ofono_props else 'binder')

        if old_state != self.props['State'].value:
            self.StateChanged(old_state, self.props['State'].value, 1)

        changed_props = {}
        for prop in self.props:
            if self.props[prop].value != old_props[prop].value:
                changed_props.update({ prop: self.props[prop].value })

        self.emit_properties_changed(changed_props)

    @method()
    async def Enable(self, enable: 'b'):
        if self.props['State'].value == -1:
            return

        old_state = self.props['State'].value
        self.props['State'] = Variant('i', 6 if enable else 3)
        self.StateChanged(old_state, self.props['State'].value, 1)
        self.emit_properties_changed({'State': self.props['State'].value})

        try:
            await self.ofono_modem.call_set_property('Online', Variant('b', enable))
        except Exception as e:
            pass

        self.set_props()

    @method()
    def ListBearers(self) -> 'ao':
        return self.props['Bearers'].value

    @method()
    async def CreateBearer(self, properties: 'a{sv}') -> 'o':
        try:
            return await self.doCreateBearer(properties)
        except Exception as e:
            pass

    async def doCreateBearer(self, properties):
        global bearer_i
        connection_manager_tries = 0

        # Prevents initial modem connection to fail by waiting for ofono
        while 'org.ofono.ConnectionManager' not in self.ofono_interfaces and connection_manager_tries < 10:
            await asyncio.sleep(1)
            connection_manager_tries += 1

        if 'org.ofono.ConnectionManager' not in self.ofono_interfaces:
            return

        Logger.debug(f"docreatebearer {bearer_i}")
        mm_bearer_interface = MMBearerInterface(self.index, self.bus, self.ofono_client, self.modem_name, self.ofono_modem, self.ofono_props, self.ofono_interfaces, self.ofono_interface_props, self)
        mm_bearer_interface.props.update({
            "Properties": Variant('a{sv}', properties)
        })

        # users would usually have to do
        # set-context-property 0 AccessPointName example.apn && activate-context 1
        # to activate the correct context for ofono2mm to use, lets do it on bearer creation to not need ofono scripts
        contexts = await self.ofono_interfaces['org.ofono.ConnectionManager'].call_get_contexts()
        self.context_names = []
        ctx_idx = 0
        chosen_apn = None
        chosen_ctx_path = None
        for ctx in contexts:
            name = ctx[1].get('Type', Variant('s', '')).value
            access_point_name = ctx[1].get('AccessPointName', Variant('s', '')).value
            if name.lower() == "internet":
                ctx_idx += 1
                if access_point_name:
                    self.context_names.append(access_point_name)
                    chosen_apn = access_point_name
                    chosen_ctx_path = ctx[0]

                    # print(chosen_ctx_path)

            if chosen_ctx_path:
                # print("set apn")
                chosen_ctx_interface = self.ofono_client["ofono_context"][chosen_ctx_path]['org.ofono.ConnectionContext']
                await chosen_ctx_interface.call_set_property("Active", Variant('b', False))
                await chosen_ctx_interface.call_set_property("AccessPointName", Variant('s', chosen_apn))
                await chosen_ctx_interface.call_set_property("Protocol", Variant('s', 'ip'))
                await chosen_ctx_interface.call_set_property("Active", Variant('b', True))

        ofono_ctx = await self.ofono_interfaces['org.ofono.ConnectionManager'].call_add_context("internet")
        ofono_ctx_interface = self.ofono_client["ofono_context"][ofono_ctx]['org.ofono.ConnectionContext']
        if 'apn' in properties:
            await ofono_ctx_interface.call_set_property("AccessPointName", properties['apn'])

        await mm_bearer_interface.add_auth_ofono(properties['username'].value if 'username' in properties else '',
                                                        properties['password'].value if 'password' in properties else '')

        await ofono_ctx_interface.call_set_property("Protocol", Variant('s', 'ip'))
        mm_bearer_interface.ofono_ctx = ofono_ctx
        ofono_ctx_interface.on_property_changed(self.ofono_context_changed)
        self.bus.export(f'/org/freedesktop/ModemManager/Bearer/{bearer_i}', mm_bearer_interface)
        self.props['Bearers'].value.append(f'/org/freedesktop/ModemManager/Bearer/{bearer_i}')
        self.bearers[f'/org/freedesktop/ModemManager/Bearer/{bearer_i}'] = mm_bearer_interface
        self.emit_properties_changed({'Bearers': self.props['Bearers'].value})
        bearer_i += 1

        return f'/org/freedesktop/ModemManager/Bearer/{bearer_i}'

    @method()
    async def DeleteBearer(self, path: 'o'):
        if path in self.props['Bearers'].value:
            self.props['Bearers'].value.remove(path)
            await self.ofono_interfaces['org.ofono.ConnectionManager'].call_remove_context(self.bearers[path].ofono_ctx)
            self.bearers.pop(path)
            self.bus.unexport(path)
            self.emit_properties_changed({'Bearers': self.props['Bearers'].value})

    @method()
    async def Reset(self):
        await self.ofono_modem.call_set_property('Powered', Variant('b', False))
        await self.ofono_modem.call_set_property('Powered', Variant('b', True))

        old_state = self.props['State'].value
        self.props['State'] = Variant('i', 6)  # 6 typically represents an enabled state
        self.StateChanged(old_state, self.props['State'].value, 1)
        self.emit_properties_changed({'State': self.props['State'].value})

        await self.ofono_modem.call_set_property('Online', Variant('b', True))

        self.set_props()

    @method()
    async def FactoryReset(self, code: 's'):
        # not quite a factory reset but better than nothing
        await self.ofono_modem.call_set_property('Powered', Variant('b', False))
        await self.ofono_modem.call_set_property('Powered', Variant('b', True))

        old_state = self.props['State'].value
        self.props['State'] = Variant('i', 6)  # 6 typically represents an enabled state
        self.StateChanged(old_state, self.props['State'].value, 1)
        self.emit_properties_changed({'State': self.props['State'].value})

        await self.ofono_modem.call_set_property('Online', Variant('b', True))

        self.set_props()

    @method()
    async def SetPowerState(self, state: 'u'):
        try:
            await self.ofono_modem.call_set_property('Powered', Variant('b', state > 1))
        except Exception as e:
            pass

        if state in [2, 3]:  # If state is 'on' or 'low'
            old_state = self.props['State'].value
            self.props['State'] = Variant('i', 6)  # 6 typically represents an enabled state
            self.StateChanged(old_state, self.props['State'].value, 1)
            self.emit_properties_changed({'State': self.props['State'].value})

            try:
                await self.ofono_modem.call_set_property('Online', Variant('b', enable))
            except Exception as e:
                pass

            self.set_props()

    @method()
    def SetCurrentCapabilities(self, capabilities: 'u'):
        self.props['CurrentCapabilities'] = Variant('u', capabilities)

    @method()
    async def SetCurrentModes(self, modes: '(uu)'):
        for supported_modes in self.props['SupportedModes'].value:
            if supported_modes[1] == modes[1]:
                value = list(filter(lambda x: OFONO_MODES[x] == modes[1], OFONO_MODES))[0]
                await self.ofono_interfaces['org.ofono.RadioSettings'].call_set_property('TechnologyPreference', Variant('s', value))
                return

        for supported_modes in self.props['SupportedModes'].value[::-1]:
            if supported_modes[0] & modes[0] != 0:
                value = list(filter(lambda x: OFONO_MODES[x] == modes[0], OFONO_MODES))[0]
                await self.ofono_interfaces['org.ofono.RadioSettings'].call_set_property('TechnologyPreference', Variant('s', value))
                return

        self.set_props()

    @method()
    def SetCurrentBands(self, bands: 'au'):
        self.props['CurrentBands'] = Variant('u', bands)

    @method()
    def SetPrimarySimSlot(self, sim_slot: 'u'):
        self.props['PrimarySimSlot'] = Variant('u', sim_slot)

    @method()
    def GetCellInfo(self) -> 'aa{sv}':
        cell_info = {
            "cell-type": Variant("u", self.mm_cell_type),
            "serving": Variant("b", self.props['State'].value == 8), # 8 should mean its registered correctly to a network
        }

        return [cell_info]

    @method()
    def Command(self, cmd: 's', timeout: 'u') -> 's':
        return ''

    @signal()
    def StateChanged(self, old, new, reason) -> 'iiu':
        return [old, new, reason]

    @dbus_property(access=PropertyAccess.READ)
    def Sim(self) -> 'o':
        return self.props['Sim'].value

    @dbus_property(access=PropertyAccess.READ)
    def SimSlots(self) -> 'ao':
        return self.props['SimSlots'].value

    @dbus_property(access=PropertyAccess.READ)
    def PrimarySimSlot(self) -> 'u':
        return self.props['PrimarySimSlot'].value

    @dbus_property(access=PropertyAccess.READ)
    def Bearers(self) -> 'ao':
        return self.props['Bearers'].value

    @dbus_property(access=PropertyAccess.READ)
    def SupportedCapabilities(self) -> 'au':
        return self.props['SupportedCapabilities'].value

    @dbus_property(access=PropertyAccess.READ)
    def CurrentCapabilities(self) -> 'u':
        return self.props['CurrentCapabilities'].value

    @dbus_property(access=PropertyAccess.READ)
    def MaxBearers(self) -> 'u':
        return self.props['MaxBearers'].value

    @dbus_property(access=PropertyAccess.READ)
    def MaxActiveBearers(self) -> 'u':
        return self.props['MaxActiveBearers'].value

    @dbus_property(access=PropertyAccess.READ)
    def MaxActiveMultiplexedBearers(self) -> 'u':
        return self.props['MaxActiveMultiplexedBearers'].value

    @dbus_property(access=PropertyAccess.READ)
    def Manufacturer(self) -> 's':
        return self.props['Manufacturer'].value

    @dbus_property(access=PropertyAccess.READ)
    def Model(self) -> 's':
        return self.props['Model'].value

    @dbus_property(access=PropertyAccess.READ)
    def Revision(self) -> 's':
        return self.props['Revision'].value

    @dbus_property(access=PropertyAccess.READ)
    def HardwareRevision(self) -> 's':
        return self.props['HardwareRevision'].value

    @dbus_property(access=PropertyAccess.READ)
    def DeviceIdentifier(self) -> 's':
        return self.props['DeviceIdentifier'].value

    @dbus_property(access=PropertyAccess.READ)
    def Device(self) -> 's':
        return self.props['Device'].value

    @dbus_property(access=PropertyAccess.READ)
    def Physdev(self) -> 's':
        return self.props['Physdev'].value

    @dbus_property(access=PropertyAccess.READ)
    def Drivers(self) -> 'as':
        return self.props['Drivers'].value

    @dbus_property(access=PropertyAccess.READ)
    def Plugin(self) -> 's':
        return self.props['Plugin'].value

    @dbus_property(access=PropertyAccess.READ)
    def PrimaryPort(self) -> 's':
        return self.props['PrimaryPort'].value

    @dbus_property(access=PropertyAccess.READ)
    def Ports(self) -> 'a(su)':
        return self.props['Ports'].value

    @dbus_property(access=PropertyAccess.READ)
    def EquipmentIdentifier(self) -> 's':
        return self.props['EquipmentIdentifier'].value

    @dbus_property(access=PropertyAccess.READ)
    def UnlockRequired(self) -> 'u':
        return self.props['UnlockRequired'].value

    @dbus_property(access=PropertyAccess.READ)
    def UnlockRetries(self) -> 'a{uu}':
        return self.props['UnlockRetries'].value

    @dbus_property(access=PropertyAccess.READ)
    def State(self) -> 'i':
        return self.props['State'].value

    @dbus_property(access=PropertyAccess.READ)
    def StateFailedReason(self) -> 'u':
        return self.props['StateFailedReason'].value

    @dbus_property(access=PropertyAccess.READ)
    def AccessTechnologies(self) -> 'u':
        return self.props['AccessTechnologies'].value

    @dbus_property(access=PropertyAccess.READ)
    def SignalQuality(self) -> '(ub)':
        return self.props['SignalQuality'].value

    @dbus_property(access=PropertyAccess.READ)
    def OwnNumbers(self) -> 'as':
        return self.props['OwnNumbers'].value

    @dbus_property(access=PropertyAccess.READ)
    def PowerState(self) -> 'u':
        return self.props['PowerState'].value

    @dbus_property(access=PropertyAccess.READ)
    def SupportedModes(self) -> 'a(uu)':
        return self.props['SupportedModes'].value

    @dbus_property(access=PropertyAccess.READ)
    def CurrentModes(self) -> '(uu)':
        return self.props['CurrentModes'].value

    @dbus_property(access=PropertyAccess.READ)
    def SupportedBands(self) -> 'au':
        return self.props['SupportedBands'].value

    @dbus_property(access=PropertyAccess.READ)
    def CurrentBands(self) -> 'au':
        return self.props['CurrentBands'].value

    @dbus_property(access=PropertyAccess.READ)
    def SupportedIpFamilies(self) -> 'u':
        return self.props['SupportedIpFamilies'].value

    def ofono_changed(self, name, varval):
        self.ofono_props[name] = varval
        if name == "Interfaces":
            for iface in varval.value:
                if not (iface in self.ofono_interfaces):
                    self.loop.create_task(self.add_ofono_interface(iface))
            for iface in self.ofono_interfaces:
                if not (iface in varval.value):
                    self.loop.create_task(self.remove_ofono_interface(iface))

        self.set_props()
        if self.mm_modem3gpp_interface:
            self.mm_modem3gpp_interface.ofono_changed(name, varval)
        if self.mm_sim_interface:
            self.mm_sim_interface.ofono_changed(name, varval)

    def ofono_interface_changed(self, iface):
        def ch(name, varval):
            if iface in self.ofono_interface_props:
                self.ofono_interface_props[iface][name] = varval
                self.set_props()
                if self.mm_modem3gpp_interface:
                    self.mm_modem3gpp_interface.ofono_interface_changed(iface)(name, varval)
                if self.mm_sim_interface:
                    self.mm_sim_interface.ofono_interface_changed(iface)(name, varval)

        return ch

    def ofono_context_changed(self, propname, value):
        if propname == "Active":
            self.set_props()
