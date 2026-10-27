import type { ButtonHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  type?: "button" | "submit";
  keepFocusOnMouseDown?: boolean;
};

export function Button({
  type = "button",
  keepFocusOnMouseDown = false,
  onMouseDown,
  ...buttonProps
}: ButtonProps) {
  return (
    <button
      {...buttonProps}
      type={type}
      onMouseDown={(event) => {
        // Sin quitar el foco al campo, su error no desaparece bajo el puntero y el clic llega (D-17).
        if (keepFocusOnMouseDown) event.preventDefault();
        onMouseDown?.(event);
      }}
    />
  );
}
