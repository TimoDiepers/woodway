import { useRef, useState, type FormEvent } from "react";
import { Loader2, Search } from "lucide-react";
import { useT } from "@/i18n/useT";

export interface Place { name: string; lon: number; lat: number }

interface NominatimHit { display_name: string; lat: string; lon: string }

/** Place search after woodway's LocationSearch, reduced to an explicit submit: nothing leaves the page
 *  until Enter, then one request to OpenStreetMap's Nominatim. */
export function PlaceSearch({ onPick, fetcher = (...a) => fetch(...a) }: { onPick(p: Place): void; fetcher?: typeof fetch }) {
  const t = useT();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Place[] | null>(null);
  const [state, setState] = useState<"idle" | "loading" | "error">("idle");
  const inputRef = useRef<HTMLInputElement>(null);
  const abort = useRef<AbortController | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    abort.current?.abort();
    const ctl = (abort.current = new AbortController());
    setState("loading");
    setResults(null);
    try {
      const res = await fetcher(`https://nominatim.openstreetmap.org/search?format=json&limit=5&q=${encodeURIComponent(q)}`, { signal: ctl.signal });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const hits = (await res.json()) as NominatimHit[];
      if (ctl.signal.aborted) return;
      setResults(hits.map((h) => ({ name: h.display_name, lon: parseFloat(h.lon), lat: parseFloat(h.lat) }))
        .filter((p) => Number.isFinite(p.lon) && Number.isFinite(p.lat)));
      setState("idle");
    } catch (err) {
      if (!(err instanceof DOMException && err.name === "AbortError")) setState("error");
    }
  };

  const pick = (p: Place) => {
    onPick(p);
    setResults(null);
    inputRef.current?.blur();
  };

  return (
    <div className="text-sm">
      <form role="search" onSubmit={submit}
        className="flex items-center gap-2 rounded-md border border-panelBorder bg-paper/60 px-2.5 py-1.5 focus-within:ring-2 focus-within:ring-accent/50">
        {state === "loading" ? <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin text-inkMuted" aria-hidden />
          : <Search className="h-3.5 w-3.5 shrink-0 text-inkMuted" aria-hidden />}
        {/* 16 px on phones: iOS zooms the page into smaller focused fields */}
        <input ref={inputRef} type="search" value={query} onChange={(e) => setQuery(e.target.value)}
          aria-label={t("search.label")} placeholder={t("search.placeholder")} enterKeyHint="search"
          autoCorrect="off" autoCapitalize="off" spellCheck={false}
          className="min-w-0 flex-1 bg-transparent text-base [&::-webkit-search-cancel-button]:appearance-none text-ink placeholder:text-inkMuted focus:outline-none md:text-sm" />
      </form>
      {state === "error" && <p className="mt-1 px-1 text-xs text-inkMuted">{t("search.error")}</p>}
      {results && results.length === 0 && <p className="mt-1 px-1 text-xs text-inkMuted">{t("search.none")}</p>}
      {results && results.length > 0 && (
        <ul className="mt-1 max-h-56 overflow-y-auto">
          {results.map((p) => (
            <li key={`${p.lat},${p.lon}`}>
              <button type="button" onClick={() => pick(p)} title={p.name}
                className="block w-full truncate rounded px-2 py-1.5 text-left text-xs text-ink hover:bg-ink/5">{p.name}</button>
            </li>
          ))}
        </ul>
      )}
      {results && <p className="mt-1 px-1 text-[10px] text-inkMuted">{t("search.credit")}</p>}
    </div>
  );
}
