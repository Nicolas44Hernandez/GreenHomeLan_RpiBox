#include <ArduinoBLE.h>
BLEService buttonService("180A");
BLEByteCharacteristic switchCommand("2A57", BLERead | BLEWrite| BLENotify | BLEBroadcast);

const int leBouton = 2;  // un bouton sur la broche 2
// variable qui enregistre l'état du bouton
int etatBouton;
int ancienEtatBouton;

// long previousMillis = 0;
// int pres = 0;
// bool activate = false;

void setup() {
  
  // CONFIGURATION SERIAL LINK
  Serial.begin(9600);
  while(!Serial);
  pinMode(LED_BUILTIN, OUTPUT);

  // CONFIGURATION INPUT BUTTON
  pinMode(leBouton, INPUT);
  digitalWrite(leBouton, HIGH);
  etatBouton = HIGH;          // le bouton est relaché
  ancienEtatBouton = HIGH;    // le bouton est relaché

  
  if (!BLE.begin()){
    Serial.println("starting BLE failed!");
    while (1);
  }

  String address = BLE.address();
  Serial.print("Local address is: ");
  Serial.println(address);
  
  BLE.setLocalName("ButtonBLE");
  
  // BLE.setAdvertisedService(buttonService);
  // buttonService.addCharacteristic(switchCommand);
  // BLE.addService(buttonService);
  BLE.setAdvertisingInterval(500);
  switchCommand.writeValue((byte)0x11);
  BLE.advertise();
  switchCommand.broadcast();
  Serial.println("Bluetooth device active, waiting for communications...");
}

void loop() {
  // BLEDevice central = BLE.central();
  // if (central) {
  //   Serial.print("Connected to central : ");
  //   Serial.println(central.address()); 


    digitalWrite(LED_BUILTIN, HIGH);
    // activate = false;
    // while (central.connected()){
    while (1==1){


      etatBouton = digitalRead(leBouton);
      if ((etatBouton == HIGH) && (ancienEtatBouton == LOW)) {
          Serial.println("Button Relache"); // le bouton est relaché
          switchCommand.writeValue(0);
      } else if ((etatBouton == LOW) && (ancienEtatBouton == HIGH)) {
          Serial.println("Button Appuye"); // le bouton est appuyé
          switchCommand.writeValue(65);
      } else {
      }
      ancienEtatBouton = etatBouton;
      

    }
    digitalWrite(LED_BUILTIN, LOW);
    // Serial.print("Disconnected from central: ");
    // Serial.println(central.address());
    digitalWrite(leBouton, LOW); 
  // }
}
