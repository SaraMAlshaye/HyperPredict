# Optional IoT sensor demonstration

This folder is reserved for a separate proof-of-concept that can read pulse and SpO2 using an ESP32 or Arduino-compatible board and a compatible sensor such as MAX30102.

Important, from the dataset review in [docs/DATASET.md](../docs/DATASET.md):
- **SpO2 is not in the training data.** NHANES 2021–2023 has no oxygen-saturation measurement, so SpO2 readings must never be passed to the model (none has been trained yet). They can only be displayed.
- **Pulse is in the training data, but it was measured differently.** The model's `Pulse_BPM` feature comes from the blood-pressure cuff, averaged over three readings after 5 minutes of seated rest. A MAX30102 fingertip reading is a different measurement, so it is not yet established that it can replace the training feature.
- **Pulse is a weak predictor in this data** (Spearman 0.04 with the target).

Keep the sensor display separate from the model until the team has decided and documented whether sensor pulse is compatible with the training data. The sensor demo is not evidence that the model uses these measurements.

Before demonstrating hardware, verify wiring, sensor/library compatibility, and readings against appropriate reference equipment. Consumer sensor readings can be inaccurate and are not clinical measurements.
