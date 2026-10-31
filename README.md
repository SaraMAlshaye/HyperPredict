# HyperPredict
### Hypertension classification with machine learning, featuring Pulsie 💙

HyperPredict is a university machine-learning project. It estimates whether an adult's profile resembles people who had **hypertension** in the U.S. CDC National Health and Nutrition Examination Survey (**NHANES**, August 2021 – August 2023).

It includes:
- a reproducible data pipeline;
- a trained, documented model;
- a React web application with our mascot **Pulsie**;
- a FastAPI backend;
- groundwork for an Arduino/ESP32 + **MAX30102** pulse sensor.

> ⚠️ **Educational prototype only.** HyperPredict is not a medical device and does not diagnose hypertension or predict future disease. Its output is a machine-learning estimate. Only a blood-pressure measurement by a qualified professional can tell whether someone has hypertension.

---

## Contents
- [Features](#features)
- [Technologies](#technologies)
- [Project structure](#project-structure)
- [Installation and setup](#installation-and-setup)
- [Running the backend and frontend](#running-the-backend-and-frontend)
- [Machine learning overview](#machine-learning-overview)
- [Arduino and MAX30102 integration status](#arduino-and-max30102-integration-status)
- [Testing](#testing)
- [Documentation](#documentation)
- [Team](#team)

## Features

**Web application** (`web/`, React + TypeScript)
- **Welcome page** with Pulsie, explaining what the model is and is not.
- **About you:** age, sex, race/ethnicity, height and weight, with validation. BMI is calculated automatically; only BMI is sent to the model.
- **Resting pulse:** a sensor-based page with:
  - a large BPM display and connection status (Waiting for sensor, Connected, Measuring, Reading received, Connection error);
  - a heartbeat animation and progress indicator;
  - measuring instructions.

  Continue unlocks only after a valid sensor reading, and no BPM value is ever invented.
- **Result:** the model's real label and probability, shown against its 50% decision threshold, with plain-language explanation, general guidance and a medical disclaimer.
- **History:** past results stored in the browser (localStorage demo storage), with a score chart.
- **Learn:** short facts about hypertension, risk factors, prevention and healthy habits.
- **Layout:** desktop-first and responsive, with accessible forms, loading/error/empty states, and reduced-motion support.

**Backend** (`api/`, FastAPI)
- `GET /api/health`, `GET /api/schema`, `POST /api/predict`.
- Uses the existing trained pipeline; no preprocessing is duplicated in JavaScript.
- Accepts exactly the five model features and rejects anything else (SpO₂, height, weight, blood pressure).

**Machine learning** (`data_analysis/`, `machine_learning/`)
- One-command NHANES download, merge, cleaning, EDA and validation (30 checks).
- Three models compared with cross-validation on training data, plus a held-out test evaluation and a transparent selection rule.

**Earlier interface:** a Streamlit app (`app/`) is still included.

## Technologies

| Area | Tools |
|---|---|
| Frontend | React 18, TypeScript, Vite, React Router, custom CSS, Vitest |
| Backend | Python 3.10+, FastAPI, Uvicorn, Pydantic |
| Machine learning | pandas, NumPy, scikit-learn, joblib, Matplotlib, seaborn |
| Data | CDC NHANES 2021–2023 public-use files (downloaded by script) |
| Testing | pytest (backend, ML, sensor layer), Vitest (frontend logic) |
| Hardware (planned) | Arduino/ESP32, MAX30102, USB serial (pyserial) |
| Earlier prototype | Streamlit |

## Project structure

```text
HyperPredict/
├── web/                      # React + TypeScript web app (Vite)
│   └── src/
│       ├── pages/            # Welcome, About you, Resting pulse, Result, History, Learn
│       ├── components/       # Layout, buttons, fields, Pulsie, result & sensor displays
│       ├── lib/              # API client, BMI, validation, history, sensor state
│       ├── styles/           # Design system (global.css)
│       └── assets/pulsie.png # Original Pulsie artwork
├── api/                      # FastAPI backend serving the trained model
├── machine_learning/         # Features, candidate models, training, evaluation, inference
│   └── models/               # Trained model + schema (generated locally, not committed)
├── data_analysis/            # NHANES download, merge, cleaning, EDA, validation
├── data/                     # raw/ and processed/ data (generated locally, not committed)
├── results/
│   ├── figures/              # EDA and model evaluation charts
│   └── reports/              # Cleaning, EDA, validation and model reports
├── iot/                      # Sensor protocol, serial layer, firmware template (untested)
├── app/                      # Streamlit prototype (earlier interface)
├── tests/                    # pytest suite (no hardware needed)
├── docs/                     # DATASET.md, MODEL.md, PROJECT_PLAN.md
├── TASKS.md                  # Team task tracker
└── requirements.txt
```

## Installation and setup

**Requirements:** Python 3.10+, Node.js 18+ (for the web app), Git.

```bash
git clone https://github.com/SaraMAlshaye/HyperPredict.git
cd HyperPredict

# Python environment
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1
# macOS / Linux:       source .venv/bin/activate
pip install -r requirements.txt
```

**Build the data and the model.** Data and trained model files are not stored in Git. These two commands recreate them exactly from the official CDC files:

```bash
python data_analysis/run_pipeline.py   # downloads NHANES, merges, cleans, EDA, 30 validation checks
python -m machine_learning.train       # trains and compares models, saves the selected one
python -m machine_learning.evaluate    # optional: re-checks the saved model
```

**Web app dependencies:**

```bash
cd web
npm install
```

## Running the backend and frontend

Open two terminals in the project root.

**Terminal 1: backend (port 8000)**
```bash
python -m uvicorn api.main:app --reload --port 8000
```

**Terminal 2: frontend (port 5173)**
```bash
cd web
npm run dev
```

Then open **http://localhost:5173**. The dev server forwards `/api` requests to the backend.

**Single-server option:** run `npm run build` in `web/`, start only the backend, and open http://localhost:8000.

**Streamlit prototype (optional):** `streamlit run app/app.py`

More frontend details: [web/README.md](web/README.md).

## Machine learning overview

| Item | Details |
|---|---|
| Data | NHANES 2021–2023: DEMO_L, BPXO_L, BPQ_L, BMX_L, merged on `SEQN`. 6,081 adults after cleaning. |
| Target | `Hypertension_Status` = 1 if mean BP ≥ 130/80 mmHg **or** taking prescribed BP medication (reproduces CDC/NCHS Data Brief 511; survey-weighted prevalence 47.7%) |
| Features (5) | `Age_Years`, `BMI`, `Pulse_BPM`, `Sex`, `Race_Ethnicity` |
| Never used as features | Blood-pressure readings and BP questionnaire/medication answers (they define the target), `SEQN`, SpO₂ (not measured in NHANES) |
| Method | Stratified 80/20 split; 5-fold CV on training data only; preprocessing inside the scikit-learn pipeline |
| Selected model | **Logistic Regression** (model version 3) |

**Results on the held-out test set (1,217 people):**

| Model | CV ROC-AUC | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|---|
| **Logistic Regression (selected)** | 0.788 | 0.721 | 0.733 | 0.749 | 0.741 | 0.791 |
| Decision Tree | 0.772 | 0.709 | 0.726 | 0.730 | 0.728 | 0.764 |
| Random Forest | 0.790 | 0.725 | 0.726 | 0.777 | 0.751 | 0.789 |

- **Why Logistic Regression:** Random Forest's CV ROC-AUC is only 0.002 higher. That is within the pre-set 0.01 tie margin, so the simpler, explainable model was chosen.
- **What it relies on:** age matters most, followed by BMI.
- **Performance is moderate:** about 1 in 4 people with hypertension is missed. That is suitable for an educational prototype only.
- **Model history:**
  - Version 2 removed the income-to-poverty ratio (it added almost nothing).
  - Version 3 removed waist circumference.

Full details: [docs/DATASET.md](docs/DATASET.md) and [docs/MODEL.md](docs/MODEL.md).

## Arduino and MAX30102 integration status

| Part | Status |
|---|---|
| Web app Resting Pulse page (sensor UI, status states, validation) | ✅ Built. Shows **"Waiting for sensor"**, because no device is connected yet |
| Sensor state layer in the web app (`web/src/lib/sensor.ts`) | ✅ Built, with a single connection point for real hardware |
| Python serial protocol and connection layer (`iot/`) | ✅ Built and unit-tested with a simulated port |
| Firmware for ESP32/Arduino + MAX30102 (`iot/firmware/`) | ⚠️ Template only: not yet compiled or tested on hardware |
| Physical wiring and real readings | ❌ Not done yet |

**Current limitation:** because the Resting Pulse page waits for a real sensor reading, a full prediction cannot be completed in the web app until the hardware is connected. Readings are never simulated.

**Important design rules:**
- **SpO₂ is display-only** and is never sent to the model, because the model was not trained on it.
- **Sensor heart rate needs validation first.** The model learned from blood-pressure-cuff pulse measured at rest, so the team must check that the MAX30102 heart rate agrees with it (see the compatibility study in [iot/README.md](iot/README.md)).

Wiring tables and the bring-up checklist: [iot/README.md](iot/README.md).

## Testing

```bash
python -m pytest            # backend API, inference, sensor layer, Streamlit app (75 tests)
cd web
npm run typecheck           # TypeScript
npm test                    # frontend logic: BMI, validation, history, sensor state (25 tests)
npm run build               # production build
```

## Documentation

| Document | Contents |
|---|---|
| [docs/DATASET.md](docs/DATASET.md) | Data source, merge, cleaning rules, target definition, leakage, EDA |
| [docs/MODEL.md](docs/MODEL.md) | Training method, results, selection, limitations, version history |
| [web/README.md](web/README.md) | Web app architecture, API connection, sensor integration point |
| [iot/README.md](iot/README.md) | Hardware status, wiring, message format, bring-up checklist |
| [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) · [TASKS.md](TASKS.md) | Plan and team task tracker |

## Data and privacy
- NHANES public-use data is downloaded by script and **not stored in this repository**.
- Prediction history lives only in the user's browser.
- No API keys, credentials or personal data are committed.

## Team
- **Sara Alshaye** — [@SaraMAlshaye](https://github.com/SaraMAlshaye)
- **Mashael Almojally** — [@mashaelalmojally](https://github.com/mashaelalmojally)
- **Sara Aldayel** — [@saaraaldayel](https://github.com/saaraaldayel)

## Disclaimer
This software is an educational prototype. It has not been clinically validated, and no prediction should replace assessment by a qualified healthcare professional.
