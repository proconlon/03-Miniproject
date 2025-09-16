# audio/synth.py
import time

class Synth:
    def __init__(self, pwm_driver, *, master_vol=0.6):
        self.pwm = pwm_driver
        self.master = master_vol
        self.active = None  # track current note

    @staticmethod
    def midi_to_hz(pitch: int) -> float:
        return 440.0 * (2 ** ((pitch - 69) / 12))

    def note_on(self, pitch: int, velocity=1.0, duration_ms=None):
        if pitch < 0 or pitch > 127:
            raise ValueError("pitch out of range")
        if not (0.0 <= velocity <= 1.0):
            raise ValueError("velocity out of range")

        freq = self.midi_to_hz(pitch)
        self.pwm.set_freq(freq)
        self.pwm.set_duty(velocity * self.master)
        self.active = pitch

        if duration_ms:
            time.sleep_ms(duration_ms)
            self.note_off()

    def note_off(self, pitch=None):
        if pitch is None or pitch == self.active:
            self.pwm.stop()
            self.active = None

    def all_notes_off(self):
        self.pwm.stop()
        self.active = None
