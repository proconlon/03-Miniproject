from machine import Pin, PWM
import time

def setup_rgb_pins(r_pin, g_pin, b_pin, freq=PWM_FREQ):
  """
  Initialize PWM channels for RGB pins.
  """
  r = PWM(Pin(r_pin))
  g = PWM(Pin(g_pin))
  b = PWM(Pin(b_pin))
  
  for ch in (r, g, b):
      ch.freq(freq)

  return {"r": r, "g": g, "b": b}

def apply_pwm(pwm_channel, brightness_0_255: int):
  """
  Set PWM duty based on brightness (0-255). Converts to 16-bit range.
  """
  brightness_0_255 = max(0, min(255, brightness_0_255)) # Clamp
  if COMMON_ANODE:
  brightness_0_255 = 255 - brightness_0_255 # Invert for common anode
  duty_u16 = int((brightness_0_255 / 255) * 65535)
  pwm_channel.duty_u16(duty_u16)
  
  def set_rgb(pwms: dict, r: int, g: int, b: int):
  """
  Apply RGB values to PWM pins.
  """
  apply_pwm(pwms["r"], r)
  apply_pwm(pwms["g"], g)
  apply_pwm(pwms["b"], b)
  
  def light_to_rgb(input_val: int) -> tuple[int, int, int]:
  """
  Map input_val (0-5000) to RGB color.
  5000 = Red, 2500 = Green, 0 = Blue
  """
  input_val = max(0, min(5000, input_val)) # Clamp

  if input_val >= 2500:
      # Red to Green
      t = (input_val - 2500) / 2500  # 0 at 2500 → 1 at 5000
      r = int(255 * t)
      g = int(255 * (1 - t))
      b = 0
  else:
      # Green to Blue
      t = input_val / 2500  # 0 at 0 → 1 at 2500
      r = 0
      g = int(255 * t)
      b = int(255 * (1 - t))
  
  return r, g, b

def update_led_from_input(pwms, input_val: int):
  """
  Convert input to RGB and apply to LED.
  """
  try:
  r, g, b = light_to_rgb(input_val)
  set_rgb(pwms, r, g, b)
  print(f"Input: {input_val} → RGB({r},{g},{b})")
  except Exception as e:
  print(f"Error updating LED: {e}")
  set_rgb(pwms, 0, 0, 0) # Turn off LED on error
