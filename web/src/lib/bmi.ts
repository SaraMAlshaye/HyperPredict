/** BMI = weight (kg) / height (m)². Height and weight stay in the browser; only BMI is sent. */
export function calculateBmi(heightCm: number, weightKg: number): number | null {
  if (!Number.isFinite(heightCm) || !Number.isFinite(weightKg)) return null;
  if (heightCm <= 0 || weightKg <= 0) return null;
  // Same as weight / (height/100)², written to avoid binary rounding error
  // (1.6 * 1.6 = 2.5600000000000005 would turn 31.25 into 31.2499…).
  return (weightKg * 10000) / (heightCm * heightCm);
}

/** NHANES records BMI with one decimal place, so the model receives the same precision. */
export function roundBmi(bmi: number): number {
  return Math.round(bmi * 10) / 10;
}

/** Standard adult BMI categories (WHO). Shown as general information only. */
export function bmiCategory(bmi: number): string {
  if (bmi < 18.5) return "Underweight range";
  if (bmi < 25) return "Healthy weight range";
  if (bmi < 30) return "Overweight range";
  return "Obesity range";
}
