# main.py
from hal.pwm_driver import PWMDriver
from audio.synth import Synth
import time

def demo():
    pwm = PWMDriver(pin_num=16)  # adjust pin for your buzzer
    synth = Synth(pwm)

    melody = [(60, 300), (62, 300), (64, 300), (65, 600)]  # C D E F
    for pitch, dur in melody:
        synth.note_on(pitch, velocity=0.7, duration_ms=dur)
        time.sleep_ms(50)  # gap

if __name__ == "__main__":
    demo()
