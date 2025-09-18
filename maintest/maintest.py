# main.py — Light → Tone (simple & simultaneous)
# Pins: LDR on GP28 (ADC2), Buzzer on GP16 (PWM), optional mute button on GP14→GND

from machine import Pin, ADC, PWM
import time

# --- pin config ---
ADC_PIN = 28          # GP28 = ADC2
PWM_PIN = 16          # GP16 → buzzer +
BTN_MUTE_PIN = 14     # button to GND (internal pull-up)

ldr = ADC(ADC_PIN)
buz = PWM(Pin(PWM_PIN))
btn = Pin(BTN_MUTE_PIN, Pin.IN, Pin.PULL_UP)

# --- tone config (tweak these if you like) ---
MIN_F = 200           # lowest pitch (Hz)
MAX_F = 1800          # highest pitch (Hz)
DUTY  = 30000         # loudness (0..65535) — keep in range
ALPHA = 0.15          # smoothing (0..1), higher = more responsive

buz.duty_u16(0)       # start silent
sound_on = True
smooth = None
last_btn = 1
last_print = time.ticks_ms()

def map_exp(z: float) -> int:
    """nonlinear map 0..1 -> MIN_F..MAX_F (feels nicer to the ear)"""
    return int(MIN_F + (MAX_F - MIN_F) * (z ** 1.8))

while True:
    # 1) read sensor
    raw = ldr.read_u16()              # 0..65535, higher = darker with this wiring
    norm = raw / 65535.0              # 0..1
    val  = 1.0 - norm                 # invert so BRIGHTER = HIGHER pitch

    # 2) smooth it a bit so pitch isn't jittery
    smooth = val if smooth is None else (ALPHA * val + (1 - ALPHA) * smooth)

    # 3) map to frequency and play
    freq = map_exp(smooth)
    if sound_on:
        buz.freq(freq)
        buz.duty_u16(DUTY)
    else:
        buz.duty_u16(0)

    # 4) mute button (edge-detected, simple debounce)
    cur = btn.value()
    if cur == 0 and last_btn == 1:    # pressed
        sound_on = not sound_on
        if not sound_on:
            buz.duty_u16(0)
        time.sleep_ms(20)             # debounce
    last_btn = cur

    # 5) lightweight telemetry (every ~0.5 s)
    if time.ticks_diff(time.ticks_ms(), last_print) > 500:
        print(f"raw={raw} norm={norm:.2f} val={val:.2f} f={freq}Hz on={sound_on}")
        last_print = time.ticks_ms()

    # keep sleep >= 0 (negative sleeps are undefined in MicroPython)
    time.sleep_ms(10)
