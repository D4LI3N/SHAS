#include <WiFi.h>
#include <WiFiClient.h>
#include <WebServer.h>
#include "HT_SSD1306Wire.h"

// PINS (9)
#define PIN_BUTTON 39
#define PIN_PIR 25

#define PIN_FRESISTOR 34
#define PIN_TEMP 35

#define PIN_COOLER 12
#define PIN_HEATER 13

#define PIN_LIGHTS 21
#define PIN_RED 2
#define PIN_GREEN 23

// btn
int btnLastState = HIGH; // the previous state from the input pin
int btnCurrentState;     // the current reading from the input pin
// PIR
volatile int MOVE;       // 1 when move has been detected
// photoresistor
volatile int LUX;        // lumens, min value = 0, max value = 4095
// OLED
SSD1306Wire  display(0x3c, 500000, SDA_OLED, SCL_OLED, GEOMETRY_128_64, RST_OLED);
float progress;
int FPS=0;
// LM35
#define ADC_VREF_mV    3300.0 // in millivolt
#define ADC_RESOLUTION 4096.0
float milliVolt;
int adcVal;
volatile int TEMP;
// serial
String  inputString;
int     inputState;
// modes
boolean auto_ac_mode = true;
boolean light_auto_mode = false;
boolean home_secure_mode = false;
boolean emergency_mode = false;
// wifi
const char* ssid = "";          // Define AP's SSID
const char* password = "";      // Define AP's Password
IPAddress ipAddress(192, 168, 1, 123);  // Define IP address
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);
WebServer server(80);
String connectedIP = "N\\A";
// other
int counter;
boolean first_run=true;
char *token;
String receivedText;
String returnedText;
String splitArray[3];
int i = 0;



//functions
void checkBtn(){
 /*
 * Function: checkBtn
 * ----------------------------
 *   Checks for button click
 */
  btnCurrentState = digitalRead(PIN_BUTTON);
  if(btnLastState == LOW && btnCurrentState == HIGH){
    emergency_mode=1;
    Serial.println("[!] Button pressed!");
  }
  btnLastState = btnCurrentState;
 }



void pinSetup(){
 /*
 * Function: pinSetup
 * ----------------------------
 *   Setting the pins I/O modes
 */
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  pinMode(PIN_PIR, INPUT_PULLUP); //attachInterrupt(digitalPinToInterrupt(PIN_PIR), pirMovement, RISING);
  //pinMode(PIN_FRESISTOR, INPUT);//not needed for analogRead()
  //pinMode(PIN_TEMP, INPUT);//not needed for analogRead()
  pinMode(PIN_HEATER, OUTPUT);
  pinMode(PIN_COOLER, OUTPUT);
  pinMode(PIN_LIGHTS, OUTPUT);
  pinMode(PIN_GREEN, OUTPUT);
  pinMode(PIN_RED, OUTPUT);
}

void setAC(int x){ 
 /*
 * Function: setAC
 * ----------------------------
 *   Air condition system control
 *   
 *   x: 0 = OFF, 1 = COOLING, 2 = HEATING
 */
  switch(x){
    case 1: // COOLING
      digitalWrite(PIN_COOLER,HIGH);
      digitalWrite(PIN_HEATER,LOW);
      break;
    case 2: // HEATING
      digitalWrite(PIN_COOLER,LOW);
      digitalWrite(PIN_HEATER,HIGH);
      break;
    default: // 0
      digitalWrite(PIN_COOLER,LOW);
      digitalWrite(PIN_HEATER,LOW);
      break;
  }
}



void updateTemp(){
 /*
 * Function: updateTemp
 * ----------------------------
 *   Updates the TEMP variable
 */
  adcVal = analogRead(PIN_TEMP);
  // convert the ADC value to voltage in millivolt
  milliVolt = adcVal * (ADC_VREF_mV / ADC_RESOLUTION);
  // convert the voltage to the temperature in °C
  TEMP = milliVolt / 10;
}

