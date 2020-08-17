#!/usr/bin/python3

from bluepy.btle import *
import queue
from threading import Thread
import time

results_q = queue.Queue()

class MyDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        print("Got Notification for handle {}!".format(hex(cHandle)))
        if cHandle == 0x30:
            results = normalize_temps(data)
            q.put(results)
            '''
            i = 1
            for res in results:
                print("Probe {}: {}F".format(i, res))

                i += 1
            '''
def send_write_request(p, svc_uuid, char_uuid, notify_handle, data):
    p.writeCharacteristic(notify_handle, data, withResponse=True)

def normalize_temps(temp_array):
    temps = []
    for i in range(0,7,2):
        temp = (temp_array[i + 1] <<8) | (temp_array[i] & 255)
        temp /= 10
        # Convert to F
        f_temp = (temp * 9/5) + 32
        if f_temp == 11826.68:
            # No probe plugged in this slot
            continue
        temps.append((f_temp, datetime.datetime.now().timestamp()))
    return temps

def receive_notifications(p):
    while True:
        if p.waitForNotifications(1.0):
            continue

def setup_ble_connection():
    print("Connecting")
    # device MAC hardcoded here for now, may write code to scan 
    # and get it programatically later
    p = Peripheral("24:7d:4d:6b:e8:cc")
    print("Connected")
    p.setDelegate(MyDelegate())
    service_uuid = 0xfff0
    # Auto-pair
    send_write_request(p, service_uuid, 0xfff2, 0x0029,
                   b'\x21\x07\x06\x05\x04\x03\x02\x01\xb8\x22\x00\x00\x00\x00\x00')
    # Register for notifications for temperature beacons
    send_write_request(p, service_uuid, 0xfff4, 0x0031, b'\x01\x00')
    # Tell device to start broadcasting temp notifications
    send_write_request(p, service_uuid, 0xfff5, 0x0034, b'\x0b\x01\x00\x00\x00\x00')
    return p;

def main():
    iBBQ = setup_ble_connection()
    ble_notification_handler = Thread(target=receive_notifications,
                                      args=(iBBQ))
    ble_notification_handler.setDaemon(True)
    ble_notification_handler.start()
    '''
    MATPLOTLIB animation stuff goes here
    '''

if __name__ == '__main__':
    main()
