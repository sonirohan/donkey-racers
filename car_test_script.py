#!/usr/bin/env python3
"""
Donkey Car motor + servo stress test.

Drives the ESC (throttle) and servo (steering) through a series of PWM pulse
widths via a PCA9685 board, with hard safety limits, gradual ramping, and
guaranteed return-to-neutral on exit (including Ctrl-C).

Examples:
    python3 motor_stress_test.py -i 1 --test servo
    python3 motor_stress_test.py -e 1 -s 0 --test esc --esc-max 1600
    python3 motor_stress_test.py --test both --cycles 3 --dwell 1.0
"""

import argparse
import time

import busio
from board import SCL, SDA
from adafruit_pca9685 import PCA9685

# === Constants ===
FREQ = 60  # Hz; standard ESC/servo expect ~50-60 Hz
PERIOD_US = 1_000_000 / FREQ  # ~16,667 us per cycle

# Pulse widths in microseconds (from the car's calibration)
ESC_NEUTRAL_US = 1500
SERVO_NEUTRAL_US = 1650

# HARD limits: nothing the user passes in can exceed these.
ESC_HARD_MIN_US = 1500    # forward only, so never below neutral
ESC_HARD_MAX_US = 1900
SERVO_HARD_MIN_US = 1150  # full left
SERVO_HARD_MAX_US = 1850  # full right


# === Helpers ===
def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def us_to_duty(pulse_us):
    """Convert a pulse width in microseconds to the 16-bit duty_cycle value.

    adafruit_pca9685 expects 0..0xFFFF for 0..100% duty, so:
        duty = (pulse / period) * 0xFFFF
    e.g. 1500 us @ 60 Hz -> ~5898, 1900 us -> ~7471
    """
    return int(round(pulse_us / PERIOD_US * 0xFFFF))


def frange(start, stop, step):
    """Inclusive float/int range that works in either direction."""
    if step <= 0:
        raise ValueError("step must be positive")
    vals = []
    v = start
    if start <= stop:
        while v < stop:
            vals.append(v)
            v += step
    else:
        while v > stop:
            vals.append(v)
            v -= step
    vals.append(stop)
    return vals


class Rig:
    """Wraps the PCA board and enforces limits on every write."""

    def __init__(self, pca, esc_ch, servo_ch, esc_max, servo_min, servo_max):
        self.pca = pca
        self.esc_ch = esc_ch
        self.servo_ch = servo_ch
        self.esc_max = clamp(esc_max, ESC_HARD_MIN_US, ESC_HARD_MAX_US)
        self.servo_min = clamp(servo_min, SERVO_HARD_MIN_US, SERVO_HARD_MAX_US)
        self.servo_max = clamp(servo_max, SERVO_HARD_MIN_US, SERVO_HARD_MAX_US)

    def set_esc(self, pulse_us):
        pulse_us = clamp(pulse_us, ESC_HARD_MIN_US, self.esc_max)
        self.pca.channels[self.esc_ch].duty_cycle = us_to_duty(pulse_us)
        return pulse_us

    def set_servo(self, pulse_us):
        pulse_us = clamp(pulse_us, self.servo_min, self.servo_max)
        self.pca.channels[self.servo_ch].duty_cycle = us_to_duty(pulse_us)
        return pulse_us

    def neutral(self):
        self.set_esc(ESC_NEUTRAL_US)
        self.set_servo(SERVO_NEUTRAL_US)


# === Tests ===
def servo_sweep(rig, step, dwell, cycles):
    """neutral -> full left -> full right -> neutral, repeated."""
    print(f"\n[SERVO] sweep {rig.servo_min}-{rig.servo_max} us "
          f"(neutral {SERVO_NEUTRAL_US} us), "
          f"step={step} us, dwell={dwell}s, cycles={cycles}")
    for c in range(1, cycles + 1):
        print(f"  cycle {c}/{cycles}")
        path = (frange(SERVO_NEUTRAL_US, rig.servo_min, step)
                + frange(rig.servo_min, rig.servo_max, step)
                + frange(rig.servo_max, SERVO_NEUTRAL_US, step))
        for us in path:
            actual = rig.set_servo(us)
            print(f"    servo -> {actual:7.1f} us  (duty {us_to_duty(actual)})")
            time.sleep(dwell)
    rig.set_servo(SERVO_NEUTRAL_US)


def esc_ramp(rig, step, dwell, cycles):
    """neutral -> esc_max in steps, then back down to neutral, repeated."""
    print(f"\n[ESC] ramp {ESC_NEUTRAL_US}-{rig.esc_max} us, "
          f"step={step} us, dwell={dwell}s, cycles={cycles}")
    for c in range(1, cycles + 1):
        print(f"  cycle {c}/{cycles}")
        path = (frange(ESC_NEUTRAL_US, rig.esc_max, step)
                + frange(rig.esc_max, ESC_NEUTRAL_US, step))
        for us in path:
            actual = rig.set_esc(us)
            print(f"    esc   -> {actual:7.1f} us  (duty {us_to_duty(actual)})")
            time.sleep(dwell)
        # Brief rest at neutral between cycles to let motor/ESC cool a bit
        rig.set_esc(ESC_NEUTRAL_US)
        time.sleep(1.0)
    rig.set_esc(ESC_NEUTRAL_US)


