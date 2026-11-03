import { LiveAnnouncer } from "./components/LiveAnnouncer";
import type { LanguageStorage } from "./i18n/language";
import { useDocumentLanguage } from "./i18n/useDocumentLanguage";
import { matchRoute, useLocation } from "./routing/router";
import { ShowcasePage } from "./showcase/ShowcasePage";

// La página de muestra sigue siendo la de inicio y la de reserva (S-06 de componentes-base-accesibles).
const ROUTES = ["/"] as const;

type AppProps = {
  storage?: LanguageStorage;
};

export function App({ storage }: AppProps) {
  useDocumentLanguage();
  const route = matchRoute(useLocation().path, ROUTES, "/");
  return <LiveAnnouncer>{route === "/" && <ShowcasePage storage={storage} />}</LiveAnnouncer>;
}
