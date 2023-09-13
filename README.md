# Smart Home Automation System (SHAS)

[![badge](https://img.shields.io/badge/license-MIT-success.svg)](https://opensource.org/license/mit)
[![badge](https://img.shields.io/badge/support-PayPal-blue.svg)](https://paypal.me/d4li3n)
[![badge](https://img.shields.io/badge/publication-danielthecyberdude.com-purple.svg)](https://danielthecyberdude.com/project/shas)


![badge](https://img.shields.io/badge/technology-C/C++-green.svg)
![badge](https://img.shields.io/badge/technology-Python-green.svg)
![badge](https://img.shields.io/badge/technology-Arduino-green.svg)
![badge](https://img.shields.io/badge/technology-ThingSpeak-green.svg)


![header image](https://github.com/D4LI3N/SHAS/blob/master/SHAS-Documentation/x.png?raw=true)



**Smart Home Automation System (SHAS)** is an innovative project designed to provide homeowners with convenient remote control over sensors and devices in their homes. It utilizes a diverse range of channels and devices to deliver flexible and efficient control capabilities.

Although currently showcased on a breadboard for demonstration purposes, with minimal modifications or even in its current state, SHAS has the potential to be effectively implemented in real-world scenarios.

# Project Features
- Control through four potential channels: physical button, Email, serial, and any device with a web browser, with smartphones being the most convenient option.
- Cloud data backups and analytics for temperature, luminosity, and intruder detection, facilitated by the ThingSpeak analytics platform.
- Real-time control, responses, and access to historical data.
- Five operational modes:
    - AC Mode: Controls the operation of the air conditioning system.

    - Light Auto Mode: Automatically adjusts the lighting based on ambient conditions or programmed settings.

    - Home Secure Mode: Enhances home security by activating various monitoring and alert systems.

    - Emergency Mode: Activates predefined emergency protocols to ensure safety and provide immediate assistance in critical situations.

- Features a simple and intuitive command syntax using "SET/GET" commands.

# Operation
## Setup:
- Configure the AP settings of the devices.
- Connect the devices to a power supply (5VDC).
- Optional: Configure dynamic DNS on a router to enable control of SHAS from outside the home network.

## Usage:
After booting,

- If the device is not connected to the configured WiFi AP (home router), it can only be controlled:
    - physically.

- If the device is connected to the configured WiFi AP (home router), it can only be controlled:
    - physically

    - through a web UI

- If the device is connected to the configured WiFi AP (home router) and a computer, it can only be controlled:
    - physically

    - through a web UI

    - through the serial channel

- If the device is connected to the configured WiFi AP (home router) and a computer running the expansion script with internet access, it can only be controlled:
    - physically

    - through a web UI

    - through the serial channel

    - via email

# Technology Overview
## Software:
- C/C++
- Python
- Arduino
- ThingSpeak

## Hardware:
- Heltec WIFI LoRa 32 (ESP32 based MCU)
- PIR sensor (HC-SR501)
- Resistor (220 Ω)
- Temperature sensor (LM35)
- Illumination sensor (GL5528 photoresistor)
- DC motor (5VDC)
- Relay (5VDC10A)
- LED (DIP)
- Breadboard and wires
