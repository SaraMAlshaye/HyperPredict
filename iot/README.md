# Arduino / ESP32 + MAX30102 sensor integration

> **Status:** the software side is implemented and tested without hardware. **No physical device has been connected yet.** The firmware is an untested template. No hardware result in this project has been measured.

## What is implemented vs not

| Part | Status |
|---|---|
| Message format (JSON lines over USB serial) — `sensor_protocol.py` | ✅ Implemented, unit-tested |
| Connection layer (connect, read, stale/disconnect detection) — `sensor_source.py` | ✅ Implemented, tested with a fake serial port |
| App sensor panel: heart rate, SpO₂, connection status, time of last measurement — `app/app.py`, `display.py` | ✅ Implemented, tested headlessly; shows "Disconnected" and "—" without hardware |
| Command-line check — `python -m iot.sensor_readings` | ✅ Implemented; tested only without a device |
| Firmware — `firmware/hyperpredict_max30102/hyperpredict_max30102.ino` | ⚠️ Template only: never compiled, uploaded or run |
| Wiring | ⚠️ Documented below, not built |
| Real readings, accuracy vs a reference oximeter | ❌ Not done |
| Using sensor heart rate as a model input | ❌ Not allowed until the compatibility study below is done |

## Sensor readings are display only

- **SpO₂ is never sent to the model.** NHANES 2021–2023 has no oxygen-saturation measurement, so the model was trained without SpO₂. The app's input check rejects any SpO₂ value.
- **Sensor heart rate is not sent to the model either (for now).** The model's `Pulse_BPM` feature is the mean of three blood-pressure-cuff (oscillometric) pulse readings, taken after 5 minutes of seated rest under a clinical protocol. A MAX30102 estimates heart rate from fingertip light (PPG). It is a different method, often noisy (motion, finger pressure, cold hands, ambient light), and the sitting/rest conditions are uncontrolled. The two are **not assumed to be equivalent**. In the app, pulse is typed in by hand.
- **The MAX30102 does not measure BMI.** That model input is entered by the user.
- **Pulse matters little to the model.** Permutation importance is 0.015 ROC-AUC, compared with 0.211 for age.

## Why USB serial (and not Wi-Fi/HTTP first)

The app is a local Streamlit program that runs on the same laptop the board plugs into. USB serial:
- works the same on Arduino Uno/Nano and ESP32;
- needs no network, passwords, IP addresses or extra server;
- powers the board from the laptop;
- is easy to debug with the Arduino Serial Monitor.

HTTP/Wi-Fi (ESP32 only) would need a separate web endpoint next to Streamlit, because Streamlit cannot receive POST requests, as well as Wi-Fi setup and network security. The message format is plain JSON, so a later Wi-Fi version can reuse `parse_line()` unchanged.

## Message format (version 1)

USB serial, 115200 baud, one JSON object per line, about once per second:

```json
{"v":1,"type":"reading","hr_bpm":72,"hr_valid":1,"spo2_pct":97,"spo2_valid":1,"finger":1,"uptime_ms":123456}
{"v":1,"type":"status","msg":"sensor_not_found"}
```

**What the app rejects or blanks out** (it never invents a value):

| Problem | What the app does |
|---|---|
| Malformed line (not JSON, wrong version, unknown type, missing or invalid `finger`) | Rejects the line |
| `hr_valid` / `spo2_valid` = 0 | Shows "—" for that value |
| Heart rate outside 30–220 BPM, or SpO₂ outside 70–100 % | Shows "—" for that value |
| `finger` = 0 | Shows "—" for both values |

**Timestamps:** the board has no clock, so each measurement is stamped with the time the laptop *received* it.

**Status shown in the app:**

| Status | Meaning |
|---|---|
| No device configured | No port entered. This is the default. |
| Cannot connect | pyserial is missing, or the port is wrong, busy or unplugged |
| Connected, waiting for data | Port open, nothing received yet |
| Connected, but no valid data received | Nothing valid after 10 s |
| Receiving readings | Valid data arriving |
| Readings stopped | No valid reading for more than 5 s; the last values are labelled "not current" |
| Device reported an error | For example, `sensor_not_found` |
| Disconnected | The connection was lost or closed |

## Wiring (planned, not yet built)

| MAX30102 pin | ESP32 dev board | Arduino Uno / Nano |
|---|---|---|
| VIN | 3V3 | 3.3V |
| GND | GND | GND |
| SDA | GPIO 21 | A4 |
| SCL | GPIO 22 | A5 |
| INT | not used | not used |

Check the breakout board's voltage rating before powering it; many MAX30102 boards are 3.3 V only. The ESP32 is recommended: 3.3 V logic, and more memory for the SpO₂ algorithm buffers.

## Hardware bring-up checklist (to do when the hardware arrives)

1. **Install the board support.** In the Arduino IDE, install ESP32 board support (or use the built-in AVR boards for the Uno), plus the library **"SparkFun MAX3010x Pulse and Proximity Sensor Library"**.
2. **Wire it** as in the table above. Open `iot/firmware/hyperpredict_max30102/hyperpredict_max30102.ino`, then compile and upload it. *Fix any compile errors; the template has never been compiled.*
3. **Check the raw output.** Open the Serial Monitor at 115200 baud and confirm one JSON line per second.
   - With no finger on the sensor, you should see `finger:0`.
   - If the sensor is miswired, you should see `sensor_not_found`.
4. **Close the Serial Monitor** (only one program can use the port at a time). Then:
   ```bash
   pip install pyserial
   python -m iot.sensor_readings --list-ports
   python -m iot.sensor_readings --port COM3        # use your port
   ```
5. **Run the app** with `streamlit run app/app.py`. Enter the port in the sidebar and click **Connect**. Check each status in the table above by placing and removing a finger and by unplugging the cable.
6. **Tune `FINGER_IR_THRESHOLD`** in the firmware if finger detection is wrong.
7. **Record the results** (what worked, and the accuracy check below) in this file before you claim the hardware works.

## Compatibility study needed before sensor heart rate can be a model input

1. **Compare against references.** In at least about 20 volunteers, measure the MAX30102 heart rate and an automatic BP-cuff pulse at the same time, using the NHANES-like protocol (5 minutes seated rest, 3 readings). Also compare against a commercial fingertip oximeter.
2. **Report the differences:** the mean difference (bias), the limits of agreement (Bland–Altman), and the percentage of readings within ±5 BPM.
3. **Decide, document, then implement.** Only if agreement is acceptable should the team add an *explicit, user-confirmed* "use sensor heart rate as pulse" option. Even then, SpO₂ stays display-only.

## Files

- `sensor_protocol.py`: message format and strict parser
- `sensor_source.py`: `NoDeviceSource` (default) and `SerialSensorSource`
- `display.py`: turns the connection state into what the app shows
- `sensor_readings.py`: command-line check
- `firmware/hyperpredict_max30102/`: Arduino/ESP32 sketch template (untested)
- Tests: `tests/test_sensor_protocol.py`, `tests/test_sensor_source.py`, `tests/test_app.py`

Consumer sensor readings can be inaccurate and are not clinical measurements.
