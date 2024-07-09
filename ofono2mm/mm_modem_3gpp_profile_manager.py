from dbus_next.service import (ServiceInterface,
                               method, dbus_property, signal)
from dbus_next.constants import PropertyAccess
from dbus_next import Variant

from ofono2mm.logging import ofono2mm_print

class MMModem3gppProfileManagerInterface(ServiceInterface):
    def __init__(self, ofono_client, modem_name, verbose=False):
        super().__init__('org.freedesktop.ModemManager1.Modem.Modem3gpp.ProfileManager')
        self.modem_name = modem_name
        ofono2mm_print("Initializing 3GPP profile manager interface", verbose)
        self.ofono_client = ofono_client
        self.verbose = verbose
        self.index_field = 'profile-id'
        self.props = {
            "apn": Variant('s', ''),
            "ip-type": Variant('u', 1),
            "apn-type": Variant('u', 2),
            "allowed-auth": Variant('u', 0),
            "user": Variant('s', ''),
            "password": Variant('s', ''),
            "roaming-allowance": Variant('u', 0),
            "access-type-preference": Variant('u', 0),
            "profile-id": Variant('i', -1),
            "profile-name": Variant('s', ''),
            "profile-enabled": Variant('b', True),
            "profile-source": Variant('u', 0),
        }

    @method()
    async def List(self) -> 'aa{sv}':
        ofono2mm_print("Returning list of profiles", self.verbose)
        properties = {}
        for key, value in self.props.items():
            if key != "roaming-allowance":
                properties[key] = value

        return [properties]

    @method()
    async def Set(self, requested_properties: 'a{sv}') -> 'a{sv}':
        ofono2mm_print(f"Setting profile with properties {requested_properties}", self.verbose)

        stored_properties = {}
        for key, value in requested_properties.items():
            if key in self.props:
                self.props[key] = value
                stored_properties[key] = value

        if stored_properties:
            self.Updated()

        if "roaming-allowance" in requested_properties:
            roaming_value_variant = requested_properties["roaming-allowance"]
            roaming_allowed = roaming_value_variant.value != 0
            ofono_interface = self.ofono_client["ofono_modem"][self.modem_name]['org.ofono.ConnectionManager']
            await ofono_interface.call_set_property("RoamingAllowed", Variant('b', roaming_allowed))

        return stored_properties

    @method()
    async def Delete(self, properties: 'a{sv}'):
        ofono2mm_print(f"Deleting profile with properties {properties}", self.verbose)

        for key in properties.items():
            if key in self.props:
                del self.props[key]

    @signal()
    def Updated(self):
        ofono2mm_print("Signal: Updated emitted", self.verbose)

    @dbus_property(access=PropertyAccess.READ)
    def IndexField(self) -> 's':
        return self.index_field
