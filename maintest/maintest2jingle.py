# main.py — Kid-friendly Light Orchestra
# LDR on GP28 (ADC2), Buzzer on GP16 (PWM), Mute on GP14, Mode on GP15
# Modes:
#   - Continuous: brightness -> pitch (theremin style)
#   - Jingle: entering a brightness range plays a short melody for that range

from machine import Pin, ADC, PWM
import time

# ---------- Pins ----------
ADC_PIN = 28           # GP28 = ADC2
PWM_PIN = 16           # GP16 -> buzzer +
BTN_MUTE_PIN = 14      # to GND (internal pull-up)
BTN_MODE_PIN = 15      # to GND (internal pull-up)

ldr = ADC(ADC_PIN)
buz = PWM(Pin(PWM_PIN))
btn_mute = Pin(BTN_MUTE_PIN, Pin.IN, Pin.PULL_UP)
btn_mode = Pin(BTN_MODE_PIN, Pin.IN, Pin.PULL_UP)

# ---------- Audio settings ----------
DUTY = 30000           # 0..65535 (~46%)
MIN_F, MAX_F = 200, 1800
ALPHA = 0.15           # smoothing factor (0..1)
buz.duty_u16(0)

# ---------- App state ----------
sound_on = True
jingle_mode = False    # False = continuous pitch, True = jingle by range
last_mute = 1
last_mode = 1
last_print = time.ticks_ms()
smooth = None

# ---------- Helpers ----------
def map_exp(z: float) -> int:
    """Nonlinear map 0..1 -> MIN_F..MAX_F (feels nicer)."""
    return int(MIN_F + (MAX_F - MIN_F) * (z ** 1.8))

def set_tone(freq: int, duty=DUTY):
    if sound_on:
        buz.freq(int(freq))
        buz.duty_u16(duty)
    else:
        buz.duty_u16(0)

def silence():
    buz.duty_u16(0)

def edge_pressed(pin: Pin, last: int) -> (bool, int):
    cur = pin.value()
    pressed = (cur == 0 and last == 1)
    if pressed:
        time.sleep_ms(20)  # debounce
    return pressed, cur

# ---------- Tiny note helpers (Hz) ----------
def hz(note_name: str) -> int:
    TABLE = {
        'C4': 262, 'D4': 294, 'E4': 330, 'F4': 349, 'G4': 392,
        'A4': 440, 'B4': 494, 'C5': 523, 'E5': 659, 'G5': 784, 'A5': 880
    }
    return TABLE.get(note_name, 440)

# ---------- Jingle sequences ----------
# Each jingle = list of (frequency_Hz, duration_ms, gap_ms_after)
JINGLE_LOW = [
    (hz('C4'), 180, 20), (hz('E4'), 180, 20),
    (hz('G4'), 300, 80), (hz('C5'), 350, 120)
]
JINGLE_MID = [
    (hz('E4'), 160, 10), (hz('F4'), 160, 10),
    (hz('G4'), 160, 10), (hz('A4'), 280, 60),
    (hz('G4'), 180, 20), (hz('E4'), 260, 80)
]
JINGLE_HIGH = [
    (hz('G4'), 150, 10), (hz('A4'), 150, 10),
    (hz('B4'), 150, 10), (hz('C5'), 300, 40),
    (hz('E5'), 300, 60)
]
JINGLE_SUPER = [
    (hz('C5'), 150, 10), (hz('E5'), 150, 10),
    (hz('G5'), 150, 10), (hz('C5'), 450, 140)
]

# Brightness bins: val in [0..1], lower->darker, higher->brighter
BINS = [
    (0.00, 0.25, JINGLE_LOW,   "LOW"),
    (0.25, 0.55, JINGLE_MID,   "MID"),
    (0.55, 0.85, JINGLE_HIGH,  "HIGH"),
    (0.85, 1.01, JINGLE_SUPER, "SUPER"),
]

CUR_BIN = None
ENTER_TIME = None
HOLD_MS = 350          # must remain in bin for this long to trigger
HYST = 0.04            # hysteresis buffer

def classify(value_01: float, cur_bin_idx):
    """Return new bin idx if value is in a bin (with hysteresis)."""
    for i, (lo, hi, *_rest) in enumerate(BINS):
        if cur_bin_idx == i:
            lo_h = max(0.0, lo - HYST)
            hi_h = min(1.0, hi + HYST)
        else:
            lo_h, hi_h = lo, hi
        if lo_h <= value_01 < hi_h:
            return i
    return None

def play_jingle(seq):
    """Blocking jingle playback with mute-check."""
    global last_mute, last_mode, jingle_mode, sound_on  # FIX: declare globals once at top
    if not sound_on:
        return
    for f, dur, gap in seq:
        if not sound_on:
            silence()
            return
        set_tone(f)
        t_end = time.ticks_add(time.ticks_ms(), dur)
        while time.ticks_diff(t_end, time.ticks_ms()) > 0:
            # allow mute/mode changes mid-note
            pressed, last_mute = edge_pressed(btn_mute, last_mute)
            if pressed:
                sound_on = not sound_on
                if not sound_on:
                    silence()
                    return
            pressed2, last_mode = edge_pressed(btn_mode, last_mode)
            if pressed2:
                jingle_mode = not jingle_mode
            time.sleep_ms(2)
        silence()
        time.sleep_ms(gap)

# ---------- Main loop ----------
print("Mode: Continuous (press Mode button to switch). Mute toggles sound.")

while True:
    # Buttons
    p, last_mute = edge_pressed(btn_mute, last_mute)
    if p:
        sound_on = not sound_on
        if not sound_on:
            silence()
        print("Mute:", not sound_on)

    p2, last_mode = edge_pressed(btn_mode, last_mode)
    if p2:
        jingle_mode = not jingle_mode
        print("Mode:", "JINGLE" if jingle_mode else "CONTINUOUS")

    # Sensor read
    raw = ldr.read_u16()
    norm = raw / 65535.0
    val = 1.0 - norm
    smooth = val if smooth is None else (ALPHA * val + (1 - ALPHA) * smooth)

    if not jingle_mode:
        # Continuous theremin-style
        set_tone(map_exp(smooth))
    else:
        # Jingle mode
        new_bin = classify(smooth, CUR_BIN)
        now = time.ticks_ms()
        if new_bin != CUR_BIN:
            CUR_BIN = new_bin
            ENTER_TIME = now
        else:
            if CUR_BIN is not None and ENTER_TIME is not None:
                if time.ticks_diff(now, ENTER_TIME) >= HOLD_MS:
                    _, _, seq, name = BINS[CUR_BIN]
                    print("Jingle:", name)
                    play_jingle(seq)
                    ENTER_TIME = time.ticks_ms()
        silence()  # quiet between jingles

    if time.ticks_diff(time.ticks_ms(), last_print) > 600:
        mode = "JINGLE" if jingle_mode else "CONTINUOUS"
        print(f"raw={raw} val={val:.2f} smooth={smooth:.2f} mode={mode} on={sound_on}")
        last_print = time.ticks_ms()

    time.sleep_ms(10)
