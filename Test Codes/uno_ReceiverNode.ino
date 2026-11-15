#include <SPI.h>
#include <LoRa.h>

#define LOCAL_ADDR  0x22
#define BROADCAST   0xFF
#define SYNC_WORD   0xDD
#define LORA_FREQ   433.5E6
#define SF_LEVEL    9

#define DHTPIN 3
#define DHTTYPE DHT11
#define LED01 4
#define LED02 5
#define volPin A0


bool LineBlockedSent = false;


//finale finale finale
unsigned long lastSend = 0;
const unsigned long sendInterval = 4000; // 10 sec
int msgID = 0;

void setup() {
  Serial.begin(115200);
  pinMode(LED01, OUTPUT);
  pinMode(LED02, OUTPUT);

  
  if (!LoRa.begin(LORA_FREQ)) {
    Serial.println("LoRa start failed!");
    while (1);
  }

  LoRa.setSyncWord(SYNC_WORD);
  LoRa.setSpreadingFactor(SF_LEVEL);

  Serial.println("UNO Node Ready...");
}

void sendPacket(String msg, byte dest) {
  LoRa.beginPacket();
  LoRa.write(dest);         // destination
  LoRa.write(LOCAL_ADDR);   // sender
  LoRa.write(msgID);        // message ID
  LoRa.write(msg.length()); // payload length
  LoRa.print(msg);
  LoRa.endPacket();         // blocking send
  msgID++;

  Serial.println(msg);
}

void receivePacket(int packetSize) {
  if (packetSize == 0) return;

  int recipient = LoRa.read();
  int sender    = LoRa.read();
  int id        = LoRa.read();
  int len       = LoRa.read();

  String incoming = "";
  while (LoRa.available()) incoming += (char)LoRa.read();

  if (recipient != LOCAL_ADDR && recipient != BROADCAST) return;
  Serial.println(incoming);


  // Manual LED control
  if (incoming == "Motor1_ON") digitalWrite(LED01, HIGH);
  if (incoming == "Motor1_OFF") digitalWrite(LED01, LOW);
  if (incoming == "Motor2_ON") digitalWrite(LED02, HIGH);
  if (incoming == "Motor2_OFF") digitalWrite(LED02, LOW);
}

void loop() {
  // Send DHT sensor data every 10 seconds
  if (millis() - lastSend > sendInterval) {
    float volValue = analogRead(volPin)/1023.0*5;
    String msgVol = String(volValue, 2);
    sendPacket(msgVol, 0x11);

    if (volValue >= 1.2) {

  // Check whether pin 4 and 5 are ON
      bool pin4State = digitalRead(4);
      bool pin5State = digitalRead(5);

      if (pin4State == HIGH || pin5State == HIGH) {

        if (!LineBlockedSent) {
          Serial.println("Line_blocked");

          // Turn off power after detection
          digitalWrite(4, LOW);
          digitalWrite(5, LOW);

          String msg = "Line_blocked";

          for (int i = 0; i < 20; i++) {
            sendPacket(msg, 0x11);
            delay(50);
      }

          LineBlockedSent = true;
    }
  }

  } else {
    // reset flag only when voltage returns to normal
    LineBlockedSent = false;
}



    lastSend = millis();
  }

  // Check for incoming commands
  int packetSize = LoRa.parsePacket();
  if (packetSize) receivePacket(packetSize);

  delay(3); // small delay for stability
}


