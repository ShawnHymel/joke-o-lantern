"""
Flickers LEDs and plays WAV file whenever D6 goes high.

Tested with CircuitPython v7.0.0 on Adafruit Feather M0 Express

Date: October 25, 2021
Author: Shawn Hymel
License: 0BSD
"""

import os
import time
import random

import board
from digitalio import DigitalInOut, Direction, Pull
import audioio
import audiocore

import neopixel

# Parameters
audio_dir = "audio"     # Name of directory where WAV files are stored
cooloff_time = 5        # seconds
num_pixels = 8          # Pixels in NeoPixel strip
neopixel_brightness = 0.8
neopixel_flicker_scaler = 0.3
flicker_delay_min = 0.01    # Seconds
flicker_delay_max = 0.100   # Seconds
flame_r = 226
flame_g = 121
flame_b = 35

# Pins
onboard_neopixel_pin = board.NEOPIXEL
status_led_pin = board.D13
neopixel_strip_pin = board.D9
trg_sensor_pin = board.D6
amp_shd_pin = board.D5
audio_out_pin = board.A0

# Onboard NeoPixel
led_rgb = neopixel.NeoPixel(onboard_neopixel_pin, 1)
led_rgb.brightness = 0.3
led_rgb[0] = (0, 0, 0)

# Status LEDs
status_led = DigitalInOut(status_led_pin)
status_led.direction = Direction.OUTPUT
status_led.value = False

# NeoPixel strip
pixels = neopixel.NeoPixel(neopixel_strip_pin, num_pixels, \
    brightness=neopixel_brightness, auto_write=False, pixel_order=neopixel.GRB)
for i in range(0, num_pixels):
    pixels[i] = (0, 0, 0)
pixels.show()

# Trigger pin
trg = DigitalInOut(trg_sensor_pin)
trg.direction = Direction.INPUT

# Audio amp shutdown control (leave on)
amp_shd = DigitalInOut(amp_shd_pin)
amp_shd.direction = Direction.OUTPUT
amp_shd.value = True

# List WAV files
audio_list = os.listdir(audio_dir)
print("Found files:", audio_list)

# Make sure that list only contains *.wav files
for f in audio_list:
    if f[-4:].upper() != ".WAV":
        audio_list.remove(f)
print("WAV files:", audio_list)

# Configure audio output pin
audio = audioio.AudioOut(audio_out_pin)

# Globals
trg_prev_state = False
audio_idx = 0

#-------------------------------------------------------------------------------
# Functions
#-------------------------------------------------------------------------------

# Credit to mysecretstache for flicker effect
# https://codebender.cc/sketch:271084#Neopixel%20Flames.ino
def NeoFlicker():

    for i in range(0, num_pixels):

        # Set flicker vlaues
        flicker = random.randint(0, 55)
        r = flame_r - flicker
        g = flame_g - flicker
        b = flame_b - flicker
        
        # Apply brightness multiplier
        r = int(neopixel_flicker_scaler * r)
        g = int(neopixel_flicker_scaler * g)
        b = int(neopixel_flicker_scaler * b)

        # Clamp values
        r = max(min(r, 255), 0)
        g = max(min(g, 255), 0)
        b = max(min(b, 255), 0)
        
        pixels[i] = (r, g, b)
        
    pixels.show()

# Set NeoPixel strip to one color
def SetNeoColor(r, g, b):
    for i in range(0, num_pixels):
        pixels[i] = (r, g, b)
    pixels.show()
    
# Flash color
def NeoFlash(r, g, b, time_ms, num):
    for n in range(num):
        SetNeoColor(r, g, b)
        time.sleep(time_ms)
        SetNeoColor(0, 0, 0)
        time.sleep(time_ms)

#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------

timestamp = time.monotonic()
while True:

    # Show trigger pin status on onboard NeoPixel
    if ( True == trg.value ):
        led_rgb[0] = (100, 0, 0)
    else:
        led_rgb[0] = (0, 0, 0)

    # See if we're outside our "cooling off" period
    if (time.monotonic() - timestamp >= cooloff_time):
    
        # Show that we're armed
        status_led.value = True
    
        # Determine if trigger pin has gone high
        trg_state = trg.value
        if (False == trg_prev_state) and (True == trg_state):
        
            # Reset cooling off timer and status LEDs
            timestamp = time.monotonic()
            status_led.value = False
            
            # Open audio clip and increment pointer
            audio_path = audio_dir + "/" + audio_list[audio_idx]
            audio_idx = (audio_idx + 1) % len(audio_list)
            with open(audio_path, 'rb') as file:
            
                # Play the clip
                wave = audiocore.WaveFile(file)
                print("Playing", audio_path)
                audio.play(wave)
                
                # Set everything to RED(RUM)
                SetNeoColor(255, 0, 0)
                
                # Wait for audio file to be done
                while audio.playing:
                    pass
                print("Done playing!")
            
        # Save state
        trg_prev_state = trg_state
    
    # Do flicker effect
    NeoFlicker()
    time.sleep(random.uniform(flicker_delay_min, flicker_delay_max))
    