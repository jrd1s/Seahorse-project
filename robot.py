"""PS5 DualSense -> serial bridge for the ROV Arduino sketch (robot.ino).

Controls:
  Left stick (up/down) -> servo pair angle (up = 180, down = 0, center = 90)
  R2 / L2               -> thrusters forward / backward, speed by trigger pressure
  X                      -> winch stop
  Square                 -> winch wind in
  Circle                 -> winch wind out

Run with --calibrate to print raw axis/button indices if the mappings below
don't match your controller/driver.
"""

import sys
import time

import pygame
import serial
from serial.tools import list_ports

SERIAL_PORT = "COM3"  # confirmed: FTDI USB Serial Port on this machine
BAUD_RATE = 9600

UPDATE_RATE_HZ = 50
UPDATE_INTERVAL = 1.0 / UPDATE_RATE_HZ

STICK_DEADZONE = 0.08
TRIGGER_DEADZONE = 0.03

SERVO_CENTER_ANGLE = 90
SERVO_RANGE = 90  # +/- degrees from center across full stick travel

THRUSTER_NEUTRAL_US = 1500
THRUSTER_RANGE_US = 400  # +/- microseconds from neutral at full trigger press

# SDL2 DualSense mapping (pygame 2.x on Windows). Use --calibrate to confirm.
AXIS_LEFT_STICK_Y = 1
AXIS_L2 = 4
AXIS_R2 = 5

BUTTON_X = 0       # Winch stop
BUTTON_CIRCLE = 1  # Winch wind out
BUTTON_SQUARE = 2  # Winch wind in


def apply_deadzone(value, deadzone):
    return 0.0 if abs(value) < deadzone else value


def open_serial():
    try:
        return serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    except serial.SerialException as exc:
        print(f"Could not open {SERIAL_PORT}: {exc}")
        print("Available ports:")
        for port in list_ports.comports():
            print(f"  {port.device} - {port.description}")
        sys.exit(1)


def open_controller():
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        print("No controller detected. Connect the PS5 controller and try again.")
        sys.exit(1)
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Using controller: {joystick.get_name()}")
    return joystick


def calibrate(joystick):
    print("Move sticks/triggers and press buttons. Ctrl+C to quit.")
    while True:
        pygame.event.pump()
        axes = [round(joystick.get_axis(i), 2) for i in range(joystick.get_numaxes())]
        buttons = [joystick.get_button(i) for i in range(joystick.get_numbuttons())]
        print(f"axes={axes} buttons={buttons}", end="\r")
        time.sleep(0.05)


def main():
    pygame.init()
    joystick = open_controller()

    if "--calibrate" in sys.argv:
        calibrate(joystick)
        return

    ser = open_serial()
    time.sleep(2)  # let the Arduino finish its reset after the port opens

    prev_buttons = {BUTTON_X: 0, BUTTON_CIRCLE: 0, BUTTON_SQUARE: 0}
    last_angle_sent = None
    last_us_sent = None
    last_send_time = 0.0

    print("Controller bridge running. Ctrl+C to quit.")
    try:
        while True:
            pygame.event.pump()

            if joystick.get_button(BUTTON_X) and not prev_buttons[BUTTON_X]:
                ser.write(b"1\n")
            if joystick.get_button(BUTTON_SQUARE) and not prev_buttons[BUTTON_SQUARE]:
                ser.write(b"2\n")
            if joystick.get_button(BUTTON_CIRCLE) and not prev_buttons[BUTTON_CIRCLE]:
                ser.write(b"3\n")

            for button in prev_buttons:
                prev_buttons[button] = joystick.get_button(button)

            now = time.time()
            if now - last_send_time >= UPDATE_INTERVAL:
                last_send_time = now

                stick_y = apply_deadzone(joystick.get_axis(AXIS_LEFT_STICK_Y), STICK_DEADZONE)
                angle = int(SERVO_CENTER_ANGLE - stick_y * SERVO_RANGE)
                angle = max(0, min(180, angle))
                if angle != last_angle_sent:
                    ser.write(f"S{angle}\n".encode())
                    last_angle_sent = angle

                # This DualSense reports triggers as 0 (released) .. 1 (full
                # press) via SDL's GameController axis mapping, not the -1..1
                # range some joystick APIs use - confirmed by reading resting
                # axis values before wiring this up. Adjust if yours differs.
                l2 = joystick.get_axis(AXIS_L2)
                r2 = joystick.get_axis(AXIS_R2)
                thrust = apply_deadzone(r2 - l2, TRIGGER_DEADZONE)
                us = int(THRUSTER_NEUTRAL_US + thrust * THRUSTER_RANGE_US)
                if us != last_us_sent:
                    ser.write(f"T{us}\n".encode())
                    last_us_sent = us

            time.sleep(0.005)
    except KeyboardInterrupt:
        pass
    finally:
        ser.write(b"T1500\n")
        ser.write(b"1\n")
        ser.close()
        pygame.quit()


if __name__ == "__main__":
    main()
