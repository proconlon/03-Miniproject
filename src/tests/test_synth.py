# tests/test_synth.py
from hal.pwm_driver import PWMDriver
from audio.synth import Synth
import time

pwm = PWMDriver(pin_num=16)
synth = Synth(pwm)

print("Test 1: Basic tone")
synth.note_on(69, velocity=0.5, duration_ms=500)  # expect A4

print("Test 2: Out of range pitch (expect error)")
try:
    synth.note_on(200)
except ValueError as e:
    print("PASS:", e)

print("Test 3: Velocity extremes")
synth.note_on(60, velocity=0.0, duration_ms=300)  # silent
synth.note_on(60, velocity=1.0, duration_ms=300)  # loud

print("Test 4: All notes off recovery")
synth.note_on(64, velocity=0.5)
time.sleep_ms(200)
synth.all_notes_off()
print("PASS: stopped safely")

print("All synth tests complete.")
