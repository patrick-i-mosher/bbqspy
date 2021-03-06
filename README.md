# bbqspy

## Overview
This tool allows users to receive and record temperature data from the Inkbird Smart BBQ Thermometer.  This tool has only been tested against the Inkbird model IBT-4XS using a RaspberryPi 3b.  I built this because I felt the device's companion mobile app had insufficient support for recording data over the course of a cooking session.

## Process Overview
I've included an overview of the approach I took to reverse-engineering the thermometer and building the tool below.

### Determine the Device's Address
The first step in learning how to communicate with a particular bluetooth device is discovering it's adapter address.  There are a number of ways to do this; I used the nRF Connect app on Android to gather some basic information about the thermometer.  

<img src="images/nRF_Connect.jpg" alt="nRF Connect" width="250"/>

As you can see, nRF Connect provides not only the device's bluetooth adapter address but also some basic information about the device.  Connecting to the device via the nRF interface can provide more detailed information, including advertised services and characteristics.  

### Examine the Device's Communication Protocol
Now that we know the device's address, we can start investigatng how it communicates.  Packet capture is usually the best place to start, and in this case I was fortunate enough to have access to full capture of my non-rooted Android phone's bluetooth adapter.

#### Retrieving the btsnoop_hci.log File
Many Android devices are capable of saving full capture of their bluetooth adapter in a log file called btsnoop_hci.log.  In order to allow your device to start generating this file, toggle "Enable Bluetooth HCI snoop log," in Developer Options.  The location of this file differs across Android versions and device manufacturers; in some cases it's located in the user-accessible `/sdcard` folder.  In other cases it's saved in read-restricted locations.  In my case it was the latter, and I was not able to simply pull the log directly from my phone's filesystem.  However, the Android Debug Bridge offers helpful functionality in the form of the `bugreport` command.  

#### adb bugreport
The `adb bugreport [PATH]` command (where [PATH] is the filesystem location to output the bug report) dumps a ton of useful forensic inforation about the currently connected Android device.  

![adb bugreport](images/adb_bugreport_screencap.png)

Among the many artifacts created by `adb bugreport` is a snapshot of some portions of the device's filesystem.  These are stored in a folder called `FS/`.  Some simple investigation reveals that the `btsnoop_hci.log` file is stored at `FS/data/log/bt/btsnoop_hci.log`.
 
 #### Analyzing the btsnoop_hci.log File
 Analyzing the btsnoop_hci.log file is relatively straightforward; just open it in Wireshark.
 
![btsnoop_hci.log](images/wireshark_screencap_1.png)
 
Filtering on the thermometer's address quickly shows that the vast majority of packets are Handle Value Notifications for handle 0x0030, and they are sent once per second.  It's a pretty safe bet that this is the packet that contains the temperature data.  

![btsnoop_hci.log](images/wireshark_screencap_2.png)

Unfortunately, the value field of the packet doesn't yield a ton of immediately useful information.  We see the value 0x1801, followed by three 16-bit values of 0xf6ff.  This particular thermometer has four probe slots, and at the time of the packet capture only one probe was plugged in.  Assuming that 0x1801 represents the temperature of the probe that is plugged in and 0xf6ff represents the missing probes supports the supposition that this is the device's temperature data.  However, I know that it's not 0x1801, or 6,145, degrees in my lab, so it looks like it's going to take some more work to figure out how the thermometer is encoding the temperature data.

### Examining the Companion App's Functionality
The best place to go to figure out how the thermometer is encoding and transmitting the temperature data is the thermometer's mobile companion app, in this case named "BBQ Go."  More specifically, the companion app's source code.  Unfortunately, that particular resource isn't publically available...or is it?

#### Retrieving the Companion App's APK File
Android uses Android Package, or APK, files to distribute and install applications.  The APK is really just a container for all of the things that make up the app, including the app's Dalvik bytecode (stored `.dex` files).  This bytecode in particular is what we're after in this step of the process.  A device's APK files are particularly stored in locations not directly accessible to non-privileged users, but as in the case of the btsnoop_hci.log file, `adb` once again provides the basis for a solution.

The first step to retrieving the APK file is to learn it's name.  This is possible using Android's built-in package manager.  The command `adb shell pm list packages` lists the name of every package installed on the device.  Using `grep` to search the output for the string "bbq," yields the package's name.

![list_packages](images/list_packages.png)

The next step is to again use `package manager` to determine the APK's location.  The command `adb shell pm path qlnet.com.bbqgo` provides the path to the APK.

![find_path](images/find_path.png) 

There's the path to the APK file!  For those of you wondering about the odd string of letters in the pathname, that's a base64-encoded string that decodes to Kannada, Chinese, and Korean characters that, as far as I can tell, are non-sensical.

The final step to retrieving the APK file is to, well, retrieve it.  We can do this using the command `adb pull` with the path from the previous step.

![pull_apk](images/pull_apk.png) 

#### Recovering the App's Source Code
Remember how I mentioned that the APK is really just a container?  It's actually a Zip archive that we can extract and examine more closely.

![list_apk](images/list_apk_contents.png) 