void updateLux(){
 /*
 * Function: updateLux
 * ----------------------------
 *   Updates the LUX variable
 */
  LUX = analogRead(PIN_FRESISTOR);
}

void updatePIR() {
 /*
 * Function: updatePIR
 * ----------------------------
 *   Updates the MOVE variable
 */
  if(digitalRead(PIN_PIR)==HIGH){
    MOVE=1;
  }
}

void checkSerial(){
 /*
 * Function: checkSerial
 * ----------------------------
 *   Checking the serial for incoming command,
 *   and performing required task accordingly,
 *   this includes input from the WEB UI
 */
  counter = 3;
  for (i = 0; i < 3; i++) {splitArray[i] = "";}
  if(Serial.available()){
    inputState=0;
    while(Serial.available()) {
      // read the incoming byte:
      char c = Serial.read();
      if(c==char(' ')){
        counter--;
      }else if(c==char('\n')){
        Serial.flush();
      }else{
        switch(counter){
          case 3:
            //inputType += c;
            splitArray[0] += c;
            break;
          case 2:
            //inputField += c;
            splitArray[1] += c;
            break;
          case 1:
            //inputState = c-'0';
            splitArray[2] = c;
            break;
         }
      }
    }
  }
  //web
  if(!receivedText.isEmpty()){
    
    char charArray[receivedText.length() + 1];
    receivedText.toCharArray(charArray, sizeof(charArray));

    i = 0;
    token = strtok(charArray, " ");
    while (token != NULL && i < 3) {
      splitArray[i++] = String(token);
      token = strtok(NULL, " ");
    }
    receivedText = "";
  }

  splitArray[0].toUpperCase();
  splitArray[1].toUpperCase();
  inputState = splitArray[2][0]-'0';

  //Serial.println(splitArray[0]);
  //Serial.println(splitArray[1]);
  //Serial.println(splitArray[2]);

  if(splitArray[0] == "SET"){
    if(splitArray[1]=="LIGHTS"){
      if(inputState==1){
        digitalWrite(PIN_LIGHTS,HIGH);
      }else{
        digitalWrite(PIN_LIGHTS,LOW);
        light_auto_mode=false;
      }
    }else if(splitArray[1]=="RED"){
      if(inputState==1){
        digitalWrite(PIN_RED,HIGH);
      }else{
        digitalWrite(PIN_RED,LOW);
      }
    }else if(splitArray[1]=="GREEN"){
      if(inputState==1){
        digitalWrite(PIN_GREEN,HIGH);
      }else{
        digitalWrite(PIN_GREEN,LOW);
      }
    }else if(splitArray[1]=="AC"){
      setAC(inputState);
    }else if(splitArray[1]=="ACM"){
      if(inputState==1){
        auto_ac_mode=true;
      }else{
        auto_ac_mode=false;
      }
    }else if(splitArray[1]=="LAM"){
      if(inputState==1){
        light_auto_mode=true;
      }else{
        light_auto_mode=false;
      }
    }else if(splitArray[1]=="HSM"){
      if(inputState==1){
        home_secure_mode=true;
      }else{
        home_secure_mode=false;
        digitalWrite(PIN_RED, LOW);
        digitalWrite(PIN_GREEN, HIGH);
        first_run=true;
      }
    }else if(splitArray[1]=="EM"){
      if(inputState==1){
        emergency_mode=true;
      }else{
        emergency_mode=false;
        digitalWrite(PIN_RED, LOW);
        digitalWrite(PIN_GREEN, HIGH);
      }
    }

    
  }else if(splitArray[0] == "GET"){
    Serial.flush();
    if(splitArray[1]=="TEMP"){
      Serial.println(String(TEMP));
      returnedText = String(TEMP);
    }else if(splitArray[1]=="LUX"){
      Serial.println(LUX);
      returnedText = String(LUX);
    }else if(splitArray[1]=="MOVE"){
      Serial.println(String(MOVE));
      returnedText = String(MOVE);
      MOVE=0;
    }else if(splitArray[1]=="ACM"){
      Serial.println(auto_ac_mode);
      returnedText = String(auto_ac_mode);
    }else if(splitArray[1]=="LAM"){
      Serial.println(light_auto_mode);
      returnedText = String(light_auto_mode);
    }else if(splitArray[1]=="HSM"){
      Serial.println(home_secure_mode);
      returnedText = String(home_secure_mode);
    }else if(splitArray[1]=="EM"){
      Serial.println(emergency_mode);
      returnedText = String(emergency_mode);
    }
  }
  
}


