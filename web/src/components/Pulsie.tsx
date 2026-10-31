import type { ReactNode } from "react";
import pulsieImage from "../assets/pulsie.png";

/**
 * Pulsie, the HyperPredict mascot. Always the original artwork (assets/pulsie.png),
 * never redrawn. CSS only fades the image's soft lavender background into the page.
 */
export function Pulsie({ size = "md", speech, float = false, className = "" }: {
  size?: "xs" | "sm" | "md" | "lg" | "xl"; speech?: ReactNode; float?: boolean; className?: string;
}) {
  return (
    <figure className={`pulsie pulsie--${size} ${className}`}>
      {speech && <figcaption className="pulsie__speech">{speech}</figcaption>}
      <img
        src={pulsieImage} alt="Pulsie, the HyperPredict mascot"
        className={`pulsie__img ${float ? "pulsie__img--float" : ""}`}
        width={1254} height={1254} decoding="async"
      />
    </figure>
  );
}

/** Small round Pulsie for the logo and avatars. */
export function PulsieAvatar({ size = 40 }: { size?: number }) {
  return (
    <span className="pulsie-avatar" style={{ width: size, height: size }}>
      <img src={pulsieImage} alt="" aria-hidden="true" />
    </span>
  );
}
