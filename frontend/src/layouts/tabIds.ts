// Identificadores que unen cada pestaña con su panel (`aria-controls` y `aria-labelledby`).
export function tabId(prefix: string, id: string): string {
  return `${prefix}-tab-${id}`;
}

export function tabPanelId(prefix: string, id: string): string {
  return `${prefix}-panel-${id}`;
}
