#!/usr/bin/env python3

# https://www.reddit.com/r/thinkpad/comments/7n8eyu/thinkpad_led_control_under_gnulinux/
# echo -n -e "\xc7" | sudo dd of="/sys/kernel/debug/ec/ec0/io" bs=1 seek=12 count=1 conv=notrunc

import enum
import sys
import subprocess
import os
import time

import keyboard


class LEDLight(enum.IntEnum):
    POWER = 0x0
    FN_LOCK = 0x6
    THINKPAD_I_X1 = 0x7
    THINKPAD_I_P51 = 0xa


class LEDState(enum.IntEnum):
    OFF = 0x0
    ON = 0x8
    BLINK = 0xc


DEV_FILENAME = "/sys/kernel/debug/ec/ec0/io"


def usage():
    light_options = "|".join(led_light.name for led_light in LEDLight)
    state_options = "|".join(led_state.name for led_state in LEDState)
    s = "Usage: %s <%s> [%s]\n" % (sys.argv[0], light_options, state_options)
    sys.stderr.write(s)
    return 1


def set_state(dev_file, led_light, led_state):
    dev_file.seek(12)
    byte = bytes([(led_state << 4) | led_light])
    dev_file.write(byte)


def main():
    if not (2 <= len(sys.argv) <= 3):
        return usage()

    dev_file = open(DEV_FILENAME, mode="w+b", buffering=0)

    try:
        led_light = LEDLight[sys.argv[1]]
    except KeyError:
        return usage()

    if len(sys.argv) == 3:
        try:
            led_state = LEDState[sys.argv[2]]
        except KeyError:
            return usage()
        set_state(dev_file, led_light, led_state)
        return 0

    # Set of pressed-down key scan codes.
    # I used to use a reference count, but holding a key
    # will cause multiple "down" events and only one "up".
    # I also use scan codes (e.g. 37) instead of name (e.g. "control_l"),
    # since probably there's some weird edge case with the names too.
    keys = set()
    last_seen = 0

    def hook(keyboard_event):
        nonlocal keys
        nonlocal last_seen

        old_count = len(keys)

        # Sometimes weird things will happen and our state
        # will get out of sync.
        # Fix this by clearing out the state on inactivity,
        # since inactivity probably means 0 keys are down.
        now = time.time()
        if now - last_seen > 10:
            keys = set()
        last_seen = now

        # Only print up / down.
        # Avoid printing scan_code because that would keylog passwords.
        # flush=True to make tail -F useful when redirecting into a file.
        print("event_type = %r" % keyboard_event.event_type, flush=True)
        if keyboard_event.event_type == "down":
            keys |= {keyboard_event.scan_code}
        elif keyboard_event.event_type == "up":
            keys -= {keyboard_event.scan_code}

        new_count = len(keys)
        if old_count == 0 and new_count >= 1:
            print("ON", flush=True)
            set_state(dev_file, led_light, LEDState.ON)
        elif old_count >= 1 and new_count == 0:
            print("OFF", flush=True)
            set_state(dev_file, led_light, LEDState.OFF)

    keyboard.hook(hook)

    keyboard.wait()


if __name__ == "__main__":
    sys.exit(main())
