# HyperPredict web app

React + TypeScript + Vite frontend for HyperPredict, connected to the existing trained model through a small FastAPI backend (`api/main.py`).

> Educational project only. Results come from a machine-learning model and are **not a medical diagnosis**.

## Run it

You need two terminals, both opened in the **project root** (the folder that contains `api/` and `web/`).

**1. Backend (Python, port 8000)**
```bash
pip install -r requirements.txt
python -m uvicorn api.main:app --reload --port 8000
```

**2. Frontend (Node.js 18+, port 5173)**
```bash
cd web
npm install
npm run dev
```

Open http://localhost:5173. The dev server forwards `/api/*` to the backend, so both must be running.

**Single-server option:** run `npm run build` in `web/`, then start only the backend and open http://localhost:8000. FastAPI serves the built app from `web/dist`.

## Checks
```bash
cd web
npm run typecheck   # TypeScript
npm test            # unit tests: BMI, validation, local history
npm run build       # production build
python -m pytest    # (from the project root) includes tests/test_api.py
```

## How it talks to the model

| Step | Where |
|---|---|
| User enters age, sex, race/ethnicity, height, weight | `pages/PersonalInfo.tsx` |
| BMI = weight ÷ height² is calculated in the browser; **only BMI is sent** | `lib/bmi.ts`, `lib/validation.ts` |
| Resting pulse comes from the sensor panel. Today no device is connected, so it shows "Waiting for sensor" and Continue stays disabled; no BPM is ever invented. | `pages/PulseInfo.tsx`, `components/SensorReading.tsx` |
| `POST /api/predict` with exactly `Age_Years, BMI, Pulse_BPM, Sex, Race_Ethnicity` | `lib/api.ts` |
| FastAPI validates against the saved schema and runs the saved pipeline | `api/main.py` → `machine_learning/inference.py` |
| The real label and probability are shown, then saved to localStorage history | `pages/Result.tsx`, `lib/history.ts` |

- **No preprocessing in JavaScript.** Imputation, scaling and encoding stay inside the saved scikit-learn pipeline.
- **Strict inputs.** Unknown fields (SpO₂, height, weight, blood pressure) are rejected by the API.
- **Options come from the model.** Dropdown options and value ranges are read from `GET /api/schema`, i.e. from the trained model's feature schema.

## Pages

| Route | Page |
|---|---|
| `/` | Welcome |
| `/check/about-you` | Step 1: personal information and BMI |
| `/check/pulse` | Step 2: resting pulse from the MAX30102 sensor (waiting state until hardware is integrated) |
| `/result/:id` | Prediction result |
| `/history` | Past results (this browser only) |
| `/learn` | What hypertension is, risk factors, prevention, healthy habits |

## Sensor (future hardware)

`src/lib/sensor.ts` holds the sensor state (`waiting → connected → measuring → received`, or `error`) and the `SensorSource` interface. The app currently uses `NoSensorSource`, which stays in "waiting" and never produces a reading.

To add the Arduino/ESP32 + MAX30102 later:
1. Implement `SensorSource`, for example with the browser's Web Serial API, or by streaming from the Python serial layer in `iot/sensor_source.py`.
2. Return it from `createSensorSource()`.

The page, the BPM validation (`isUsableReading`, using the model's 30–220 BPM range) and the prediction call need no changes. SpO₂ must stay display-only and is never sent to the model.

## Pulsie

`src/assets/pulsie.png` is the original Pulsie artwork supplied by the team, copied byte-for-byte. The app never redraws it. CSS only rounds or softly fades its lavender background.

## History storage

Results are stored in the browser's `localStorage` under `hyperpredict.history.v1` (newest 50). This is demo storage: it stays on one device, is not backed up, and disappears when browser data is cleared.
