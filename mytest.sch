EESchema Schematic File Version 2
LIBS:SBR002-201-FX-BRD-rescue
LIBS:power
LIBS:device
LIBS:switches
LIBS:relays
LIBS:motors
LIBS:transistors
LIBS:conn
LIBS:linear
LIBS:regul
LIBS:74xx
LIBS:cmos4000
LIBS:adc-dac
LIBS:memory
LIBS:xilinx
LIBS:microcontrollers
LIBS:dsp
LIBS:microchip
LIBS:analog_switches
LIBS:motorola
LIBS:texas
LIBS:intel
LIBS:audio
LIBS:interface
LIBS:digital-audio
LIBS:philips
LIBS:display
LIBS:cypress
LIBS:siliconi
LIBS:opto
LIBS:atmel
LIBS:contrib
LIBS:valves
LIBS:analog_devices
LIBS:si_labs
LIBS:texas_instruments
LIBS:power_manfang
LIBS:maxim
LIBS:winbond
LIBS:ESP32-footprints-Shem-Lib
LIBS:holes
LIBS:SBR002-201-FX-BRD-cache
EELAYER 25 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 6 6
Title "Accelerometer"
Date ""
Rev "A"
Comp "Saber Forge"
Comment1 "Bare PCB: SBR002-401"
Comment2 "Assembly: SBR002-201"
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L ADXL343 U6
U 1 1 5A44A0E2
P 5100 3750
F 0 "U6" H 4850 4100 50  0000 C CNN
F 1 "ADXL343" H 5350 2900 50  0000 C CNN
F 2 "lib_fp:ADI_CC-14-1" H 5100 3750 50  0001 C CNN
F 3 "http://www.analog.com/media/en/technical-documentation/data-sheets/ADXL343.pdf" H 5100 3750 50  0001 C CNN
F 4 "Analog Devices" H 5100 3750 60  0001 C CNN "Manufacturer"
F 5 "ADXL343BCCZ" H 5100 3750 60  0001 C CNN "Part Number"
F 6 "14-VFLGA" H 5100 3750 60  0001 C CNN "Package"
F 7 "Accelerometer X, Y, Z Axis ±2g, 4g, 8g, 16g 0.05Hz ~ 1.6kHz 14-LGA (3x5)" H 5100 3750 60  0001 C CNN "Description"
F 8 "~" H 5100 3750 60  0001 C CNN "Notes"
F 9 "~" H 5100 3750 60  0001 C CNN "fit_field"
F 10 "~" H 5100 3750 60  0001 C CNN "Alternate Part Number"
	1    5100 3750
	1    0    0    -1  
$EndComp
$Comp
L C C6
U 1 1 5A44A0F0
P 3900 3500
F 0 "C6" H 3925 3600 50  0000 L CNN
F 1 "4.7uF" H 3925 3400 50  0000 L CNN
F 2 "lib_fp:C_0402" H 3938 3350 50  0001 C CNN
F 3 "" H 3900 3500 50  0001 C CNN
F 4 "TDK" H 3900 3500 60  0001 C CNN "Manufacturer"
F 5 "C1005X5R1A475M050BC" H 3900 3500 60  0001 C CNN "Part Number"
F 6 "0402" H 4050 3200 60  0001 C CNN "Package"
F 7 "4.7uF, 10V, 0402, 20%, X5R" H 3900 3500 60  0001 C CNN "Description"
F 8 "or equivalent" H 3900 3500 60  0001 C CNN "Notes"
F 9 "~" H 3900 3500 60  0001 C CNN "fit_field"
F 10 "0402ZD475MAT2A" H 3900 3500 60  0001 C CNN "Alternate Part Number"
	1    3900 3500
	1    0    0    -1  
$EndComp
$Comp
L +2V7 #PWR065
U 1 1 5A44A0F7
P 3900 3300
F 0 "#PWR065" H 3900 3150 50  0001 C CNN
F 1 "+2V7" H 3900 3440 50  0000 C CNN
F 2 "" H 3900 3300 50  0001 C CNN
F 3 "" H 3900 3300 50  0001 C CNN
	1    3900 3300
	1    0    0    -1  
$EndComp
Wire Wire Line
	5500 3700 6150 3700
Wire Wire Line
	5500 3850 6150 3850
