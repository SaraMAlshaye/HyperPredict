import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Icon, type IconName } from "./Icon";

type Variant = "primary" | "secondary" | "ghost" | "danger";

interface Props {
  children: ReactNode;
  variant?: Variant;
  to?: string;
  onClick?: () => void;
  type?: "button" | "submit";
  icon?: IconName;
  iconRight?: IconName;
  loading?: boolean;
  disabled?: boolean;
  size?: "md" | "lg";
}

export function Button({
  children, variant = "primary", to, onClick, type = "button", icon, iconRight,
  loading = false, disabled = false, size = "md",
}: Props) {
  const className = `btn btn--${variant} btn--${size}`;
  const content = (
    <>
      {loading ? <span className="spinner spinner--sm" aria-hidden="true" /> : icon && <Icon name={icon} />}
      <span>{children}</span>
      {!loading && iconRight && <Icon name={iconRight} />}
    </>
  );
  if (to && !disabled) {
    return <Link to={to} className={className} onClick={onClick}>{content}</Link>;
  }
  return (
    <button type={type} className={className} onClick={onClick}
            disabled={disabled || loading} aria-busy={loading || undefined}>
      {content}
    </button>
  );
}
