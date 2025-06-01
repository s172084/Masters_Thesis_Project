/*
 * @author 
 */
 
byte j;
int y = 0;
int i = 0;
char val;
byte direc = 2;
int freq_gap = 91;
int startX = 0;
int startY = 0;
int gap = 0;
int point = 256;

char inputfx[4];
char tempfx;
byte maxDigitfx = 3;
int maxfx = 255;

char inputfy[4];
char tempfy;
byte maxDigitfy = 3;
int maxfy = 255;

char inputgap[4];
char tempgap;
byte maxDigitgap = 3;
int maxgap = 128;

char inputpoint[6];
char temppoint;
byte maxDigitpoint = 5;
int maxpoint = 11;

int con;

float sf = 100000;

int fes[256];
int color;
int fes_stop;
int fes_signal;

int delay_time = 1400;

void setup() {
  DDRL = B11111111; //Digital pin 49~42 x
  DDRC = B11111111; //Digital pin 37~30 y
  pinMode(A0, INPUT);
  PORTL = 0;
  PORTC = 0;
  Serial.begin(115200);
}

void loop() {
  if (Serial.available()){
    val = Serial.read();
    
    switch(val) {
      case 'p' :
         j = 0; //count reset;
        while ((temppoint = Serial.read()) != '\n') {
          if (temppoint >= '0' && temppoint <= '9' && j < maxDigitpoint) { 
            inputpoint[j] = temppoint;
            j++;
          }
        }
        inputpoint[j] = '\0';
        delay_time = atoi(inputpoint); 
        
        /**************************************************
        Optimized Values for 256x256:

        Line Rate 0.8 Hz => delay_time = 1000 (Fastest)
        Line Rate 0.6 Hz => delay_time = 1400
        Line Rate 0.4 Hz => delay_time = 4700
        Line Rate 0.2 Hz => delay_time = 14000
        **************************************************/
        break;
        
      case 'x' :
         j = 0; //count reset;
        while ((tempfx = Serial.read()) != '\n') {
          if (tempfx >= '0' && tempfx <= '9' && j < maxDigitfx) { 
            inputfx[j] = tempfx;
            j++;
          }
        }
        inputfx[j] = '\0';
        startX = atoi(inputfx); 
        if (startX > maxfx) startX = maxfx;
        break;
         
      case 'y' :
         j = 0; //count reset;
        while ((tempfy = Serial.read()) != '\n') {
          if (tempfy >= '0' && tempfy <= '9' && j < maxDigitfy) { 
            inputfy[j] = tempfy;
            j++;
          }
        }
        inputfy[j] = '\0';
        startY = atoi(inputfy); 
        if (startY > maxfy) startY = maxfy;
         break;

      case 'g' :
         j = 0; //count reset;
        while ((tempgap = Serial.read()) != '\n') {
          if (tempgap >= '0' && tempgap <= '9' && j < maxDigitgap) { 
            inputgap[j] = tempgap;
            j++;
          }
        }
        inputgap[j] = '\0';
        gap = atoi(inputgap); 
        if (gap > maxgap) gap = maxgap;
         break;

      case 'u':
        direc = 0;
        break;
      case 'e':
        direc = 2;
        PORTL = 0;
        PORTC = 0;
        break;
    }
    if (direc == 0){
      Serial.print('a');
    }
  }
    if (direc == 0){
      // Set Y position
      PORTC = startY;
      delay(1);
      
      // Scan line left to right
      for (i = 0; i < 256; i++){
        PORTL = i;
        delayMicroseconds(delay_time);
        fes[i] = analogRead(A0);
      }
      
      // Move to next line
      startY += gap;
      
      // Send data immediately after each line
      for (i = 0; i < 256; i++){
        Serial.println(fes[i]);
        delayMicroseconds(50);  // Reduced delay for faster data transmission
      }
    }
    else {
      fes_signal = analogRead(A0);
      Serial.println(fes_signal);
      delay(10);
    }
}