void updateDisplay(){
 /*
 * Function: updateDisplay
 * ----------------------------
 *   Updates the on-board OLED display
 */
  if(FPS>30){
    display.clear();
    display.setFont(ArialMT_Plain_16);
    display.setTextAlignment(TEXT_ALIGN_CENTER);
    display.drawString(65, 0, "IP: "+connectedIP);
    display.drawString(65, 20, "T:"+String(TEMP)+" L:"+String(LUX)+" M:"+String(MOVE));
    display.setFont(ArialMT_Plain_10);
    display.drawString(65, 40, "ACM:"+String(auto_ac_mode)+" LAM:"+String(light_auto_mode)+" HSM:"+String(home_secure_mode)+" EM:"+String(emergency_mode));
    display.drawString(65, 50, "danielthecyberdude.com");
    display.display();
    FPS=0;
  }
  FPS++;
}

void checkACMode(){
/*
 * Function: checkACMode
 * ----------------------------
 *   Handler for Air conditioning system, note; only cooling or heating can work in a period of time, not both
 */
  if(auto_ac_mode){
    if(TEMP>23){
      setAC(1);
    }else if(TEMP<17){
    setAC(2);
    }else{
      setAC(0);
    }
  }
}

void checkAutoLightMode(){
 /*
 * Function: checkAutoLightMode
 * ----------------------------
 *   Turns the lights if the light_auto_mode is true and luminosity is under 30%
 */
  if(light_auto_mode){
    if(LUX<1228){// lower than 30%
      digitalWrite(PIN_LIGHTS, HIGH);
    }else{
      digitalWrite(PIN_LIGHTS, LOW);
    }
  }
}

void checkHomeSecureMode(){
 /*
 * Function: checkHomeSecureMode
 * ----------------------------
 *   Handles motion and turns on RED LED when the motion is detected
 */
  if(home_secure_mode){
    
    if(MOVE){
      counter++;
      digitalWrite(PIN_RED, HIGH);
      if(counter==1) Serial.println("[!] Motion detected!");
      if(counter>1000){
        MOVE=false;
        digitalWrite(PIN_RED, LOW);
        counter=0;
      }
    }
  }
}

void checkEmergencyMode(){
 /*
 * Function: checkEmergenyMode
 * ----------------------------
 *   Affects other modes accordingly
 */
  if(emergency_mode){
    if(first_run){
      auto_ac_mode = false;
      light_auto_mode = false;
      home_secure_mode = true;
      digitalWrite(PIN_RED, HIGH);
      digitalWrite(PIN_GREEN, LOW);
      first_run=false;
    }
  }
}

