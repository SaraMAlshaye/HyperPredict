"""Placeholder for optional serial sensor integration.

Do not connect this demo to the ML predictor. The training data (NHANES 2021-2023) has
no SpO2, and its pulse feature comes from a blood-pressure cuff, not a fingertip sensor
(see docs/DATASET.md). Implement only after documenting your sensor output format,
hardware setup, and safety limitations.
"""


def main() -> None:
    print("IoT integration is not configured yet.")
    print("Add and validate sensor-specific serial parsing before use.")
    print("Pulse and SpO2 values are not ML model inputs in this project version.")


if __name__ == "__main__":
    main()
