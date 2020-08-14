#!/bin/python3

import Adafruit_BluefruitLE
'''
temps = [14, 1]
magic = 0

print((temps[magic + 1] << 8) | (temps[magic + 0] & 255)) 
'''
'''
def ble_beacon_scan():
   
    request = GATTRequester(dest_addr)
    value = request.read_by_handle(0x30)[0]
    print("Got {}".format(value))
   
    print("Scanning for beacon")
    service = BeaconService()
    devices = service.scan(5)
    for address, data in list(devices.items()):
        b = Beacon(data, address)
        print(b)

def ble_scan(timeout=10):
    print("Discovering nearby devices")
    service = DiscoveryService("hci0")
    devices = service.discover(timeout)
    for addr, name in devices.items():        
        if name == "iBBQ":
            return addr
'''
def main():
    adapter = ble.get_default_adapter()
    return

ble = Adafruit_BluefruitLE.get_provider()
ble.initialize()
ble.run_mainloop_with(main)