void handleRoot() {
   /*
 * Function: handleRoot
 * ----------------------------
 *   Forms WEB UI
 */
  String html = "<html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'>";
  html += "<style>button.switch { appearance: none; -webkit-appearance: none; width: 100px; height: 50px; background-color: #ccc; border: 2px solid #000; border-radius: 25px; position: relative; cursor: pointer; }";
  html += "button.switch:before { content: ''; position: absolute; width: 50px; height: 50px; border-radius: 50%; top: 50%; transform: translateY(-50%); left: -50; right: 0; margin: auto; background-color: #fff; transition: 0.2s; border: 2px solid #000; }";
  html += "button.switch.on { background-color: #00ff00; } button.switch.on:before { left: 50px; } h1, h3 {text-align: center;} .input-section {margin-bottom: 10px; text-align: center;} .input-section label {display: block; font-weight: bold; margin-bottom: 5px;} .input-section input[type='text'] {width: 200px; padding: 5px; border-radius: 5px; border: 1px solid #ccc;} .input-section button {padding: 5px 10px; border-radius: 5px; background-color: #ccc; border: none; cursor: pointer;} .received-text-section {text-align: center;}</style></head><body>";
  html += "<h1>Smart Home Automation System</h1>";
  html += "<h3>{By Daniel Petrovich}</h3>";
  
  html += "<div style='display: flex; flex-direction: row; justify-content: center;'>";

  // Lights
  html += "<div style='margin-right: 20px;'>";
  html += "<h2>Lights</h2>";
  if (digitalRead(PIN_LIGHTS)) {
    html += "<button class='switch on' onclick=\"location.href='/lightsOff'\"></button>";
  } else {
    html += "<button class='switch' onclick=\"location.href='/lightsOn'\"></button>";
  }

  // Light Auto Mode
  html += "<h2>Light Auto Mode</h2>";
  if (light_auto_mode) {
    html += "<button class='switch on' onclick=\"location.href='/lightAutoModeOff'\"></button>";
  } else {
    html += "<button class='switch' onclick=\"location.href='/lightAutoModeOn'\"></button>";
  }

  // Home Secure Mode
  html += "<h2>Home Secure Mode</h2>";
  if (home_secure_mode) {
    html += "<button class='switch on' onclick=\"location.href='/homeSecureModeOff'\"></button>";
  } else {
    html += "<button class='switch' onclick=\"location.href='/homeSecureModeOn'\"></button>";
  }  
  html += "</div>";

  // AC
  html += "<div>";
  html += "<h2>AC Mode</h2>";
  if (auto_ac_mode) {
    html += "<button class='switch on' onclick=\"location.href='/acModeOff'\"></button>";
  } else {
    html += "<button class='switch' onclick=\"location.href='/acModeOn'\"></button>";
  }
  html += "<h2>Cooling</h2>";
  if (digitalRead(PIN_COOLER)) {
    html += "<button class='switch on' onclick=\"location.href='/acOff'\"></button>";
  } else {
    html += "<button class='switch' onclick=\"location.href='/coolingOn'\"></button>";
  }
  html += "<h2>Heating</h2>";
  if (digitalRead(PIN_HEATER)) {
    html += "<button class='switch on' onclick=\"location.href='/acOff'\"></button>";
  } else {
    html += "<button class='switch' onclick=\"location.href='/heatingOn'\"></button>";
  }
  html += "</div>";

  html += "</div><br/><br/>";
  
  // Command input section with autocomplete
  html += "<div class='input-section'><h2>Command:</h2>";
  html += "<input type='text' id='text-input' style='margin: 0 auto;' list='commands'>";
  html += "<datalist id='commands'>";
  html += "<option value='SET LIGHTS 1'>";
  html += "<option value='SET LIGHTS 0'>";
  html += "<option value='SET AC 0'>";
  html += "<option value='SET AC 1'>";
  html += "<option value='SET AC 2'>";
  html += "<option value='SET ACM 1'>";
  html += "<option value='SET ACM 0'>";
  html += "<option value='SET RED 1'>";
  html += "<option value='SET RED 0'>";
  html += "<option value='SET GREEN 1'>";
  html += "<option value='SET GREEN 0'>";
  html += "<option value='SET LAM 1'>";
  html += "<option value='SET LAM 0'>";
  html += "<option value='SET HSM 1'>";
  html += "<option value='SET HSM 0'>";
  html += "<option value='SET EM 1'>";
  html += "<option value='SET EM 0'>";
  
  html += "<option value='GET TEMP'>";
  html += "<option value='GET LUX'>";
  html += "<option value='GET MOVE'>";
  html += "<option value='GET ACM'>";
  html += "<option value='GET LAM'>";
  html += "<option value='GET HSM'>";
  html += "<option value='GET EM'>";
  html += "</datalist>";
  html += "<button onclick=\"sendText()\">Send</button></div>";

  html += "<div class='received-text-section'><h2>Response:</h2>";
  html += "<div id='output' style='margin: 0 auto;'>" + returnedText + "</div></div>";
  html += "<script>function sendText(){var t=document.getElementById('text-input').value;if(t!==''){var e='/sendText?text='+encodeURIComponent(t);location.href=e;}}</script>";
  html += "</body></html>";
  
  server.send(200, "text/html", html);
}






