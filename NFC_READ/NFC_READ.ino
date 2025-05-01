#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN 10
#define RST_PIN 9

MFRC522 rfid(SS_PIN, RST_PIN);  // MFRC522 인스턴스

void setup() {
  Serial.begin(9600);
  SPI.begin();            
  rfid.PCD_Init();       
  Serial.println(F("Ready to read NFC tag (decimal only)."));
}

void loop() {
  // 새로운 카드가 없으면 리턴
  if (!rfid.PICC_IsNewCardPresent()) return;
  if (!rfid.PICC_ReadCardSerial()) return;

  // UID의 10진수 값을 Serial로 전송
  // 예: "123 45 67 89\n"
  for (byte i = 0; i < rfid.uid.size; i++) {
    Serial.print(rfid.uid.uidByte[i], DEC);
    if (i < rfid.uid.size - 1) Serial.print(' ');
  }
  Serial.println();

  // 카드 통신 종료
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
}
