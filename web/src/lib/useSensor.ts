import { useEffect, useMemo, useState } from "react";
import { INITIAL_SENSOR_STATE, createSensorSource, type SensorSource, type SensorState } from "./sensor";

/** Subscribes to the sensor for as long as the component is on screen. */
export function useSensor(source?: SensorSource): { state: SensorState; retry: () => void } {
  const sensor = useMemo(() => source ?? createSensorSource(), [source]);
  const [state, setState] = useState<SensorState>(INITIAL_SENSOR_STATE);

  useEffect(() => {
    const unsubscribe = sensor.subscribe(setState);
    sensor.start();
    return () => {
      unsubscribe();
      sensor.stop();
    };
  }, [sensor]);

  return { state, retry: () => sensor.start() };
}
