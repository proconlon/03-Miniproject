# hal/pwm_driver.py
from machine import Pin, PWM

class PWMDriver:
    def __init__(self, pin_num=16):
        self.pin = Pin(pin_num)
        self.pwm = PWM(self.pin)
        self.pwm.deinit()  # idle

    def set_freq(self, hz: float):
        hz = max(20, min(10000, int(hz)))  # clamp
        self.pwm.freq(hz)

    def set_duty(self, duty_0_1: float):
        duty_u16 = max(0, min(65535, int(duty_0_1 * 65535)))
        self.pwm.duty_u16(duty_u16)

    def stop(self):
        self.pwm.duty_u16(0)
