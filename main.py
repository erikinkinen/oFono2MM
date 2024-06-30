#!/usr/bin/env python3

import asyncio
from os import environ
from argparse import ArgumentParser

from dbus_next.aio import MessageBus
from dbus_next.service import (ServiceInterface,
                               method, dbus_property)
from dbus_next.constants import PropertyAccess
from dbus_next import DBusError, BusType, Variant

from ofono2mm import MMModemInterface, Ofono, DBus
from ofono2mm.utils import async_locked, read_setting
from ofono2mm.logging import ofono2mm_print

has_bus = False
sim_i = 0

class MMInterface(ServiceInterface):
    def __init__(self, loop, bus, verbose=False):
        super().__init__('org.freedesktop.ModemManager1')
        ofono2mm_print("Initializing Manager interface", verbose)
        self.loop = loop
        self.bus = bus
        self.verbose = verbose
        self.i = 0
        self.ofono_client = Ofono(bus)
        self.dbus_client = DBus(bus)
        self.mm_modem_interfaces = []
        self.mm_modem_objects = []
        self.offline_modems = []
        self.modem_added_block = False
        self.apn_task = None
        self.loop.create_task(self.check_ofono_presence())

    @dbus_property(access=PropertyAccess.READ)
    def Version(self) -> 's':
        return '1.22.0'

    @method()
    async def ScanDevices(self):
        ofono2mm_print("Scanning devices", self.verbose)

        try:
            await self.find_ofono_modems()
        except Exception as e:
            ofono2mm_print(f"Failed to scan for devices: {e}", self.verbose)

    async def check_ofono_presence(self):
        ofono2mm_print("Checking ofono presence", self.verbose)

        dbus_iface = self.dbus_client["dbus"]["/org/freedesktop/DBus"]["org.freedesktop.DBus"]
        dbus_iface.on_name_owner_changed(self.dbus_name_owner_changed)
        has_ofono = await dbus_iface.call_name_has_owner("org.ofono")
        if has_ofono:
            self.ofono_added()
        else:
            self.ofono_removed()

    def ofono_added(self):
        ofono2mm_print("oFono added", self.verbose)

        self.ofono_manager_interface = self.ofono_client["ofono"]["/"]["org.ofono.Manager"]
        self.ofono_manager_interface.on_modem_added(self.ofono_modem_added)
        self.ofono_manager_interface.on_modem_removed(self.ofono_modem_removed)
        self.loop.create_task(self.find_ofono_modems())

    def ofono_removed(self):
        ofono2mm_print("oFono removed", self.verbose)
        self.ofono_manager_interface = None

    @async_locked
    async def find_ofono_modems(self):
        ofono2mm_print("Finding oFono modems", self.verbose)

        global has_bus, sim_i

        for mm_object in self.mm_modem_objects:
            self.bus.unexport(mm_object)

        self.mm_modem_objects = []
        self.mm_modem_interfaces = []
        self.offline_modems = []

        if not self.ofono_manager_interface:
            ofono2mm_print("oFono manager interface is empty, skipping", self.verbose)
            return

        self.ofono_modem_list = False
        self.modem_added_block = True
        while not self.ofono_modem_list:
            try:
                if self.ofono_manager_interface is None:
                    ofono2mm_print("oFono manager interface is not initialized properly. skipping", self.verbose)
                    return

                modems = await self.ofono_manager_interface.call_get_modems()

                for modem in modems:
                    ofono2mm_print(f"Modems available in oFono: {modem[0]}", self.verbose)

                self.ofono_modem_list = [
                    x
                    for x in modems
                    if x[0].startswith("/ril_") or x[0].startswith("/phonesim") # FIXME
                ]

                if not self.ofono_modem_list:
                    ofono2mm_print("No modems available, retrying", self.verbose)
                    await asyncio.sleep(0.3)
                    continue

                for modem in self.ofono_modem_list:
                    ofono2mm_print(f"Selected modem: {modem[0]}", self.verbose)

                    if modem[1]['Online'].value == False:
                        try:
                            for i in range(5):
                                ofono2mm_print(f"Setting modem {modem[0]} to online", self.verbose)
                                self.ofono_modem = self.ofono_client["ofono_modem"][modem[0]]['org.ofono.Modem']
                                await self.ofono_modem.call_set_property('Online', Variant('b', True))
                                modem[1]['Online'].value = True
                                break
                        except DBusError as e:
                            ofono2mm_print(f"Error setting modem {modem[0]} to online: {e}", self.verbose)
                            self.ofono_modem_list = False
            except DBusError as e:
                ofono2mm_print(f"Failed to get the current modem: {e}", self.verbose)
                self.ofono_modem_list = False

        self.i = 0
        sim_i = len(self.ofono_modem_list)

        for modem in self.ofono_modem_list:
            try:
                self.ofono_sim_manager = self.ofono_client["ofono_modem"][modem[0]]['org.ofono.SimManager']
                sim_manager_props = await self.ofono_sim_manager.call_get_properties()
                sim_present = sim_manager_props['Present'].value

                ofono2mm_print(f"modem is {modem[0]}, online: {modem[1]['Online'].value}, number of sims: {sim_i} sim is present: {sim_present}", self.verbose)

                if sim_present == False and sim_i > 1:
                    self.offline_modems.append(modem)
                else:
                    await self.export_new_modem(modem[0], modem[1])
            except DBusError as e:
                print(f"Error interacting with modem {modem[0]}: {e}")
                continue

        for modem_info in self.offline_modems:
            await self.export_new_modem(*modem_info)

        if not has_bus and len(self.mm_modem_objects) != 0:
            await self.bus.request_name('org.freedesktop.ModemManager1')
            has_bus = True

    def dbus_name_owner_changed(self, name, old_owner, new_owner):
        if name == "org.ofono":
            ofono2mm_print(f"oFono name owner changed, name: {name}, old owner: {old_owner}, new owner: {new_owner}", self.verbose)
            if new_owner == "":
                self.ofono_removed()
            elif old_owner == "":
                self.ofono_added()

    def ofono_modem_added(self, path, mprops):
        ofono2mm_print(f"oFono modem added at path {path} and properties {mprops}", self.verbose)

        if self.modem_added_block:
            ofono2mm_print(f"oFono modem block is on, skipping", self.verbose)
            return

        try:
            self.loop.create_task(self.export_new_modem(path, mprops))
        except Exception as e:
            ofono2mm_print(f"Failed to create task for modem {path}: {e}", self.verbose)

    async def export_new_modem(self, path, mprops):
        ofono2mm_print(f"Processing modem {path} with properties {mprops}", self.verbose)
        for mm_modem in self.mm_modem_interfaces:
            if mm_modem.modem_name == path:
                ofono2mm_print(f"Modem {path} is already exported, skipping", self.verbose)
                return

        mm_modem_interface = MMModemInterface(self.loop, self.i, self.bus, self.ofono_client, path, self.verbose)
        mm_modem_interface.ofono_props = mprops
        self.ofono_client["ofono_modem"][path]['org.ofono.Modem'].on_property_changed(mm_modem_interface.ofono_changed)
        await mm_modem_interface.init_ofono_interfaces()
        self.bus.export(f'/org/freedesktop/ModemManager1/Modem/{self.i}', mm_modem_interface)
        self.modem_added_block = False
        mm_modem_interface.set_props()
        promises = [mm_modem_interface.init_mm_sim_interface(),
                    mm_modem_interface.init_mm_3gpp_interface(),
                    mm_modem_interface.init_mm_3gpp_ussd_interface(),
                    mm_modem_interface.init_mm_3gpp_profile_manager_interface(),
                    mm_modem_interface.init_mm_messaging_interface(),
                    mm_modem_interface.init_mm_simple_interface(),
                    mm_modem_interface.init_mm_firmware_interface(),
                    mm_modem_interface.init_mm_time_interface(),
                    mm_modem_interface.init_mm_cdma_interface(),
                    mm_modem_interface.init_mm_sar_interface(),
                    mm_modem_interface.init_mm_oma_interface(),
                    mm_modem_interface.init_mm_signal_interface(),
                    mm_modem_interface.init_mm_location_interface(),
                    mm_modem_interface.init_mm_voice_interface()]

        await asyncio.gather(*promises)

        self.mm_modem_interfaces.append(mm_modem_interface)
        self.mm_modem_objects.append(f'/org/freedesktop/ModemManager1/Modem/{self.i}')
        self.i += 1

        mm_modem_simple = mm_modem_interface.get_mm_modem_simple_interface()
        try:
            self.apn_task = self.loop.create_task(self.simple_set_apn(mm_modem_simple))
        except Exception:
            pass

        if read_setting('data').strip() == 'True':
            ofono2mm_print("Activating context on startup", self.verbose)

            try:
                self.loop.create_task(self.startup_activate_context(mm_modem_simple, mm_modem_interface))
            except Exception as e:
                ofono2mm_print(f"Failed to activate context: {e}", self.verbose)

    async def startup_activate_context(self, mm_modem_simple, mm_modem):
        ofono2mm_print("Activating context on startup", self.verbose)

        while True:
            if read_setting('data').strip() == 'False':
                ofono2mm_print("Data toggle changed to False, no longer need to activate on startup", self.verbose)
                return

            strength = mm_modem_simple.check_signal_strength()

            if strength == 0:
                ofono2mm_print("Strength is not available, skipping", self.verbose)
            elif strength > 0:
                ofono2mm_print(f"Signal strength is {strength}, activating context now", self.verbose)

                try:
                    ret = await mm_modem.activate_internet_context()
                    if ret == True:
                        return
                except Exception as e:
                    ofono2mm_print(f"Failed to activate context: {e}", self.verbose)

            await asyncio.sleep(2)

    async def simple_set_apn(self, mm_modem_simple):
        ofono2mm_print("Setting APN in Network Manager", self.verbose)

        while True:
            ret = await mm_modem_simple.network_manager_set_apn()
            if ret == True:
                self.apn_task = None
                return

            await asyncio.sleep(2)

    def ofono_modem_removed(self, path):
        ofono2mm_print(f"oFono modem removed at path {path}", self.verbose)

        for mm_object in self.mm_modem_objects:
            try:
                for mm_modem in self.mm_modem_interfaces:
                    if mm_modem.modem_name == path:
                        ofono2mm_print(f"oFono path matches our modem interface path, unexporting", self.verbose)
                        mm_modem.unexport_mm_interface_objects()
                        self.bus.unexport(mm_object)
                        mm_modem = None
            except Exception as e:
                ofono2mm_print(f"Failed to unexport modem at path {path} with object path {mm_object}: {e}", self.verbose)

        self.mm_modem_objects = []
        self.mm_modem_interfaces = []

    @method()
    def SetLogging(self, level: 's'):
        ofono2mm_print(f"Set logging with level {level}", self.verbose)

    @method()
    def ReportKernelEvent(self, properties: 'a{sv}'):
        ofono2mm_print(f"Report kernel events with properties {properties}", self.verbose)

    @method()
    def InhibitDevice(self, uid: 's', inhibit: 'b'):
        ofono2mm_print(f"Inhibit device with uid {uid} set to {inhibit}", self.verbose)

def get_version():
    return "1.22.0"

def print_version():
    version = get_version()
    print(f"oFono2MM version {version}")

def custom_help(parser):
    parser.print_help()
    print("\nDBus system service to control mobile broadband modems through oFono.")

async def main():
    parser = ArgumentParser(description="Run the ModemManager interface.", add_help=False)
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output.')
    parser.add_argument('-V', '--version', action='store_true', help='Print version.')
    parser.add_argument('-h', '--help', action='store_true', help='Show help.')

    args = parser.parse_args()

    if args.version:
        print_version()
        return

    if args.help:
        custom_help(parser)
        return

    if environ.get('MODEM_DEBUG', 'false').lower() == 'true':
        verbose = True
    else:
        verbose = args.verbose

    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    loop = asyncio.get_running_loop()
    mm_manager_interface = MMInterface(loop, bus, verbose=verbose)
    bus.export('/org/freedesktop/ModemManager1', mm_manager_interface)
    await bus.wait_for_disconnect()

if __name__ == "__main__":
    asyncio.run(main())