void handleSwitch(String command) {
   /*
 * Function: handleSwitch
 * ----------------------------
 *   Handles the routing for the Switches from the WEB UI
 */
  //digitalWrite(PIN_LIGHTS, state);
  receivedText = command;
  server.sendHeader("Location", "/");
  server.send(302);
}

void handleSendText() {
     /*
 * Function: handleSwitch
 * ----------------------------
 *   Handles the Commands from the WEB UI
 */
  receivedText = server.arg("text");
  //Serial.println(receivedText);
  server.sendHeader("Location", "/");
  server.send(302);
}


void setupWifi() {
     /*
 * Function: handleSwitch
 * ----------------------------
 *   Tries to connect to the WiFi AP,
 *   if fail, continues with IP == "N/A"
 */
  WiFi.begin(ssid, password);
  int i = 0;
  while (WiFi.status() != WL_CONNECTED && i < 10) {
    Serial.println("[!] Connecting to WiFi...");
    display.clear();
    progress = (float)i/10*100;
    // draw the progress bar
    display.drawProgressBar(0, 32, 120, 10, progress);
    
    // draw the percentage as String
    display.setTextAlignment(TEXT_ALIGN_CENTER);
    display.drawString(64, 15, "DP-SHAS "+String(progress) + "%");
    
    display.display();
    delay(1000);//1000/20
    i++;
  }

  if(WiFi.status() == WL_CONNECTED){
    Serial.println("[+] Connected to WiFi");
    WiFi.config(ipAddress, gateway, subnet);
    Serial.println("[+] IP address: "+ ipAddress.toString());
    connectedIP = ipAddress.toString();
  
    server.on("/", handleRoot);
    server.on("/lightsOn", []() { handleSwitch("SET LIGHTS 1"); });
    server.on("/lightsOff", []() { handleSwitch("SET LIGHTS 0"); });
    server.on("/lightAutoModeOn", []() { handleSwitch("SET LAM 1"); });
    server.on("/lightAutoModeOff", []() { handleSwitch("SET LAM 0"); });
    server.on("/homeSecureModeOn", []() { handleSwitch("SET HSM 1"); });
    server.on("/homeSecureModeOff", []() { handleSwitch("SET HSM 0"); });
    
    server.on("/acModeOn", []() { handleSwitch("SET ACM 1"); });
    server.on("/acModeOff", []() { handleSwitch("SET ACM 0"); });
    server.on("/coolingOn", []() { handleSwitch("SET AC 1"); });
    server.on("/heatingOn", []() { handleSwitch("SET AC 2"); });
    server.on("/acOff", []() { handleSwitch("SET AC 0"); });
    server.on("/sendText", handleSendText);

    server.onNotFound([](){
      server.sendHeader("Location", String("/"));
      server.send(302, "text/plain", "");
    });
  
    server.begin();
    Serial.println("[+] HTTP server started");
  }else{
    Serial.println("[-] Wifi AP '"+String(ssid)+"' not found");
  }
}

// MAIN
void setup() {
  Serial.begin(115200);
  display.init(); display.setFont(ArialMT_Plain_10);
  pinSetup();
  
  //calibratePIR();
  setupWifi();
  digitalWrite(PIN_GREEN,HIGH);
}

void loop() {
  updateTemp();
  updateLux();
  updatePIR();
  updateDisplay();

  checkBtn();
  checkEmergencyMode();
  checkACMode();
  checkAutoLightMode();
  checkHomeSecureMode();
  
  server.handleClient();
  checkSerial();
  delay(10);
}
