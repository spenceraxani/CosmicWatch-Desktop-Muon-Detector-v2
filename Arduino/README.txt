CosmicWatch MIT Arduino code

CH34x_Install_V1.3_MAC.pkg is a driver, which I obtained from:
https://github.com/adrianmihalko/ch340g-ch34g-ch34x-mac-os-x-driver
The driver is needed for MACs to communicate with the Arduino Nano.

In order to use the code below, a few libraries must be installed.
	1. Adafruit ssd1306     -- Version 1.1.2
	2. Adafruit GFX Library -- Version 1.0.2
	3. TimerOne             -- Version 1.1.0
	4. SPI                  -- Version 1.0.0
	5. SD                   -- Version 1.0.9
	6. EEPROM               -- Version 2.0.0


Naming.ino:
	This code is used to name the detector. 
	Simply replace the det_name variable with your desired detector name and upload the code. 
	The name will be permanently written to the EEPROM, until this code is run again.

OLED.ino
	This is the code to run the OLED screen. 
	You can also use the coincidence connection on the back.
	It also works with a temperature sensor.

SDcard.ino
	This operates the same as the OLED.ino code. 
	Instead of running the OLED screen, we run the microSD card reader/writer. 
	We cannot run both the OLED and the microSd card reader/writer at the same time.
	This is due to the limited flash storage space and ram on the Arduino Nano.