While it's possible to examine the .dex file directly to figure out how it works, in this case there's a much more convenient option.  There are numerous tools to "decompile," the bytecode.  For this project I used a tool called [jadx](https://github.com/skylot/jadx).

![jadx](images/jadx.png) 

Now we can simply open the `sources` folder in Android Studio, and dig around in the source code to our heart's content.

#### Digging In
Jumping in to the source code for an app that somebody else built can be an enlightening, and occiasionally entertaining, experience.  This app, for example, also contained the source code for three other apps, and the project name was the Android Studio default of "example."  I won't dive in to all of the other quirkiness I came across, but I will say that while I was examining the source I was also looking for indicators of malicious or potentially malicious activity, and I didn't find any.

The source tree for this file contains the helpfully-named MyBbqBleService.java file, which it's safe to assume contains the code to interact with the thermometer's bluetooth low energy (BLE) adapter.  Opening this file presents a wall of helpful code, such as:

```java    
    public boolean J = true;  
    private final int K = 24;  
    private final int L = 23;  
    private final int M = 22;  
    private final int N = 21;  
    private final int O = 20;  
    private int P = 30000;  
```

Now these lousy variable names aren't because the developer was lazy; it's a result of the decompilation process.  One of the challenges of a reverse-engineering project is following the flow of control when symbols don't have meaningful names.  One thing I find helpful is to rename symbols as you figure out their purpose.  This is easy to do in Android Studio; just highlight the variable or function name, right-click, and select "rename," from the "refactor," menu.  This will update that symbol's name throughout the entire file.  Another helpful tip is to pay attention to context clues.  While the compilation process removes comments from the code, you can still gain a lot of information based on the strings that the decompiled code contains.  This project in particular makes extensive use of Androids logging API, and the strings associated with the call to the logging function provides a heap of useful information.

This file contains around 1,200 lines of code.  It can be hard to find a starting place, but fortunately we know what we are looking for: the code that handles temperature data received from the thermometer.  In Android, the BluetoothGattCallback abstract class is used to implement callbacks for relevant bluetooth low energy events, so this is probably a good place to start.

Looking at this app's BluetoothGattCallback implementation, we find a very long `if...else if` block that performs different actions determined by the value of the data packet received.  Towards the end of it is this block of code:
```java
else if (bluetoothGattCharacteristic.getUuid().equals(MyBbqBleService.this.F.getUuid())) {
byte[] value3 = bluetoothGattCharacteristic.getValue();
if (MyBbqBleService.this.J) {
    MyBbqBleService.this.ad.putInt("PROBE_COUNT", value3.length / 2);
    MyBbqBleService.this.ad.commit();
    boolean unused8 = MyBbqBleService.this.J = false;
    MyBbqBleService.this.sendBroadcast(new Intent("INTENT_GET_TEMP"));
}
for (int i2 = 0; i2 < value3.length; i2 += 2) {
    short round = (short) ((int) Math.round(((double) MyBbqBleService.a(value3, i2)) / 10.0d));
    Log.i(MyBbqBleService.this.f317a, "onCharacteristicChanged: t: " + round);
    if (round < MyBbqBleService.this.v || round > MyBbqBleService.this.u) {
        MyBbqBleService.this.a(MyBbqBleService.this.r[i2 / 2]);
    } else {
        MyBbqBleService.this.a(MyBbqBleService.this.q[i2 / 2], round);
        MyBbqBleService.this.d.a((i2 / 2) + 1, round);
    }
}

```
The `INTENT_GET_TEMP` seems like a pretty strong clue that we're on the right track.  The following line offers some more clues: 

```java
short round = (short) ((int) Math.round(((double) MyBbqBleService.a(value3, i2)) / 10.0d));`
```
This line is in a loop that iterates over a `byte[]` (`value3` in the line above).  The line calls the function `MyBbqService.a()` with the `byte[] value3` and the loop's counter (`i2`) as arguments, divides the resulting value by 10, and rounds it to the nearest whole number.  Let's take a look at `MyBbqService.a()`.  To easily navigate to the correct function, highlight the function name in Android Studio, right-click, and select "Go To" -> "Declaration or Usages."  That takes us to this function:

```java
public static short a(byte[] bArr, int i2) {
    if (bArr.length <= i2) {
        return 0;
    }
    return (short) ((bArr[i2 + 1] << 8) | (bArr[i2 + 0] & 255));
}
```
This looks like it might be the temperature decode operation we were looking for.  This line performs an 8-bit left shift on the value in index `i2 + 1`, performs a bitwise `AND` of the value in index `i2` and 255, and finally performs a logical `OR` of those two values.  Using the example data from our packet capture, where the first two bytes were 0x1801, we can perform the following operation:
```
0x01 << 0x08 = 0x100
0x18 & 0xff = 0x10
0x100 | 0x10 = 0x110
0x110 / 0x0a = 0x11
0x11 = 27
```
The final value we get is 0x11, or 27 in base 10.  Keeping in mind that this thermometer was manufactured outside of the United States and likely uses Celsius as the default temperature unit, we can conclude that the device is reporting that the first probe's temperature is 27 degrees Celsius.  Calculating that to Fahrenheit yields 80.6, which (rounded up) was the temperature displayed on the face of the thermometer at the time of the PCAP.





