#include <ArduinoBLE.h>
BLEService buttonService("180A");
BLEByteCharacteristic switchCommand("2A57", BLERead | BLEWrite| BLENotify | BLEBroadcast);

const int ledPin = 2;
int newState;
int currentState;
long previousMillis = 0;
int pres = 0;
bool activate = false;
int a = 10;

void setup() {
  Serial.begin(9600);
  while(!Serial);
  pinMode(LED_BUILTIN, OUTPUT);


  pinMode(ledPin, INPUT);
  digitalWrite(ledPin, LOW);
  newState = LOW;           // le bouton est relaché
  currentState = LOW;       // le bouton est relaché
  
  if (!BLE.begin()){
    Serial.println("starting BLE failed!");
    while (1);
  }
  String address = BLE.address();
  Serial.print("Local address is: ");
  Serial.println(address);
  BLE.setLocalName("ButtonBLE");
  
  //BLE.setAdvertisingInterval(5000);
  BLE.advertise();
  
}

void loop() {
    newState = digitalRead(ledPin);
    if ((newState == HIGH) && (currentState == LOW)) {
      Serial.println("Button Appuye"); // le bouton est relaché
      digitalWrite(LED_BUILTIN, HIGH);
    }  
    else if ((newState == LOW) && (currentState == HIGH)) {
      Serial.println("Button Relache"); // le bouton est appuyé
      digitalWrite(LED_BUILTIN, LOW);
      switchCommand.broadcast();
      switchCommand.writeValue(a);
      a = a + 1;
    } 
    currentState = newState;
 }
