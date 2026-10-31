import { useState } from "react";
import { Button } from "../components/Button";
import { Icon, type IconName } from "../components/Icon";
import { Pulsie } from "../components/Pulsie";

type Tab = "what" | "risk" | "prevent" | "habits";
const TABS: { id: Tab; label: string }[] = [
  { id: "what", label: "What is hypertension?" },
  { id: "risk", label: "Risk factors" },
  { id: "prevent", label: "Prevention" },
  { id: "habits", label: "Healthy habits" },
];

const RISKS: { icon: IconName; title: string; text: string }[] = [
  { icon: "calendar", title: "Getting older", text: "Blood vessels stiffen with age, so blood pressure tends to rise." },
  { icon: "user", title: "Family history", text: "High blood pressure often runs in families." },
  { icon: "scale", title: "Excess body weight", text: "A higher BMI makes the heart work harder." },
  { icon: "shaker", title: "Lots of salt", text: "Too much sodium makes the body hold on to water." },
  { icon: "run", title: "Low activity", text: "Little physical activity is linked with higher blood pressure." },
  { icon: "drop", title: "Alcohol and tobacco", text: "Heavy drinking and smoking both raise blood pressure." },
];

const HABITS: { icon: IconName; title: string; text: string }[] = [
  { icon: "leaf", title: "Eat a balanced diet", text: "Plenty of vegetables, fruit, whole grains and beans; less processed food." },
  { icon: "run", title: "Stay active", text: "At least 150 minutes of moderate activity a week, such as brisk walking." },
  { icon: "moon", title: "Get enough sleep", text: "Most adults need 7–9 hours of good-quality sleep." },
  { icon: "drop", title: "Stay hydrated", text: "Choose water over sugary drinks most of the time." },
  { icon: "heart", title: "Manage stress", text: "Short walks, breathing exercises and time with friends all help." },
  { icon: "stethoscope", title: "Know your numbers", text: "Check your blood pressure regularly, especially after age 40." },
];

export function Learn() {
  const [tab, setTab] = useState<Tab>("what");

  return (
    <div className="page page--learn">
      <header className="page__header">
        <div>
          <h1>Learn more</h1>
          <p className="muted">Short, general facts about blood pressure. Not medical advice.</p>
        </div>
      </header>

      <div className="tabs" role="tablist" aria-label="Topics">
        {TABS.map((t) => (
          <button key={t.id} role="tab" id={`tab-${t.id}`} aria-selected={tab === t.id}
                  aria-controls={`panel-${t.id}`} className={`tabs__tab ${tab === t.id ? "is-active" : ""}`}
                  onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </div>

      <section role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`} className="learn-panel">
        {tab === "what" && (
          <div className="learn-what">
            <div className="card">
              <h2>What is hypertension?</h2>
              <p>
                Hypertension, or high blood pressure, means the force of blood against the walls of your
                arteries stays too high. Over time it can damage blood vessels and raise the chance of heart
                disease, stroke and kidney problems.
              </p>
              <p>
                It usually has <strong>no symptoms</strong>, which is why it is often called a “silent”
                condition. The only way to know is to measure it.
              </p>
              <div className="bp-explainer">
                <div><span className="bp-explainer__num">130</span><span>Systolic: pressure when the heart beats</span></div>
                <span className="bp-explainer__slash">/</span>
                <div><span className="bp-explainer__num">80</span><span>Diastolic: pressure between beats</span></div>
              </div>
              <p className="muted">
                U.S. guidelines (2017 ACC/AHA), which the HyperPredict training data follows, treat readings
                of 130/80 mmHg or higher as hypertension.
              </p>
            </div>
            <Pulsie size="md" speech="Blood pressure is quiet. Measuring it is how you find out!" />
          </div>
        )}

        {tab === "risk" && (
          <ul className="tile-grid">
            {RISKS.map((r) => (
              <li key={r.title} className="card tile">
                <span className="tile__icon"><Icon name={r.icon} size={22} /></span>
                <h3>{r.title}</h3><p>{r.text}</p>
              </li>
            ))}
          </ul>
        )}

        {tab === "prevent" && (
          <div className="card">
            <h2>Lowering your chances</h2>
            <ul className="ticks">
              <li>Keep a healthy weight; even a small loss can lower blood pressure.</li>
              <li>Cut down on salt and highly processed foods.</li>
              <li>Be physically active most days of the week.</li>
              <li>Limit alcohol and avoid tobacco.</li>
              <li>Have your blood pressure checked regularly, and follow your clinician's advice if it is high.</li>
            </ul>
            <p className="muted small">
              Further reading:{" "}
              <a href="https://www.who.int/news-room/fact-sheets/detail/hypertension" target="_blank" rel="noreferrer">WHO hypertension fact sheet</a>.
            </p>
          </div>
        )}

        {tab === "habits" && (
          <ul className="tile-grid">
            {HABITS.map((h) => (
              <li key={h.title} className="card tile">
                <span className="tile__icon"><Icon name={h.icon} size={22} /></span>
                <h3>{h.title}</h3><p>{h.text}</p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <div className="cta card card--soft">
        <div>
          <h2>Curious what the model says about you?</h2>
          <p className="muted">It takes about a minute and only needs five answers.</p>
        </div>
        <Button to="/check/about-you" iconRight="arrowRight">Start a check</Button>
      </div>
    </div>
  );
}
