/*
  CosmicWatch Desktop Muon Detector Arduino Code

  This code does not use the microSD card reader/writer, but does used the OLED screen.
  
  Questions?
  Spencer N. Axani
  saxani@mit.edu

  Requirements: Sketch->Include->Manage Libraries:
  SPI, EEPROM, SD, and Wire are probably already installed.
  1. Adafruit SSD1306     -- by Adafruit Version 1.0.1
  2. Adafruit GFX Library -- by Adafruit Version 1.0.2
  3. TimerOne             -- by Jesse Tane et al. Version 1.1.0
*/

#include <Adafruit_SSD1306.h>
#include <Adafruit_GFX.h>
#include <TimerOne.h>
#include <Wire.h>
#include <SPI.h>
#include <EEPROM.h>

const byte OLED = 1;                      // Turn on/off the OLED [1,0]

const int SIGNAL_THRESHOLD      = 50;    // Min threshold to trigger on. See calibration.pdf for conversion to mV.
const int RESET_THRESHOLD       = 25;    

const int LED_BRIGHTNESS        = 255;    // Brightness of the LED [0,255]

const long double cal[] = {-9.085681659276021e-27, 4.6790804314609205e-23, -1.0317125207013292e-19,
  1.2741066484319192e-16, -9.684460759517656e-14, 4.6937937442284284e-11, -1.4553498837275352e-08,
   2.8216624998078298e-06, -0.000323032620672037, 0.019538631135788468, -0.3774384056850066, 12.324891083404246};
   
const int cal_max = 1023;

//INTERUPT SETUP
#define TIMER_INTERVAL 1000000          // Every 1,000,000 us the timer will update the OLED readout

//OLED SETUP
#define OLED_RESET 10
Adafruit_SSD1306 display(OLED_RESET);

//initialize variables
char detector_name[40];

unsigned long time_stamp                      = 0L;
unsigned long measurement_deadtime            = 0L;
unsigned long time_measurement                = 0L;      // Time stamp
unsigned long interrupt_timer                 = 0L;      // Time stamp
int start_time                                = 0L;      // Reference time for all the time measurements
unsigned long total_deadtime                  = 0L;      // total measured deadtime
unsigned long waiting_t1                      = 0L;
unsigned long measurement_t1;
unsigned long measurement_t2;

float sipm_voltage                            = 0;
long int count                                = 0L;      // A tally of the number of muon counts observed
float last_sipm_voltage                       = 0;
float temperatureC;

byte waiting_for_interupt                     = 0;
byte SLAVE;
byte MASTER;
byte keep_pulse                               = 0;

void setup() {
  analogReference (EXTERNAL);
  ADCSRA &= ~(bit (ADPS0) | bit (ADPS1) | bit (ADPS2));  // clear prescaler bits
  ADCSRA |= bit (ADPS0) | bit (ADPS1);                   // Set prescaler to 8
  Serial.begin(9600);
  
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);                               
  pinMode(3, OUTPUT);
  pinMode(6, INPUT);
  if (digitalRead(6) == HIGH) {
      SLAVE = 1;
      MASTER = 0;
      digitalWrite(3,HIGH);
      delay(1000);}

  else{
      delay(10);
      MASTER = 1;
      SLAVE = 0;
      pinMode(6, OUTPUT);
      digitalWrite(6, HIGH);}

  if (OLED == 1){
      display.setRotation(2);         // Upside down screen (0 is right-side-up)
      OpeningScreen();                // Run the splash screen on start-up
      delay(2000);                    // Delay some time to show the logo, and keep the Pin6 HIGH for coincidence
      display.setTextSize(1);}

  else {delay(2000);}
  digitalWrite(3,LOW);
  if (MASTER == 1) {digitalWrite(6, LOW);}

  Serial.println(F("##########################################################################################"));
  Serial.println(F("### CosmicWatch: The Desktop Muon Detector"));
  Serial.println(F("### Questions? saxani@mit.edu"));
  Serial.println(F("### Comp_date Comp_time Event Ardn_time[ms] ADC[0-1023] SiPM[mV] Deadtime[ms] Temp[C] Name"));
  Serial.println(F("##########################################################################################"));

  get_detector_name(detector_name);
  Serial.println(detector_name);
  get_time();
  delay(900);
  start_time = millis();
  
  Timer1.initialize(TIMER_INTERVAL);             // Initialise timer 1
  Timer1.attachInterrupt(timerIsr);              // attach the ISR routine
  
}