def combined(rig, step, dwell, cycles):
    """Sweep the servo while the throttle ramps up and down."""
    print(f"\n[BOTH] combined test, step={step} us, dwell={dwell}s, "
          f"cycles={cycles}")
    esc_path = (frange(ESC_NEUTRAL_US, rig.esc_max, step)
                + frange(rig.esc_max, ESC_NEUTRAL_US, step))
    servo_path = (frange(SERVO_NEUTRAL_US, rig.servo_min, step)
                  + frange(rig.servo_min, rig.servo_max, step)
                  + frange(rig.servo_max, SERVO_NEUTRAL_US, step))
    n = max(len(esc_path), len(servo_path))
    for c in range(1, cycles + 1):
        print(f"  cycle {c}/{cycles}")
        for i in range(n):
            e = rig.set_esc(esc_path[min(i, len(esc_path) - 1)])
            s = rig.set_servo(servo_path[min(i, len(servo_path) - 1)])
            print(f"    esc {e:7.1f} us | servo {s:7.1f} us")
            time.sleep(dwell)
        rig.neutral()
        time.sleep(1.0)
    rig.neutral()


# === Main ===
def main():
    parser = argparse.ArgumentParser(description="Motor/servo stress test script!")
    parser.add_argument('-e', '--esc', type=int, default=1, help='ESC channel (default: 1)')
    parser.add_argument('-s', '--servo', type=int, default=0, help='Servo channel (default: 0)')
    parser.add_argument('-i', '--initialize', type=int, default=0,
                        help='1 if the ESC needs arming (first run since power-on) (default: 0)')
    parser.add_argument('--test', choices=['servo', 'esc', 'both'], default='both',
                        help='Which test to run (default: both)')
    parser.add_argument('--step', type=float, default=25,
                        help='Pulse step size in microseconds (default: 25)')
    parser.add_argument('--dwell', type=float, default=0.5,
                        help='Seconds to hold each step (default: 0.5)')
    parser.add_argument('--cycles', type=int, default=1,
                        help='Number of repetitions (default: 1)')
    parser.add_argument('--esc-max', type=float, default=1600,
                        help=f'Max ESC pulse in us, capped at {ESC_HARD_MAX_US} (default: 1600)')
    parser.add_argument('--servo-min', type=float, default=SERVO_HARD_MIN_US,
                        help=f'Min servo pulse in us (default: {SERVO_HARD_MIN_US})')
    parser.add_argument('--servo-max', type=float, default=SERVO_HARD_MAX_US,
                        help=f'Max servo pulse in us (default: {SERVO_HARD_MAX_US})')
    parser.add_argument('-y', '--yes', action='store_true',
                        help='Skip the "wheels off the ground?" confirmation')
    args = parser.parse_args()

    if args.step <= 0 or args.dwell < 0 or args.cycles < 1:
        parser.error("step must be > 0, dwell >= 0, cycles >= 1")

    if not args.yes:
        print("SAFETY CHECK: wheels off the ground? Battery above 6.5 V? "
              "Grounds connected first?")
        input("Press Enter to continue, Ctrl-C to abort... ")

    # Setup I2C bus and PCA9685
    i2c = busio.I2C(SCL, SDA)
    pca = PCA9685(i2c)
    pca.frequency = FREQ

    rig = Rig(pca, args.esc, args.servo,
              args.esc_max, args.servo_min, args.servo_max)

    try:
        # Always start at neutral
        rig.neutral()

        if args.initialize:
            print("Arming ESC: holding neutral for 2 seconds...")
            time.sleep(2)

        if args.test in ('servo', 'both') and args.test != 'both':
            servo_sweep(rig, args.step, args.dwell, args.cycles)
        elif args.test == 'esc':
            esc_ramp(rig, args.step, args.dwell, args.cycles)
        else:
            # 'both': individual tests first, then the combined one
            servo_sweep(rig, args.step, args.dwell, args.cycles)
            esc_ramp(rig, args.step, args.dwell, args.cycles)
            combined(rig, args.step, args.dwell, args.cycles)

        print("\nAll tests finished.")

    except KeyboardInterrupt:
        print("\nInterrupted! Returning to neutral...")

    finally:
        # Runs on success, error, or Ctrl-C: never leave the motor running
        try:
            rig.neutral()
            time.sleep(0.5)
        finally:
            pca.deinit()
            print("PCA board deinitialized. Done.")


if __name__ == '__main__':
    main()