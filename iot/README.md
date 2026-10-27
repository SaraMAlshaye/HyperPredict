# Optional IoT sensor demonstration

This folder is reserved for a separate proof-of-concept that can read pulse and SpO2 using an ESP32 or Arduino-compatible board and a compatible sensor such as MAX30102.

Important: the currently selected hypertension dataset does not include pulse or SpO2 according to the project's data review. These readings therefore must not be passed into the trained ML model unless a suitable, documented training dataset with matching features and labels is sourced and approved. The sensor display is a separate demonstration, not evidence that the model uses those measurements.

Before demonstrating hardware, verify wiring, sensor/library compatibility, and readings against appropriate reference equipment. Consumer sensor readings can be inaccurate and are not clinical measurements.
