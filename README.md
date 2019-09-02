# thinkled - make Thinkpad LED light up as you type

Usage:
```bash
sudo modprobe -r ec_sys
sudo modprobe ec_sys write_support=1
sudo ./thinkled.py POWER
```

Makes the Thinkpad power LED flash as you type!

Also works on the LED on the back of a thinkpad.

Linux only.
