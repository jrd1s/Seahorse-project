#include <Servo.h>

Servo winchServo;
Servo servo1;
Servo servo2;
Servo thruster;
Servo thruster1;

const int servo1Pin = 9;
const int servo2Pin = 10;
const int winchServoPin = 6;
const int thrusterPin = 5;
const int thrusterPin1 = 3;

const int THRUSTER_NEUTRAL_US = 1500;

// Helper function to mirror the angle for a reversed servo
int reverseAngle(int angle) {
  return 180 - angle;
}

void setup() {
  Serial.begin(9600);

  winchServo.attach(winchServoPin);
  servo1.attach(servo1Pin);
  servo2.attach(servo2Pin);
  thruster.attach(thrusterPin);
  thruster1.attach(thrusterPin1);

  // Arm the ESCs with neutral signal before use
  thruster.writeMicroseconds(THRUSTER_NEUTRAL_US);
  thruster1.writeMicroseconds(THRUSTER_NEUTRAL_US);
  delay(4000); // Wait for ESC arming beeps to complete

  servo1.write(90);
  servo2.write(reverseAngle(90));

  Serial.println("1");
}

void loop() {
  if (Serial.available() > 0) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) return;

    char command = line.charAt(0);

    switch (command) {
      case '1':  // Winch stop (X)
        winchServo.writeMicroseconds(1500);
        Serial.println("Winch: stop");
        break;

      case '2':  // Winch wind in (Square)
        winchServo.writeMicroseconds(500);
        Serial.println("Winch: wind in");
        break;

      case '3':  // Winch wind out (Circle)
        winchServo.writeMicroseconds(2500);
        Serial.println("Winch: wind out");
        break;

      case 'S': {  // Servo pair angle from left stick, e.g. "S135"
        int angle = line.substring(1).toInt();
        angle = constrain(angle, 0, 180);
        servo1.write(angle);
        servo2.write(reverseAngle(angle));
        break;
      }

      case 'L': {  // Left servo (servo1) raw angle for turning, e.g. "L180"
        int angle = line.substring(1).toInt();
        angle = constrain(angle, 0, 180);
        servo1.write(angle);
        break;
      }

      case 'R': {  // Right servo (servo2) raw angle for turning, e.g. "R180"
        int angle = line.substring(1).toInt();
        angle = constrain(angle, 0, 180);
        servo2.write(angle);
        break;
      }

      case 'T': {  // Thruster microseconds from triggers, e.g. "T1650"
        int us = line.substring(1).toInt();
        us = constrain(us, 1000, 2000);
        thruster.writeMicroseconds(us);
        thruster1.writeMicroseconds(us);
        break;
      }

      case 'A': {  // Left thruster (pin 5) only, e.g. "A1650" - used while turning
        int us = line.substring(1).toInt();
        us = constrain(us, 1000, 2000);
        thruster.writeMicroseconds(us);
        break;
      }

      case 'B': {  // Right thruster (pin 3) only, e.g. "B1650" - used while turning
        int us = line.substring(1).toInt();
        us = constrain(us, 1000, 2000);
        thruster1.writeMicroseconds(us);
        break;
      }

      default:
        Serial.println("Try again");
        break;
    }
  }
}
