# main.py — Light Orchestra (No Buttons)
# LDR on GP28 (ADC2), Buzzer on GP16 (PWM)
# Behavior:
#   - JINGLE mode is primary: when brightness sits in a bin for HOLD_MS, play that bin's jingle.
#   - When light is moving fast (wiggling), briefly play a continuous pitch for immediate feedback.

from machine import Pin, ADC, PWM
import time

# ---------- Pins ----------
ADC_PIN = 28           # GP28 = ADC2
PWM_PIN = 16           # GP16 -> buzzer +

ldr = ADC(ADC_PIN)
buz = PWM(Pin(PWM_PIN))

# ---------- Audio settings ----------
DUTY = 30000           # 0..65535 (~46%)
MIN_F, MAX_F = 200, 1800
ALPHA = 0.15           # smoothing for brightness (0..1)
buz.duty_u16(0)

# ---------- Jingle logic ----------
HOLD_MS = 350          # must remain in bin this long to trigger the jingle
HYST = 0.04            # hysteresis around bin boundaries to reduce flutter

# When the light is moving quickly, play continuous tone for responsiveness
CONTINUOUS_WHEN_MOVING = True
MOTION_WINDOW = 20     # samples (~200 ms at 10 ms loop)
MOTION_THRESH = 0.06   # avg |delta| over window above this => "moving"

# ---------- Helpers ----------
def map_exp(z: float) -> int:
    """Nonlinear map 0..1 -> MIN_F..MAX_F (sounds more natural)."""
    return int(MIN_F + (MAX_F - MIN_F) * (z ** 1.8))

def set_tone(freq: int, duty=DUTY):
    buz.freq(int(freq))
    buz.duty_u16(duty)

def silence():
    buz.duty_u16(0)

def hz(note_name: str) -> int:
    TABLE = {
        'C4': 262, 'D4': 294, 'E4': 330, 'F4': 349, 'G4': 392,
        'A4': 440, 'B4': 494, 'C5': 523, 'E5': 659, 'G5': 784, 'A5': 880
    }
    return TABLE.get(note_name, 440)

# Jingle sequences: list of (frequency_Hz, duration_ms, gap_ms_after)
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

# Brightness bins: val in [0..1], lower->darker, higher->brighter (we invert sensor below)
BINS = [
    (0.00, 0.25, JINGLE_LOW,   "LOW"),
    (0.25, 0.55, JINGLE_MID,   "MID"),
    (0.55, 0.85, JINGLE_HIGH,  "HIGH"),
    (0.85, 1.01, JINGLE_SUPER, "SUPER"),
]

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
    """Blocking jingle playback (short)."""
    for f, dur, gap in seq:
        set_tone(f)
        t_end = time.ticks_add(time.ticks_ms(), dur)
        while time.ticks_diff(t_end, time.ticks_ms()) > 0:
            time.sleep_ms(2)
        silence()
        time.sleep_ms(gap)

# ---------- Main loop ----------
print("JINGLE mode active (no buttons). Wiggle light = continuous tone; hold steady = jingle.")

smooth = None
CUR_BIN = None
ENTER_TIME = None

# for motion detection
hist = [0.0] * MOTION_WINDOW
hist_i = 0
avg_motion = 0.0
last_smooth = None
last_print = time.ticks_ms()

while True:
    # Sensor read (invert so brighter -> larger)
    raw = ldr.read_u16()              # 0..65535 ; higher = darker with this wiring
    norm = raw / 65535.0
    val = 1.0 - norm                  # 0..1, brighter -> higher
    smooth = val if smooth is None else (ALPHA * val + (1 - ALPHA) * smooth)

    # Motion metric (avg |delta| over the last MOTION_WINDOW samples)
    if last_smooth is None:
        delta = 0.0
    else:
        delta = abs(smooth - last_smooth)
    last_smooth = smooth
    avg_motion += (delta - hist[hist_i]) / MOTION_WINDOW
    hist[hist_i] = delta
    hist_i = (hist_i + 1) % MOTION_WINDOW

    # If moving a lot, give immediate audio feedback via continuous tone
    if CONTINUOUS_WHEN_MOVING and avg_motion > MOTION_THRESH:
        set_tone(map_exp(smooth))
        # Reset jingle hold timer so we don't accidentally trigger during motion
        ENTER_TIME = time.ticks_ms()
    else:
        # Jingle mode (primary): trigger on bin entry after HOLD_MS
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
                    ENTER_TIME = time.ticks_ms()  # avoid immediate retrigger
        # Keep quiet between jingles so it feels snappy
        silence()

    # Telemetry every ~0.6s (handy for tuning)
    if time.ticks_diff(time.ticks_ms(), last_print) > 600:
        print(f"raw={raw} val={val:.2f} smooth={smooth:.2f} motion={avg_motion:.3f}")
        last_print = time.ticks_ms()

    time.sleep_ms(10)