void loop()
{
  while (1){
    if (analogRead(A0) > SIGNAL_THRESHOLD){ 

      // Make a measurement of the pulse amplitude
      int adc = analogRead(A0);
      
      // If Master, send a signal to the Slave
      if (MASTER == 1) {
          digitalWrite(6, HIGH);
          count++;
          keep_pulse = 1;}

      // Wait for ~8us
      analogRead(A3);
      
      // If Slave, check for signal from Master
      
      if (SLAVE == 1){
          if (digitalRead(6) == HIGH){
              keep_pulse = 1;
              count++;}}  

      // Wait for ~8us
      analogRead(A3);

      // If Master, stop signalling the Slave
      if (MASTER == 1) {
          digitalWrite(6, LOW);}

      // Measure the temperature, voltage reference is currently set to 3.3V
      temperatureC = (((analogRead(A3)+analogRead(A3)+analogRead(A3))/3. * (3300./1024)) - 500.)/10. ;

      
      // Measure deadtime
      measurement_deadtime = total_deadtime;
      time_stamp = millis() - start_time;
      
      
      // If you are within 15 miliseconds away from updating the OLED screen, we'll let if finish 
      if((interrupt_timer + 1000 - millis()) < 15){ 
          waiting_t1 = millis();
          waiting_for_interupt = 1;
          delay(30);
          waiting_for_interupt = 0;}

      measurement_t1 = micros();
      
      if (MASTER == 1) {
          analogWrite(3, LED_BRIGHTNESS);
          sipm_voltage = get_sipm_voltage(adc);
          last_sipm_voltage = sipm_voltage; 
          Serial.println((String)count + " " + time_stamp+ " " + adc+ " " + sipm_voltage+ " " + measurement_deadtime+ " " + temperatureC);}
  
      if (SLAVE == 1) {
          if (keep_pulse == 1) {   
              analogWrite(3, LED_BRIGHTNESS);
              sipm_voltage = get_sipm_voltage(adc);
              last_sipm_voltage = sipm_voltage; 
              Serial.println((String)count + " " + time_stamp+ " " + adc+ " " + sipm_voltage + " " + measurement_deadtime+ " " + temperatureC);}}
      
      keep_pulse = 0;
      digitalWrite(3, LOW);
      while(analogRead(A0) > RESET_THRESHOLD){continue;}
      total_deadtime += (micros() - measurement_t1) / 1000.;}}
}

void timerIsr() 
{
  interrupts();
  interrupt_timer                       = millis();
  if (waiting_for_interupt == 1){
      total_deadtime += (millis() - waiting_t1);}
  waiting_for_interupt = 0;
  if (OLED == 1){
      get_time();}
}

void get_time() 
{
  unsigned long int OLED_t1             = micros();
  float count_average                   = 0;
  float count_std                       = 0;

  if (count > 0.) {
      count_average   = count / ((interrupt_timer - start_time - total_deadtime) / 1000.);
      count_std       = sqrt(count) / ((interrupt_timer - start_time - total_deadtime) / 1000.);}
  else {
      count_average   = 0;
      count_std       = 0;}
  
  display.setCursor(0, 0);
  display.clearDisplay();
  display.print(F("Total Count: "));
  display.println(count);
  display.print(F("Uptime: "));

  int minutes                 = ((interrupt_timer - start_time) / 1000 / 60) % 60;
  int seconds                 = ((interrupt_timer - start_time) / 1000) % 60;
  char min_char[4];
  char sec_char[4];
  
  sprintf(min_char, "%02d", minutes);
  sprintf(sec_char, "%02d", seconds);

  display.println((String) ((interrupt_timer - start_time) / 1000 / 3600) + ":" + min_char + ":" + sec_char);

  if (count == 0) {
    display.println("Hi, I'm "+(String)detector_name);
    }
      //if (MASTER == 1) {display.println(F("::---  MASTER   ---::"));}
      //if (SLAVE  == 1) {display.println(F("::---   SLAVE   ---::"));}}
      
  else{
      if (last_sipm_voltage > 180){
          display.print(F("===---- WOW! ----==="));}
      else{
            if (MASTER == 1) {display.print(F("M"));}
            if (SLAVE  == 1) {display.print(F("S"));}
            for (int i = 1; i <=  (last_sipm_voltage + 10) / 10; i++) {display.print(F("-"));}}
      display.println(F(""));}

  char tmp_average[4];
  char tmp_std[4];

  int decimals = 2;
  if (count_average < 10) {decimals = 3;}
  
  dtostrf(count_average, 1, decimals, tmp_average);
  dtostrf(count_std, 1, decimals, tmp_std);
   
  display.print(F("Rate: "));
  display.print((String)tmp_average);
  display.print(F("+/-"));
  display.println((String)tmp_std);
  display.display();
  
  total_deadtime                      += (micros() - OLED_t1 +73)/1000.;
}

void OpeningScreen(void) 
{
    display.setTextSize(2);
    display.setTextColor(WHITE);
    display.setCursor(8, 0);
    display.clearDisplay();
    display.print(F("Cosmic \n     Watch"));
    display.display();
    display.setTextSize(1);
    display.clearDisplay();
}


// This function converts the measured ADC value to a SiPM voltage via the calibration array
float get_sipm_voltage(float adc_value)
{
  float voltage = 0;
  for (int i = 0; i < (sizeof(cal)/sizeof(float)); i++) {
    voltage += cal[i] * pow(adc_value,(sizeof(cal)/sizeof(float)-i-1));
    }
    return voltage;
}

// This function reads the EEPROM to get the detector ID
boolean get_detector_name(char* det_name) 
{
    byte ch;                              // byte read from eeprom
    int bytesRead = 0;                    // number of bytes read so far
    ch = EEPROM.read(bytesRead);          // read next byte from eeprom
    det_name[bytesRead] = ch;               // store it into the user buffer
    bytesRead++;                          // increment byte counter

    while ( (ch != 0x00) && (bytesRead < 40) && ((bytesRead) <= 511) ) 
    {
        ch = EEPROM.read(bytesRead);
        det_name[bytesRead] = ch;           // store it into the user buffer
        bytesRead++;                      // increment byte counter
    }
    if ((ch != 0x00) && (bytesRead >= 1)) {det_name[bytesRead - 1] = 0;}
    return true;
}
