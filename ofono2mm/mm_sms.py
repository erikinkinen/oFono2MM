from dbus_next.service import (ServiceInterface, method,
                               dbus_property)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

class MMSmsInterface(ServiceInterface):
    def __init__(self):
        super().__init__('org.freedesktop.ModemManager1.Sms')
        self.props = {
            "State": Variant('u', 0), # default value unknown MM_SMS_STATE_UNKNOWN
            "PduType": Variant('u', 0), # default value unknown MM_SMS_PDU_TYPE_UNKNOWN
            "Number": Variant('s', ''),
            "Text": Variant('s', ''),
            "SMSC": Variant('s', ''),
            "Validity": Variant('(uv)', [0, Variant('u', 0)]), # hardcoded value unknown MM_SMS_VALIDITY_TYPE_UNKNOWN
            "Class": Variant('i', -1), # -1 for 3GPP2/CDMA
            "TeleserviceId": Variant('u', 0), # hardcoded value MM_SMS_CDMA_SERVICE_CATEGORY_UNKNOWN
            "ServiceCategory": Variant('u', 0), # hardcoded value MM_SMS_CDMA_SERVICE_CATEGORY_UNKNOWN
            "DeliveryReportRequest": Variant('b', False),
            "MessageReference": Variant('u', 0),
            "Timestamp": Variant('s', ''),
            "DischargeTimestamp": Variant('s', ''),
            "DeliveryState": Variant('u', 0), # hardcoded value received MM_SMS_DELIVERY_STATE_COMPLETED_RECEIVED
            "Storage": Variant('u', 0) # hardcoded value unknown
        }

    @method()
    def Send(self):
        pass

    @method()
    def Store(self, storage: 'u'):
        pass

    @dbus_property(access=PropertyAccess.READ)
    def State(self) -> 'u':
        return self.props['State'].value

    @dbus_property(access=PropertyAccess.READ)
    def PduType(self) -> 'u':
        return self.props['PduType'].value

    @dbus_property(access=PropertyAccess.READ)
    def Number(self) -> 's':
        return self.props['Number'].value

    @dbus_property(access=PropertyAccess.READ)
    def Text(self) -> 's':
        return self.props['Text'].value

    @dbus_property(access=PropertyAccess.READ)
    def SMSC(self) -> 's':
        return self.props['SMSC'].value

    @dbus_property(access=PropertyAccess.READ)
    def Validity(self) -> '(uv)':
        return self.props['Validity'].value

    @dbus_property(access=PropertyAccess.READ)
    def Class(self) -> 'i':
        return self.props['Class'].value

    @dbus_property(access=PropertyAccess.READ)
    def TeleserviceId(self) -> 'u':
        return self.props['TeleserviceId'].value

    @dbus_property(access=PropertyAccess.READ)
    def ServiceCategory(self) -> 'u':
        return self.props['ServiceCategory'].value

    @dbus_property(access=PropertyAccess.READ)
    def DeliveryReportRequest(self) -> 'b':
        return self.props['DeliveryReportRequest'].value

    @dbus_property(access=PropertyAccess.READ)
    def MessageReference(self) -> 'u':
        return self.props['MessageReference'].value

    @dbus_property(access=PropertyAccess.READ)
    def Timestamp(self) -> 's':
        return self.props['Timestamp'].value

    @dbus_property(access=PropertyAccess.READ)
    def DischargeTimestamp(self) -> 's':
        return self.props['DischargeTimestamp'].value

    @dbus_property(access=PropertyAccess.READ)
    def DeliveryState(self) -> 'u':
        return self.props['DeliveryState'].value

    @dbus_property(access=PropertyAccess.READ)
    def Storage(self) -> 'u':
        return self.props['Storage'].value
