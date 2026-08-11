#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define PIEZO_BUZZER 3
#define VR A0

// LCD 설정
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ========================================================
// 🛠️ 핀 매핑 수정 (a, b, c, d, e, f, g, dp 순서)
// a:11, b:10, c:8, d:4, e:5, f:7, g:6, dp:9
// ========================================================
const int segmentPins[8] = {11, 10, 8, 4, 5, 7, 6, 9};

// 7세그먼트 숫자 표기 패턴 (0~7) - {a, b, c, d, e, f, g, dp}
const byte numPatterns[8][8] = {
  {0, 0, 0, 0, 0, 0, 0, 0}, // 0 : 꺼짐 (또는 쉼표)
  {0, 1, 1, 0, 0, 0, 0, 0}, // 1 : 도 (C) / 숫자 1
  {1, 1, 0, 1, 1, 0, 1, 0}, // 2 : 레 (D) / 숫자 2
  {1, 1, 1, 1, 0, 0, 1, 0}, // 3 : 미 (E) / 숫자 3
  {0, 1, 1, 0, 0, 1, 1, 0}, // 4 : 파 (F)
  {1, 0, 1, 1, 0, 1, 1, 0}, // 5 : 솔 (G)
  {1, 0, 1, 1, 1, 1, 1, 0}, // 6 : 라 (A)
  {1, 1, 1, 0, 0, 0, 0, 0}  // 7 : 시 (B)
};

// 음계 주파수 정의
#define NOTE_C4  262
#define NOTE_D4  294
#define NOTE_E4  330
#define NOTE_F4  349
#define NOTE_G4  392
#define NOTE_A4  440
#define NOTE_B4  494
#define NOTE_C5  523
#define NOTE_D5  587
#define NOTE_E5  659
#define NOTE_G5  784
#define REST     0

// 🍄 슈퍼마리오 메인 테마
int melody[] = {
  NOTE_E5, NOTE_E5, REST, NOTE_E5, REST, NOTE_C5, NOTE_E5, REST,
  NOTE_G5, REST, REST, REST, NOTE_G4, REST, REST, REST,
  NOTE_C5, REST, REST, NOTE_G4, REST, REST, NOTE_E4, REST,
  REST, NOTE_A4, REST, NOTE_B4, REST, NOTE_A4, NOTE_G4
};

// 각 음에 해당하는 계이름 번호 (1:도, 2:레, 3:미, 4:파, 5:솔, 6:라, 7:시, 0:쉼표)
int noteNumbers[] = {
  3, 3, 0, 3, 0, 1, 3, 0,
  5, 0, 0, 0, 5, 0, 0, 0,
  1, 0, 0, 5, 0, 0, 3, 0,
  0, 6, 0, 7, 0, 6, 5
};

int noteDurations[] = {
  8, 8, 8, 8, 8, 8, 8, 8,
  8, 8, 8, 8, 8, 8, 8, 8,
  8, 8, 8, 8, 8, 8, 8, 8,
  8, 8, 8, 8, 8, 8, 8
};

int totalNotes = sizeof(melody) / sizeof(melody[0]);
int currentNote = 0;
unsigned long previousMillis = 0;
int noteDuration = 0;

// 카운트다운 상태 변수 (0: 대기, 2: 노래 연주 중)
int playState = 0; 

// 7세그먼트 숫자 출력 함수 (신호 반전 ! 적용)
void displaySegmentNumber(int num) {
  if (num < 0 || num > 7) num = 0;
  for (int i = 0; i < 8; i++) {
    // segmentPins[i] 배열에 정의된 핀으로 !numPatterns 신호를 내보냄
    digitalWrite(segmentPins[i], !numPatterns[num][i]); 
  }
}

// ⏳ 3, 2, 1 카운트다운 함수
void runCountdown() {
  for (int count = 3; count >= 1; count--) {
    lcd.setCursor(0, 1);
    lcd.print("Ready... ");
    lcd.print(count);
    lcd.print("      ");

    displaySegmentNumber(count); // 3, 2, 1 숫자가 매핑된 핀으로 켜짐
    
    tone(PIEZO_BUZZER, 880, 100); 
    delay(500); 
  }

  // 시작 알림음
  tone(PIEZO_BUZZER, 1760, 200);
  displaySegmentNumber(0);
  delay(200);

  lcd.setCursor(0, 1);
  lcd.print("Super Mario! 🍄 ");
}

void setup() {
  Serial.begin(9600);

  // 지정된 핀(11, 10, 8, 4, 5, 7, 6, 9)을 모두 출력 모드로 설정
  for (int i = 0; i < 8; i++) {
    pinMode(segmentPins[i], OUTPUT);
  }

  // 초기 상태에서 세그먼트 완전히 끄기
  displaySegmentNumber(0);

  lcd.init();
  lcd.backlight();

  lcd.setCursor(0, 0);
  lcd.print("Sensor Value");

  lcd.setCursor(0, 1);
  lcd.print("Mario OFF       ");
}

void loop() {
  int analogValue = analogRead(VR);
  unsigned long currentMillis = millis();

  // =========================
  // 가변저항 올렸을 때 (100 초과)
  // =========================
  if (analogValue > 100) {
    
    // 1. 카운트다운 실행
    if (playState == 0) {
      runCountdown();
      playState = 2; 
      previousMillis = millis();
    }

    // 2. 노래 연주 및 음계 숫자 표시
    if (playState == 2) {
      if (currentMillis - previousMillis >= noteDuration) {
        previousMillis = currentMillis;

        noteDuration = 1200 / noteDurations[currentNote];
        
        int note = melody[currentNote];
        int noteNum = noteNumbers[currentNote];

        if (note != REST) {
          tone(PIEZO_BUZZER, note, noteDuration * 0.7);
          displaySegmentNumber(noteNum); // 계이름 번호 출력
        } else {
          noTone(PIEZO_BUZZER);
          displaySegmentNumber(0);
        }

        currentNote = (currentNote + 1) % totalNotes;
      }
    }
  } 
  // =========================
  // 가변저항 0으로 내렸을 때 (초기화)
  // =========================
  else {
    noTone(PIEZO_BUZZER);
    displaySegmentNumber(0);
    
    currentNote = 0;
    noteDuration = 0;
    playState = 0; // 카운트다운을 다시 할 수 있도록 대기 상태로 변경

    lcd.setCursor(0, 1);
    lcd.print("Mario OFF       ");
  }

  Serial.print("VR Value: ");
  Serial.println(analogValue);

  delay(20);
}