#include <SPI.h>
#include <LoRa.h>

#define LOCAL_ADDR  0x11
#define BROADCAST   0xFF
#define SYNC_WORD   0xDD
#define LORA_FREQ   433.5E6
#define SF_LEVEL    9

int csPin = D8;
int resetPin = D1;
int irqPin = D0;


unsigned long lastSend = 0;
unsigned long sendInterval = 10000; // 10 sec
int msgID = 0;

void setup() {
  Serial.begin(115200);
  randomSeed(analogRead(0));

  LoRa.setPins(csPin, resetPin, irqPin);

  if (!LoRa.begin(LORA_FREQ)) {
    Serial.println("LoRa start failed!");
    while (1);
  }

  LoRa.setSyncWord(SYNC_WORD);
  LoRa.setSpreadingFactor(SF_LEVEL);

}

void loop() {
  // Heartbeat every ~10 sec
  

  // Read manual commands from Serial
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "Motor1_ON" || cmd == "Motor1_OFF" ||cmd == "Motor2_ON" || cmd == "Motor2_OFF"|| cmd == "Motors_OFF") {
      for (int i=0;i < 20; i++){
        LoRa.beginPacket();
        LoRa.write(0x22);   // UNO
        LoRa.write(LOCAL_ADDR);
        LoRa.write(msgID++);
        LoRa.write(cmd.length());
        LoRa.print(cmd);
        LoRa.endPacket();
        delay(50); }
    }
  }

  // Check for incoming packets
  int packetSize = LoRa.parsePacket();
  if (packetSize > 0) {
    int recipient = LoRa.read();
    int sender    = LoRa.read();
    int id        = LoRa.read();
    int len       = LoRa.read();
    String incoming = "";
    while (LoRa.available()) incoming += (char)LoRa.read();

    if (recipient == LOCAL_ADDR || recipient == BROADCAST) {
      //Serial.println("----------- RECEIVED -----------");
      //Serial.print("From: 0x"); Serial.println(sender, HEX);
      //Serial.print("Message: ");
      Serial.print("Voltage:"); 
      Serial.println(incoming);
      //Serial.print("RSSI: "); Serial.println(LoRa.packetRssi());
      //Serial.print("SNR: "); Serial.println(LoRa.packetSnr());
      //Serial.println("--------------------------------");
    }
  }

  delay(3); // small delay for SX1278 stability
}