$Comp
L C C7
U 1 1 5A44A10C
P 4250 3500
F 0 "C7" H 4275 3600 50  0000 L CNN
F 1 "0.1uF" H 4275 3400 50  0000 L CNN
F 2 "lib_fp:C_0402" H 4288 3350 50  0001 C CNN
F 3 "" H 4250 3500 50  0001 C CNN
F 4 "AVX" H 4250 3500 60  0001 C CNN "Manufacturer"
F 5 "0402YC104KAT2A" H 4250 3500 60  0001 C CNN "Part Number"
F 6 "0402" H 4250 3500 60  0001 C CNN "Package"
F 7 "0.1uF 16V 0402 10% X7R" H 4250 3500 60  0001 C CNN "Description"
F 8 "or equivalent" H 4250 3500 60  0001 C CNN "Notes"
F 9 "~" H 4250 3500 60  0001 C CNN "fit_field"
F 10 "~" H 4250 3500 60  0001 C CNN "Alternate Part Number"
	1    4250 3500
	1    0    0    -1  
$EndComp
Wire Wire Line
	3900 3650 3900 3700
Wire Wire Line
	4250 3650 4250 3700
Wire Wire Line
	3900 3300 3900 3350
Wire Wire Line
	4600 3700 4700 3700
Wire Wire Line
	4600 3350 4600 3700
Wire Wire Line
	4700 3550 4600 3550
Connection ~ 4600 3550
$Comp
L GND #PWR066
U 1 1 5A44A124
P 5650 4600
F 0 "#PWR066" H 5650 4350 50  0001 C CNN
F 1 "GND" H 5650 4450 50  0000 C CNN
F 2 "" H 5650 4600 50  0001 C CNN
F 3 "" H 5650 4600 50  0001 C CNN
	1    5650 4600
	1    0    0    -1  
$EndComp
Wire Wire Line
	5500 4000 5650 4000
Wire Wire Line
	5650 4000 5650 4600
Text Notes 4950 3250 0    60   ~ 0
ADDR: 0x53
Text HLabel 6150 3700 2    60   Input ~ 0
XL_CLK
Text HLabel 6150 3850 2    60   BiDi ~ 0
XL_DATA
Text HLabel 6150 4300 2    60   Output ~ 0
INT1
Text HLabel 6150 4450 2    60   Output ~ 0
INT2
Wire Wire Line
	5500 4300 6150 4300
Wire Wire Line
	5500 4450 6150 4450
Wire Wire Line
	4700 4150 4600 4150
Wire Wire Line
	4600 4150 4600 4600
Wire Wire Line
	4700 4300 4600 4300
Connection ~ 4600 4300
Wire Wire Line
	4700 4450 4600 4450
Connection ~ 4600 4450
$Comp
L GND #PWR067
U 1 1 5A45E8CE
P 4600 4600
F 0 "#PWR067" H 4600 4350 50  0001 C CNN
F 1 "GND" H 4600 4450 50  0000 C CNN
F 2 "" H 4600 4600 50  0001 C CNN
F 3 "" H 4600 4600 50  0001 C CNN
	1    4600 4600
	1    0    0    -1  
$EndComp
$Comp
L GND #PWR068
U 1 1 5A45E909
P 4250 3700
F 0 "#PWR068" H 4250 3450 50  0001 C CNN
F 1 "GND" H 4250 3550 50  0000 C CNN
F 2 "" H 4250 3700 50  0001 C CNN
F 3 "" H 4250 3700 50  0001 C CNN
	1    4250 3700
	1    0    0    -1  
$EndComp
$Comp
L GND #PWR069
U 1 1 5A45E91D
P 3900 3700
F 0 "#PWR069" H 3900 3450 50  0001 C CNN
F 1 "GND" H 3900 3550 50  0000 C CNN
F 2 "" H 3900 3700 50  0001 C CNN
F 3 "" H 3900 3700 50  0001 C CNN
	1    3900 3700
	1    0    0    -1  
$EndComp
Wire Wire Line
	3900 3350 4600 3350
Connection ~ 4250 3350
Text HLabel 6150 3550 2    60   Input ~ 0
XL_CS
Wire Wire Line
	5500 3550 6150 3550
$EndSCHEMATC
