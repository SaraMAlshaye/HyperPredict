/*
  HyperPredict - MAX30102 firmware TEMPLATE (UNTESTED)
  =====================================================
  Status: written without hardware. It has NOT been compiled, uploaded, or checked
  against a reference oximeter. Treat every number it prints as unverified until the
  team has tested it (see iot/README.md, "Hardware bring-up checklist").

  Board:   ESP32 dev board (recommended) or Arduino Uno/Nano (see memory note below)
  Sensor:  MAX30102 breakout, I2C
  Library: "SparkFun MAX3010x Pulse and Proximity Sensor Library"
           (Arduino IDE -> Library Manager). Uses its MAX30105.h and spo2_algorithm.h,
           which also support the MAX30102.

  Output:  USB serial, 115200 baud, one JSON object per line, about once per second:
    {"v":1,"type":"reading","hr_bpm":72,"hr_valid":1,"spo2_pct":97,"spo2_valid":1,"finger":1,"uptime_ms":123456}
    {"v":1,"type":"status","msg":"sensor_not_found"}
  This must match iot/sensor_protocol.py.

  Wiring (3.3 V logic):
    MAX30102 VIN -> 3.3V        (ESP32 3V3 / Uno 3.3V)
    MAX30102 GND -> GND
    MAX30102 SDA -> ESP32 GPIO21 / Uno A4
    MAX30102 SCL -> ESP32 GPIO22 / Uno A5
    MAX30102 INT -> not used
  Check your breakout's voltage rating; many MAX30102 boards are 3.3 V only.
*/
#include <Wire.h>
#include "MAX30105.h"
#include "spo2_algorithm.h"

MAX30105 particleSensor;

// The Uno has only 2 KB of RAM, so it needs 16-bit buffers (as in SparkFun's example).
#if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__)
uint16_t irBuffer[100];
uint16_t redBuffer[100];
#else
uint32_t irBuffer[100];
uint32_t redBuffer[100];
#endif

const int32_t BUFFER_LENGTH = 100;   // 4 s of samples at 25 samples/s
const int32_t NEW_SAMPLES = 25;      // recompute every ~1 s
const uint32_t FINGER_IR_THRESHOLD = 50000;  // below this IR level: no finger (tune!)

int32_t spo2;
int8_t validSPO2;
int32_t heartRate;
int8_t validHeartRate;

void readSample(int32_t i) {
  while (!particleSensor.available()) {
    particleSensor.check();
  }
  redBuffer[i] = particleSensor.getRed();
  irBuffer[i] = particleSensor.getIR();
  particleSensor.nextSample();
}

void printStatus(const char *msg) {
  Serial.print("{\"v\":1,\"type\":\"status\",\"msg\":\"");
  Serial.print(msg);
  Serial.println("\"}");
}

void printReading(bool finger) {
  Serial.print("{\"v\":1,\"type\":\"reading\",\"hr_bpm\":");
  Serial.print(heartRate);
  Serial.print(",\"hr_valid\":");
  Serial.print(validHeartRate ? 1 : 0);
  Serial.print(",\"spo2_pct\":");
  Serial.print(spo2);
  Serial.print(",\"spo2_valid\":");
  Serial.print(validSPO2 ? 1 : 0);
  Serial.print(",\"finger\":");
  Serial.print(finger ? 1 : 0);
  Serial.print(",\"uptime_ms\":");
  Serial.print(millis());
  Serial.println("}");
}

void setup() {
  Serial.begin(115200);
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    while (true) {               // keep telling the app, never send fake readings
      printStatus("sensor_not_found");
      delay(2000);
    }
  }
  // ledBrightness, sampleAverage, ledMode (2 = red + IR), sampleRate, pulseWidth, adcRange
  particleSensor.setup(60, 4, 2, 100, 411, 4096);

  for (int32_t i = 0; i < BUFFER_LENGTH; i++) {
    readSample(i);
  }
  maxim_heart_rate_and_oxygen_saturation(irBuffer, BUFFER_LENGTH, redBuffer,
                                         &spo2, &validSPO2, &heartRate, &validHeartRate);
}

void loop() {
  // Slide the window: drop the oldest 25 samples, read 25 new ones.
  for (int32_t i = NEW_SAMPLES; i < BUFFER_LENGTH; i++) {
    redBuffer[i - NEW_SAMPLES] = redBuffer[i];
    irBuffer[i - NEW_SAMPLES] = irBuffer[i];
  }
  for (int32_t i = BUFFER_LENGTH - NEW_SAMPLES; i < BUFFER_LENGTH; i++) {
    readSample(i);
  }
  maxim_heart_rate_and_oxygen_saturation(irBuffer, BUFFER_LENGTH, redBuffer,
                                         &spo2, &validSPO2, &heartRate, &validHeartRate);
  bool finger = irBuffer[BUFFER_LENGTH - 1] >= FINGER_IR_THRESHOLD;
  printReading(finger);
}
