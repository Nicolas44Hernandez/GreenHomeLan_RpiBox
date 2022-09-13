#include <ArduinoBLE.h>
BLEService buttonService("180A");
BLEByteCharacteristic switchCommand("2A57", BLERead | BLEWrite| BLENotify | BLEBroadcast);

const int ledPin = 2;
long previousMillis = 0;
int pres = 0;
bool activate = false;

void setup() {
  Serial.begin(9600);
  while(!Serial);
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(ledPin, OUTPUT);
  if (!BLE.begin()){
    Serial.println("starting BLE failed!");
    while (1);
  }
  BLE.setLocalName("ButtonBLE");
  BLE.setAdvertisedService(buttonService);
  buttonService.addCharacteristic(switchCommand);
  BLE.addService(buttonService);
  switchCommand.writeValue((byte)0x11);
  BLE.advertise();
  Serial.println("Bluetooth device active, waiting for communications...");
}

void loop() {
  BLEDevice central = BLE.central();
  if (central) {
    Serial.print("Connected to central : ");
    Serial.println(central.address()); 
    digitalWrite(ledPin, LOW);
    digitalWrite(LED_BUILTIN, HIGH);
    activate = false;
    while (central.connected()){
      long currentMillis = millis();
      if (currentMillis - previousMillis >= 200){
        previousMillis = currentMillis;
        pres = analogRead(A1);
//        Serial.print("SwitchCommand : ");
//        Serial.println(switchCommand.valueSize());
//        Serial.print("pres : ");
//        Serial.println(pres);
        if (pres > 1000 && !activate){
          activate = true;
          Serial.println("Activation Button On");
          switchCommand.writeValue(65);
          digitalWrite(ledPin, HIGH);
        }
        else if (pres < 1001 && activate){
          activate = false;
          Serial.println("Activation Button OFF");
          switchCommand.writeValue(0);
          digitalWrite(ledPin, LOW); 
        }
      }
    }
    digitalWrite(LED_BUILTIN, LOW);
    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
    digitalWrite(ledPin, LOW); 
  }
}
