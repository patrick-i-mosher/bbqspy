#!/usr/bin/python3

from bluetooth.ble import DiscoveryService


'''
temps = [14, 1]
magic = 0

print((temps[magic + 1] << 8) | (temps[magic + 0] & 255)) 
'''
def do_scan(timeout=10):
    print("Discovering devices")
    service = DiscoveryService
    devices = service.discover(timeout)
    for name, addr in devices.item:
        print("{} - {}").format(addr, name)

def main():
    do_scan()

if __name__ == '__main__':
    main()