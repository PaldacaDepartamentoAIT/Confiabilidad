import type { LanguageStorage } from "./i18n/language";
import { useDocumentLanguage } from "./i18n/useDocumentLanguage";
import { ShowcasePage } from "./showcase/ShowcasePage";

type AppProps = {
  storage?: LanguageStorage;
};

export function App({ storage }: AppProps) {
  useDocumentLanguage();
  return <ShowcasePage storage={storage} />;
}
