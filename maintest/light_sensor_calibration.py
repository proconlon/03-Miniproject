# This file is used to calibrate the "mode" brightness -- currently set to 30000
# So you should run and see what a normal brightness for a finger over the sensor looks like and modify the src/main.py THRESHOLD value accordingly.



from machine import Pin, ADC
import time

ADC_PIN = 28  # GP28 = ADC2

# --- hardware setup ---
ldr = ADC(ADC_PIN)

print("Reading photoresistor values...")
print("Cover the sensor to see the value drop.")
print("The value is from 0 to 65535, where a higher value is darker.")
print("---------------------------------------------------------------")

while True:
    # 1) read sensor
    raw_value = ldr.read_u16()
    
    # 2) print the raw value to the terminal
    print(f"Raw ADC Value: {raw_value}")
    
    # 3) add a small delay
    time.sleep_ms(200)