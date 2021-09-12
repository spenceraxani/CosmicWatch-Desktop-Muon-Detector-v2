#include <EEPROM.h>
const int EEPROM_MIN_ADDR = 0;
const int EEPROM_MAX_ADDR = 511;

// Set the name of your detector below and then upload the code to your detector. 
// This will write the name in the EEPROM of the Arduino (permanent until overwritten).
String det_name = "Leonardo";

boolean eeprom_is_addr_ok(int addr) {
return ((addr >= EEPROM_MIN_ADDR) && (addr <= EEPROM_MAX_ADDR));
}

boolean eeprom_write_bytes(int startAddr, const byte* array, int numBytes) {
int i;
if (!eeprom_is_addr_ok(startAddr) || !eeprom_is_addr_ok(startAddr + numBytes)) {
return false;
}
for (i = 0; i < numBytes; i++) {
EEPROM.write(startAddr + i, array[i]);
}
return true;
}

boolean eeprom_write_string(int addr, const char* string) {

int numBytes; 
numBytes = strlen(string) + 1;
return eeprom_write_bytes(addr, (const byte*)string, numBytes);
}

boolean eeprom_read_string(int addr, char* buffer, int bufSize) {
byte ch; // byte read from eeprom
int bytesRead; // number of bytes read so far
if (!eeprom_is_addr_ok(addr)) { // check start address
return false;
}

if (bufSize == 0) { // how can we store bytes in an empty buffer ?
return false;
}
// is there is room for the string terminator only, no reason to go further
if (bufSize == 1) {
buffer[0] = 0;
return true;
}

bytesRead = 0; // initialize byte counter
ch = EEPROM.read(addr + bytesRead); // read next byte from eeprom
buffer[bytesRead] = ch; // store it into the user buffer
bytesRead++; // increment byte counter

while ( (ch != 0x00) && (bytesRead < bufSize) && ((addr + bytesRead) <= EEPROM_MAX_ADDR) ) {
ch = EEPROM.read(addr + bytesRead);
buffer[bytesRead] = ch; // store it into the user buffer
bytesRead++; // increment byte counter
}
if ((ch != 0x00) && (bytesRead >= 1)) {
buffer[bytesRead - 1] = 0;
}
return true;
}

const int BUFSIZE = 40;
char buf[BUFSIZE];
 
char det_name_Char[BUFSIZE];

void setup()
{
Serial.begin(9600);
Serial.print("Writing the name of the detector to EEPROM: "); 
Serial.println(det_name); 
det_name.toCharArray(det_name_Char, BUFSIZE);
strcpy(buf, det_name_Char);
eeprom_write_string(0, buf);

Serial.print("Verifing the name of the detector: "); 
eeprom_read_string(0, buf, BUFSIZE);
Serial.println(buf);
}

void loop()
{

}
