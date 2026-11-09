import { useId, type ComponentPropsWithoutRef, type ReactNode } from "react";

import "./Block.css";

type BlockProps = Omit<ComponentPropsWithoutRef<"div">, "title"> & {
  variant?: "default" | "featured" | "alert";
  as?: "div" | "section" | "aside";
  title?: ReactNode;
  headingLevel?: 2 | 3 | 4;
  count?: number | string;
  countLabel?: string;
  actions?: ReactNode;
};

export function Counter({ children, label }: { children: ReactNode; label?: string }) {
  return (
    <span className="counter" data-ui="counter" aria-label={label}>
      {children}
    </span>
  );
}

export function Block({
  variant = "default",
  as: Tag = "div",
  title,
  headingLevel = 2,
  count,
  countLabel,
  actions,
  className,
  children,
  ...rest
}: BlockProps) {
  const titleId = useId();
  const Heading = `h${headingLevel}` as "h2" | "h3" | "h4";
  const hasTitle = title !== undefined && title !== null;
  const hasCount = count !== undefined;
  const hasHeader = hasTitle || hasCount || actions;
  const labelled = Tag !== "div" && hasTitle ? { "aria-labelledby": titleId } : {};

  return (
    <Tag
      {...labelled}
      {...rest}
      className={["block", variant !== "default" && variant, className].filter(Boolean).join(" ")}
      data-ui="block"
    >
      {hasHeader && (
        <div className="blk-h">
          {hasTitle && (
            <Heading id={titleId} data-ui="block-title">
              {title}
            </Heading>
          )}
          {hasCount && <Counter label={countLabel}>{count}</Counter>}
          {actions && (
            <>
              <span className="sp" />
              {actions}
            </>
          )}
        </div>
      )}
      {children}
    </Tag>
  );
}
