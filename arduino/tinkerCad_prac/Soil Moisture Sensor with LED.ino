// 핀 번호 정의
const int SENSOR_POWER = 8;  // 수분 센서 전원 핀
const int SENSOR_PIN = A0;   // 수분 센서 아날로그 신호 핀

const int LED_BLUE = 4;      // 파란색 LED (습함)
const int LED_YELLOW = 3;    // 노란색 LED (보통)
const int LED_RED = 2;       // 빨간색 LED (건조)

// 센서 임계값 (상황에 따라 조정 가능)
// 일반적으로 팅커캐드 시뮬레이션 기준:
// - Dry (건조): 0 ~ 300
// - Moist (적당): 301 ~ 600
// - Wet (습함): 601 이상
const int THRESHOLD_DRY = 300;
const int THRESHOLD_MOIST = 600;

void setup() {
  // 시리얼 통신 시작 (시리얼 모니터로 값 확인 가능)
  Serial.begin(9600);

  // 핀 모드 설정
  pinMode(SENSOR_POWER, OUTPUT);
  pinMode(LED_BLUE, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_RED, OUTPUT);

  // 센서 전원은 기본적으로 OFF 상태로 유지
  digitalWrite(SENSOR_POWER, LOW);
}

void loop() {
  // 1. 센서 값 읽기 (전원을 잠시 켜서 측정 후 끔 - 부식 방지)
  int moistureValue = readSoilMoisture();

  // 시리얼 모니터에 값 출력
  Serial.print("Soil Moisture Value: ");
  Serial.println(moistureValue);

  // 2. 수분량에 따라 LED 제어
  if (moistureValue < THRESHOLD_DRY) {
    // [건조함] 빨간색 LED만 켬
    setLEDs(HIGH, LOW, LOW); 
  } 
  else if (moistureValue <= THRESHOLD_MOIST) {
    // [적당함] 노란색 LED만 켬
    setLEDs(LOW, HIGH, LOW); 
  } 
  else {
    // [습함/촉촉함] 파란색 LED만 켬
    setLEDs(LOW, LOW, HIGH); 
  }

  // 1초마다 반복 측정
  delay(1000);
}

// 토양 수분 센서의 값을 읽어오는 함수
int readSoilMoisture() {
  digitalWrite(SENSOR_POWER, HIGH);  // 센서에 전원 공급
  delay(10);                         // 전원이 안정될 때까지 10ms 대기
  int val = analogRead(SENSOR_PIN);  // 아날로그 값 읽기 (0 ~ 1023)
  digitalWrite(SENSOR_POWER, LOW);   // 센서 전원 차단 (센서 수명 연장)
  return val;
}

// LED 상태를 한 번에 제어하는 편의 함수
void setLEDs(int red, int yellow, int blue) {
  digitalWrite(LED_RED, red);
  digitalWrite(LED_YELLOW, yellow);
  digitalWrite(LED_BLUE, blue);
}