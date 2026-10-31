import type { ReactNode } from "react";
import { Icon, type IconName } from "./Icon";

export function Card({ title, icon, children, className = "", as: Tag = "section" }: {
  title?: string; icon?: IconName; children: ReactNode; className?: string;
  as?: "section" | "div" | "article";
}) {
  return (
    <Tag className={`card ${className}`}>
      {title && (
        <h2 className="card__title">
          {icon && <span className="card__icon"><Icon name={icon} size={18} /></span>}
          {title}
        </h2>
      )}
      {children}
    </Tag>
  );
}
