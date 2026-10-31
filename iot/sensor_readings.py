"""Command-line check for the sensor device (no app needed).

    python -m iot.sensor_readings --list-ports      # show serial ports (needs pyserial)
    python -m iot.sensor_readings --port COM3       # print live status/readings
    python -m iot.sensor_readings                   # no port: reports "no device"

Readings are printed for checking the hardware only. Pulse and SpO2 from the sensor
are NOT model inputs: the training data (NHANES 2021-2023) has no SpO2, and its pulse
came from a blood-pressure cuff, not a fingertip sensor (see iot/README.md).
"""
import argparse
import sys
import time

from iot.sensor_source import DEFAULT_BAUDRATE, NoDeviceSource, SerialSensorSource


def list_ports() -> int:
    try:
        from serial.tools import list_ports as lp
    except ImportError:
        print("pyserial is not installed. Run: pip install pyserial")
        return 1
    ports = list(lp.comports())
    if not ports:
        print("No serial ports found. Is the board plugged in and its USB driver installed?")
    for p in ports:
        print(f"{p.device}\t{p.description}")
    return 0


def describe(snap) -> str:
    r = snap.reading
    hr = f"{r.heart_rate_bpm:.0f} BPM" if r and r.heart_rate_bpm is not None else "—"
    spo2 = f"{r.spo2_percent:.0f} %" if r and r.spo2_percent is not None else "—"
    when = r.received_at.astimezone().strftime("%H:%M:%S") if r else "never"
    return f"[{snap.status.value}] HR {hr} | SpO2 {spo2} | last reading {when} | {snap.detail}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", help="serial port, e.g. COM3 or /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUDRATE)
    parser.add_argument("--seconds", type=float, default=30, help="how long to listen")
    parser.add_argument("--list-ports", action="store_true")
    args = parser.parse_args()

    if args.list_ports:
        return list_ports()
    if not args.port:
        print(describe(NoDeviceSource().snapshot()))
        return 0

    source = SerialSensorSource(args.port, args.baud)
    if not source.start():
        print(describe(source.snapshot()))
        return 1
    try:
        end = time.monotonic() + args.seconds
        while time.monotonic() < end:
            time.sleep(1)
            snap = source.snapshot()
            print(describe(snap))
            if snap.status.name == "DISCONNECTED":
                return 1
    except KeyboardInterrupt:
        pass
    finally:
        source.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
