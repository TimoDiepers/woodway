import { useT } from "@/i18n/useT";

export default function App() {
  const t = useT();
  return <main className="p-6 font-serif text-2xl">{t("app.title")}</main>;
}
