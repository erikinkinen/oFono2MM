#!/usr/bin/env python3

from dbus_next.aio import MessageBus
from dbus_next.service import (ServiceInterface,
                               method, dbus_property)
from dbus_next.constants import PropertyAccess
from dbus_next import DBusError, BusType

import asyncio
from argparse import ArgumentParser

from ofono2mm import MMModemInterface, Ofono, DBus
from ofono2mm.logger import Logger
from ofono2mm.utils import async_locked

has_bus = False

class MMInterface(ServiceInterface):
    def __init__(self, loop, bus):
        super().__init__('org.freedesktop.ModemManager1')
        self.loop = loop
        self.bus = bus
        self.ofono_client = Ofono(bus)
        self.dbus_client = DBus(bus)
        self.mm_modem_interfaces = []
        self.mm_modem_objects = []
        self.loop.create_task(self.check_ofono_presence())

    @dbus_property(access=PropertyAccess.READ)
    def Version(self) -> 's':
        return '1.22.0'

    @method()
    async def ScanDevices(self):
        try:
            await self.find_ofono_modems()
        except:
            pass

    async def check_ofono_presence(self):
        dbus_iface = self.dbus_client["dbus"]["/org/freedesktop/DBus"]["org.freedesktop.DBus"]
        dbus_iface.on_name_owner_changed(self.dbus_name_owner_changed)
        has_ofono = await dbus_iface.call_name_has_owner("org.ofono")
        if has_ofono:
            self.ofono_added()
        else:
            self.ofono_removed()

    def ofono_added(self):
        self.ofono_manager_interface = self.ofono_client["ofono"]["/"]["org.ofono.Manager"]
        self.ofono_manager_interface.on_modem_added(self.ofono_modem_added)
        self.ofono_manager_interface.on_modem_removed(self.ofono_modem_removed)
        self.loop.create_task(self.find_ofono_modems())

    def ofono_removed(self):
        self.ofono_manager_interface = None

    @async_locked
    async def find_ofono_modems(self):
        global has_bus

        for mm_object in self.mm_modem_objects:
            self.bus.unexport(mm_object)

        self.mm_modem_objects = []
        self.mm_modem_intefaces = []

        if not self.ofono_manager_interface:
            return

        self.ofono_modem_list = False
        while not self.ofono_modem_list:
            try:
                self.ofono_modem_list = [
                    x
                    for x in await self.ofono_manager_interface.call_get_modems()
                    if x[0].startswith("/ril_") or x[0].startswith("/phonesim") # FIXME
                ]
            except DBusError:
                pass

        self.i = 0

        for modem in self.ofono_modem_list:
            await self.export_new_modem(modem[0], modem[1])

        if not has_bus and len(self.mm_modem_objects) != 0:
            await self.bus.request_name('org.freedesktop.ModemManager1')
            has_bus = True

    def dbus_name_owner_changed(self, name, old_owner, new_owner):
        if name == "org.ofono":
            if new_owner == "":
                self.ofono_removed()
            elif old_owner == "":
                self.ofono_added()

    def ofono_modem_added(self, path, mprops):
        try:
            self.loop.create_task(self.export_new_modem(path, props))
        except Exception as e:
            pass

    async def export_new_modem(self, path, mprops):
        mm_modem_interface = MMModemInterface(self.loop, self.i, self.bus, self.ofono_client, path)
        mm_modem_interface.ofono_props = mprops
        self.ofono_client["ofono_modem"][path]['org.ofono.Modem'].on_property_changed(mm_modem_interface.ofono_changed)
        await mm_modem_interface.init_ofono_interfaces()
        self.bus.export(f'/org/freedesktop/ModemManager1/Modem/{self.i}', mm_modem_interface)
        mm_modem_interface.set_props()
        await mm_modem_interface.init_mm_sim_interface()
        await mm_modem_interface.init_mm_3gpp_interface()
        await mm_modem_interface.init_mm_3gpp_ussd_interface()
        await mm_modem_interface.init_mm_3gpp_profile_manager_interface()
        await mm_modem_interface.init_mm_messaging_interface()
        await mm_modem_interface.init_mm_simple_interface()
        await mm_modem_interface.init_mm_firmware_interface()
        await mm_modem_interface.init_mm_time_interface()
        await mm_modem_interface.init_mm_cdma_interface()
        await mm_modem_interface.init_mm_sar_interface()
        await mm_modem_interface.init_mm_oma_interface()
        await mm_modem_interface.init_mm_signal_interface()
        await mm_modem_interface.init_mm_location_interface()
        await mm_modem_interface.init_mm_voice_interface()
        self.mm_modem_interfaces.append(mm_modem_interface)
        self.mm_modem_objects.append(f'/org/freedesktop/ModemManager1/Modem/{self.i}')
        self.i += 1

    def ofono_modem_removed(self, path):
        for mm_object in self.mm_modem_objects:
            try:
                if mm_object.modem_name == path:
                    self.bus.unexport(mm_object)
            except Exception as e:
                pass

    @method()
    def SetLogging(self, level: 's'):
        pass

    @method()
    def ReportKernelEvent(self, properties: 'a{sv}'):
        pass

    @method()
    def InhibitDevice(self, uid: 's', inhibit: 'b'):
        pass

async def main():
    parser = ArgumentParser(description="oFono2MM.", add_help=False)
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug messages.')
    parser.add_argument('-h', '--help', action='store_true', help='Show help.')

    args = parser.parse_args()

    if args.help:
        parser.print_help()
        return

    Logger.DEBUG = args.debug

    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    loop = asyncio.get_running_loop()
    mm_manager_interface = MMInterface(loop, bus)
    bus.export('/org/freedesktop/ModemManager1', mm_manager_interface)
    await bus.wait_for_disconnect()

asyncio.run(main())
