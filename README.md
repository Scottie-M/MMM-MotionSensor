# MMM-MotionSensor

### This is a module for Magic Mirror that uses the RCWL_0516 Microwave Radar Motion Sensor to turn the connected display on and off when a person approaches. 

I realised after building and testing my mirror that the PIR I was using wasn't going to work behind the acrylic so this was my solution.

The RCWL-0516 has a detection range of around 7 meters by default, which makes it useless for this application BUT, the range can be decreased by adding a resistor across a jumper on the PCB.

This will need some soldering skill! I used an smd 500k trimmer pot, soldering one leg onto one of the SMD pads and a small jumper wire to attach the other. Setting the resistance just below half way seemed to work well and reduced the detection distance to a under 2 meters. I tried a few values of fixed resistors first but the ability to make small adjustments with a trimmer pot once the RCWL-0516 is in place is useful.

If this seems daunting then a PIR mounted externally and one of the many PIR modules may be a better option. if not... details below!


**To install:**
```bash
cd ~/MagicMirror
npm install winston
cd modules
git clone https://github.com/Scottie-M/MMM-MotionSensor.git
```
<br><br>
This is a sample config for the module:
```js
{
  module: "MMM-MotionSensor",
  header: "Motion Sensor",
  position: "bottom_left",
  config: {
    off_delay: 30 ,			// in seconds
    debounce_time: 2, 		// in seconds
    radar_pin: 4,				// GPIO pin used for the sensor
    debug: {level: "info"},
    diagnostic: false
  },
},
```
<br>

Having `position` set is useful for the initial set up but should be removed afterwards, it is just an indicator that shows the TV state. If `diagnostic` is true it also shows whether or not motion is detected to allow adjustment of the detection range.

<br><br>


| Option           | Description |
|------------------|----------------|
| `off_delay`| The time in seconds that the display will remain on once motion at the mirror has stopped<br>Default: `30`|
| `debounce_time`| To prevent repeated triggers, 2 seconds is about right!<br>Default: `2`  |
| `radar_pin`| This is the GPIO pin that `out` on the RCWL-0516 is connected to<br>Default: `4` | 
| `debug`| The level of log information sent to the console and log file.<br>Default: `"info"`<br>This needs to be in the format `{level:"LOG LEVEL"}`<br>Log levels can be: `"debug", "info" "warning", "error", "critical"`|
| `diagnostic`| This is a diagnostic mode that keeps the display turned on. A message is displayed when motion is detected and when it stops.<br>This is useful for setting up the RCWL-0516 and adjusting the trimmer to set the detection distance.<br>Default: `false`|
<br>
<br>
The Python code in this module is what interacts with the RCWL-0516 and turns the display on and off. It will try to auto detect the display server in use, X11 (Bullseye) or wayland (Bookworm / Trixie) and then try to detect the display output in use.<br><br>

The correct command to turn the display on and off should then be used.<br>
Typically for Wayland:
```
/usr/bin/wlr-randr --output HDMI-A-1 --off
```
And X11:
```
/usr/bin/xrandr -display :0 --output HDMI-1 --off
```
<br>
The following outputs will used in this order of preferance if they are available:<br>

`"HDMI", "DP", "DSI", "eDP", "DPI", "LVDS", "TV", "Composite", "CVBS", "VGA", "DVI"`
<br><br>
I will likely be adding support for multiple displays and manually overriding the display selection and command through the config options

If you have issues with your display turning off and straight back on again, it is likely that the monitor is set to auto detect the input sorurce and has cycled through them and back the connected input. This will trigger the Raspberry Pi to reactivate the display. Disable auto select on the monitor to fix this.<br>

All console output from `MMM-MotionSensor.js`, `node_helper.js` and the Python code are all directed to a log file created in the home directory in a folder called MotionSensor, this is also copied locally to the console that started MagicMirror.<br>
<br>
TODO - Test console output when using pm2, also test logging with pm2
<br><br>
Some detailed information about the RCWL-0516 and and the detection range adjustment can be found here:<br>
[Last Minute Engineers](https://lastminuteengineers.com/rcwl0516-microwave-radar-motion-sensor-arduino-tutorial/)<br>
[Wolles Elektronikkiste](https://wolles-elektronikkiste.de/en/rcwl-0516-microwave-radar-motion-detector)<br>
<br>
To reduce the detection range connected a [500k Trimmer pot](https://uk.rs-online.com/web/p/trimmer-potentiometers/1001234) to the range adjustment jumper. In this case it may be best to avoid SMD hot air rework soldering and just use a fine point on a soldering iron. Keep this below 230 deegrees celcius and be quick, otherwise the heat may destroy the IC on the other side. A good low temp lead solder or SMD solder paste is best.<br>
I soldered the jumper wire to the trimmer pad first, then lined it and the other pad up with the pads on the board and applied the soldering iron very quickly to both. A little bit of glue at the side of the trimmer pot will help keep it stable when adjusting the resistance.

<br><br>
GND - To a Ground pin on the Raspberry Pi<br>
OUT - To the GPIO pin you want to use (Default is 4)<br>
VIN - To a 5V supply pin on the Raspberry Pi<br>
<br>
I soldered a 90 degree header on this and used Dupont jumper wires to connect.<br><br>

<img src="https://github.com/user-attachments/assets/80c9eb22-da5d-431f-bf85-09dd351db8c3" alt="RCWL-0516" width="500"> <br>
<br>


<img width="800"  alt="ScreenShot 1" src="https://github.com/user-attachments/assets/042b5c77-8ea0-49d8-bdd3-6d7e31ca1b57" />



