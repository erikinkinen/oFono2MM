class ObjectProxy:
    def __init__(self, parent, getter, getter_args):
        self.parent = parent
        self.getter = getter
        self.getter_args = getter_args

    def get_interface(self, iface):
        return self.getter(self.parent, *self.getter_args, iface)

    def __getitem__(self, iface):
        return self.get_interface(iface)

class CachedClient:
    """
    An object that keeps dbus_next's object proxies and interfaces in
    an internal cache.

    Objects are lazily-obtained when needed. Usage is as follows:

    client = CachedClient()
    interface = client[INTROSPECTION][OBJECT_PATH][INTERFACE]
    """

    bus_name = None
    introspections = None

    def __init__(self, bus):
        """
        Initialises the class.

        :param: bus: the bus to use.
        """

        assert self.bus_name is not None
        assert self.introspections is not None

        self.bus = bus
        self.cache = {}

        # Load introspections
        for introspection, path in self.introspections.items():
            with open(path, "r") as f:
                self.cache[hash(introspection)] = f.read()

    def get_interface(self, introspection, path, interface):
        path_hashed = hash(path)
        interface_hashed = hash(path + interface)

        if not interface_hashed in self.cache:
            if not path_hashed in self.cache:
                self.cache[path_hashed] = self.bus.get_proxy_object(self.bus_name, path, self.cache[hash(introspection)])

            try:
                self.cache[interface_hashed] = self.cache[path_hashed].get_interface(interface)
            except Exception:
                self.cache[interface_hashed] = None  # skip over org.ofono.IpMultimediaSystem

        return self.cache[interface_hashed]

    def __getitem__(self, introspection):
        """
        Returns a proxy object
        """

        return ObjectProxy(
            self,
            lambda proxy, *args: ObjectProxy(
                    self,
                    CachedClient.get_interface,
                    [introspection, args[-1]] # UGLY
            ),
            [introspection]
        )

class Ofono(CachedClient):

    bus_name = "org.ofono"
    introspections = {
        "ofono" : '/usr/lib/ofono2mm/ofono.xml',
        'ofono_context' : '/usr/lib/ofono2mm/ofono_context.xml',
        'ofono_modem' : '/usr/lib/ofono2mm/ofono_modem.xml',
        'ofono_operator' : '/usr/lib/ofono2mm/ofono_operator.xml',
    }

class DBus(CachedClient):

    bus_name = "org.freedesktop.DBus"
    introspections = {
        "dbus" : '/usr/lib/ofono2mm/dbus.xml',
    }
