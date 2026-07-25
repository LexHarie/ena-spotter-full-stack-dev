import type { ReactNode } from "react";

export function Alert({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="alert" role="alert">
      <strong>{title}</strong>
      <div>{children}</div>
    </div>
  );
}
