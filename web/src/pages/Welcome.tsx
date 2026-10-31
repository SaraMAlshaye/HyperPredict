import { Button } from "../components/Button";
import { Icon, type IconName } from "../components/Icon";
import { Pulsie } from "../components/Pulsie";
import { Disclaimer } from "../components/States";
import { useAppState } from "../lib/AppState";
import { formatPercent } from "../lib/format";

const STEPS: { icon: IconName; title: string; text: string }[] = [
  { icon: "user", title: "Tell us about you", text: "Age, sex, background, height and weight. We work out your BMI for you." },
  { icon: "pulse", title: "Add your resting pulse", text: "Count your heartbeats for a minute after sitting quietly, and type it in." },
  { icon: "sparkle", title: "See the model's estimate", text: "A trained model compares your answers with thousands of survey participants." },
];

export function Welcome() {
  const { schemaState } = useAppState();
  const metrics = schemaState.status === "ready" ? schemaState.schema.test_metrics : null;

  return (
    <div className="page page--welcome">
      <section className="hero">
        <div className="hero__text">
          <p className="eyebrow"><Icon name="heart" size={16} /> Meet Pulsie</p>
          <h1 className="hero__title">Your little heart-health companion.</h1>
          <p className="hero__lead">Understand your health better, one step at a time.</p>
          <p className="hero__body">
            HyperPredict is a university machine-learning project. It estimates whether an adult's
            profile resembles people who had hypertension in a large U.S. health survey, using five
            simple inputs.
          </p>
          <div className="hero__actions">
            <Button to="/check/about-you" size="lg" iconRight="arrowRight">Get started</Button>
            <Button to="/learn" variant="ghost" icon="book">What is hypertension?</Button>
          </div>
          <p className="hero__note"><Icon name="shield" size={16} /> Takes about a minute. Nothing is sent anywhere except our own model.</p>
        </div>
        <div className="hero__art">
          <div className="hero__halo" aria-hidden="true" />
          <Pulsie size="xl" float speech={<>Hi, I'm Pulsie! Let's check in on your heart together.</>} />
        </div>
      </section>

      <section className="section">
        <h2 className="section__title">How it works</h2>
        <ol className="how">
          {STEPS.map((s, i) => (
            <li key={s.title} className="how__step card">
              <span className="how__num">{i + 1}</span>
              <span className="how__icon"><Icon name={s.icon} size={24} /></span>
              <h3>{s.title}</h3>
              <p>{s.text}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="section split">
        <div className="card card--soft">
          <h2 className="card__title"><span className="card__icon"><Icon name="model" size={18} /></span>About the model</h2>
          <p>
            A logistic regression model trained on CDC NHANES 2021–2023 data from 6,081 adults. It
            uses age, sex, race/ethnicity, BMI and resting pulse. Blood pressure itself is not an
            input, because it was used to define who had hypertension.
          </p>
          {metrics && (
            <dl className="stats">
              <div><dt>Found on unseen data</dt><dd>{formatPercent(metrics.recall)}</dd><span>of people with hypertension</span></div>
              <div><dt>Ranking quality</dt><dd>{metrics.roc_auc.toFixed(2)}</dd><span>ROC-AUC (1.0 = perfect)</span></div>
            </dl>
          )}
        </div>
        <div className="card card--soft">
          <h2 className="card__title"><span className="card__icon"><Icon name="shield" size={18} /></span>What it is not</h2>
          <ul className="ticks">
            <li>Not a diagnosis, and not a blood-pressure measurement.</li>
            <li>Not a prediction of future disease.</li>
            <li>Not a replacement for a check-up. Only a blood-pressure reading by a professional can tell you if you have hypertension.</li>
          </ul>
        </div>
      </section>

      <Disclaimer />
    </div>
  );
}
