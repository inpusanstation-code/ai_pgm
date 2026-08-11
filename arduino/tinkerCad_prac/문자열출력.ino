#include<LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

void setup() {
  lcd.begin(16, 2);
  lcd.print("Hello, world!!!");
}

void loop() {
  lcd.print("Cusor ON-Blink");
  lcd.cursor();
  lcd.blink();
  delay(2000);
  lcd.clear();

  lcd.print("Cusor OFF");
  lcd.noBlink();
  lcd.cursor();
  delay(1000);
  lcd.clear();
  
  lcd.print("Count Up");
  delay(1000);
  lcd.clear();
  
  for(int k = 0; k <= 10; k++) {
    lcd.home();
    lcd.print("No : ");
    lcd.print(k);
    delay(200);
  }

  lcd.clear();
  lcd.print("Hello!");

  for(int k = 0; k < 3; k++) {
    lcd.noDisplay();
    delay(1000);
    lcd.display();
    delay(1000);
  }

  lcd.clear();
  
  lcd.setCursor(6, 0);
  lcd.print("Hello!");
  
  for(int k = 0; k < 3; k++) {
    lcd.scrollDisplayRight();
    delay(500);
  }
  
  lcd.clear();

  lcd.setCursor(6, 0);
  lcd.print("Hello!");
  
  for(int k = 0; k < 3; k++) {
    lcd.scrollDisplayLeft();
    delay(500);
  }
  lcd.clear();
}
  
  
  
  
  

