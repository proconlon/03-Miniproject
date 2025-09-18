# main.py
from hal.pwm_driver import PWMDriver
from audio.synth import Synth
import time
import machine

PHOTO_PIN = 28
DEBOUNCE_DELAY_MS = 250 # debouncer for "taps" for mode switching
THRESHOLD = 30000 # should be sufficiently dark that it simulates putting your finger over the sensor to totally black out.
NUM_MODES = 3 

# global debouncer vars
debounce_timer = 0
tap_count = 0
current_mode = 0

# init hw
photoresistor = machine.ADC(PHOTO_PIN)
pwm_driver = PWMDriver(pin_num=16)
synth = Synth(pwm_driver)

def double_tap_debounce():
    """
    A "double-tap" is defined as two quick moments of darkness DEBOUNCE_DELAY_MS apart.
    Return true if a double-tap is detected
    """
    # ref the globals
    global tap_count, debounce_timer
    
    light_value = photoresistor.read_u16()
    current_time_ms = time.ticks_ms()
    
    if light_value < THRESHOLD:
        if time.ticks_diff(current_time_ms, debounce_timer) > DEBOUNCE_DELAY_MS:
            if tap_count == 0:
                print("First tap detected!")
                tap_count = 1
                debounce_timer = current_time_ms
            elif tap_count == 1:
                print("Second tap detected!")
                tap_count = 0
                return True
                
    if tap_count == 1 and time.ticks_diff(current_time_ms, debounce_timer) > DEBOUNCE_DELAY_MS:
        print("Tap window expired, resetting.")
        tap_count = 0
        
    return False

def play_melody_1():
    print("Mode 1: Playing Melody 1...")
    melody = [(60, 300), (62, 300), (64, 300), (65, 600)]  # C D E F
    for pitch, dur in melody:
        synth.note_on(pitch, velocity=0.7, duration_ms=dur)
        time.sleep_ms(50)  # gap

def play_melody_2():
    print("Mode 2: Playing Melody 2...")
    melody = [(76, 300), (74, 300), (72, 300), (71, 600)]  # F E D C (up an octave)
    for pitch, dur in melody:
        synth.note_on(pitch, velocity=0.7, duration_ms=dur)
        time.sleep_ms(50)

def silent_mode():
    print("Mode 0: Silence.")
    synth.all_notes_off()


def switch_mode():
    global current_mode
    current_mode = (current_mode + 1) % NUM_MODES
    print(f"Mode switched to: {current_mode}")
    return current_mode


def demo():
    print("Modes are: 0=Silent, 1=Melody_1, 2=Melody_2.")
    print("Waiting for a double-tap on the photo sensor...")

    while True:
        if double_tap_debounce():
            mode = switch_mode()
            
            if mode == 0:
                silent_mode()
            elif mode == 1:
                play_melody_1()
            elif mode == 2:
                play_melody_2()
            
            time.sleep_ms(500) # some delay to avoid immediate rebounce
        
        # more sleeps for fun and safety
        time.sleep_ms(100)
if __name__ == "__main__":
    demo()
