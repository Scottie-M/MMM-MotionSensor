# MMM-MotionSensor

This is a module for Magic Mirror that uses the RCWL_0516 Microwave Radar Motion Sensor to turn the connected display on and off when a person approaches. I realised after building and testing my mirror that the PIR I was using wasn't going to work behind the acrylic so this was my solution.

The RCWL-0516 has a detection range of around 7 meters by default, which makes it useless for this application BUT, the range can be decreased by adding a resistor across a jumper on the PCB.

This will need some soldering skill! I used an smd 500k trimmer, soldering one leg onto one of the SMD pads and a small jumper wire to attach the other. Setting the resistance just below half way seemed to work well and reduced the detection distance to a under 2 meters.

If this seems daunting then a PIR mounted externally and one of the many PIR modules may be a better option. if not... details below!



