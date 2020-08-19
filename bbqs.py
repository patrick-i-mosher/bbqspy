#!/usr/bin/python3

from bluepy.btle import *
from threading import Thread
from datetime import datetime
import queue
import matplotlib.pyplot as plt
import matplotlib.animation as animation

class MyDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        if cHandle == 0x30:
            results = normalize_temps(data)
            results_q.put(results)

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
        temps.append((f_temp, datetime.now().timestamp()))
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
    receive_notifications(p);

def animate(i, xs, ys):
    datapoints = results_q.get()
    ys.append(datapoints[0][0])
    xs.append(datapoints[1][1])
    xs = xs[-100:]
    ys = ys[-100:]
    ax.clear()
    ax.plot(xs, ys)
    print("{}, {}".format(xs, ys))
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    plt.title("iBBQ Temp over Time")
    plt.ylabel("Temperature (deg F)")


results_q = queue.Queue()
fig = plt.figure()
ax = fig.add_subplot(1,1,1)

def main():
    # Start a new thread to communicate with the temperature probe
    ble_notification_handler = Thread(target=setup_ble_connection,
                                      daemon=True).start()
    # Set up visualization
    xs = []
    ys = []
    ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=1000)
    plt.show()

if __name__ == '__main__':
    main()
