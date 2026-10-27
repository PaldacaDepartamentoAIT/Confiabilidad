import type { ButtonHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  type?: "button" | "submit";
};

export function Button({ type = "button", ...buttonProps }: ButtonProps) {
  return <button {...buttonProps} type={type} />;
}
