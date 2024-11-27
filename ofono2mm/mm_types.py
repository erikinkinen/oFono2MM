
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
