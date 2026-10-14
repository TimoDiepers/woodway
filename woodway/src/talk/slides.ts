import type { Atlas, Scale } from "@/data/types";
import { layerById, type Layer, type LayerId } from "@/model/layers";
import type { AtlasSlideId } from "./sequence";
import { buildP95, coolingShare, medianDacNet } from "./stats";

export interface AtlasSlideDef {
  id: AtlasSlideId; title: string; ch?: "vergleich" | "dac"; layer: LayerId;
  years: number[];                       // year per step; the map animates between them
  sitesFrom?: number;                    // step from which the three example sites are marked
  takeaway(at: Atlas, step: number): string; source: string; notes: string[]; free?: boolean;
}

const pct = (x: number) => `${Math.round(100 * x).toLocaleString("de-DE")} %`;
const yearAt = (d: { years: number[] }, step: number) => d.years[Math.max(0, Math.min(d.years.length - 1, step))];

const MODEL_SRC = "Eigenes Modell: typischer Wald der Zelle, gepflanzt 2026, FaIR (Leach et al. 2021), SSP2-4,5; Fläche Walker et al. 2022; Waldtyp: Hasler et al. 2024.";

const jedeZelle: AtlasSlideDef = {
  id: "jedeZelle", title: "Temperaturwirkung eines Baums je Zelle, 2030–2100", ch: "vergleich", layer: "deltaT", years: [2030, 2050, 2100], sitesFrom: 3,
  takeaway: (at, step) => {
    const y = yearAt(jedeZelle, step);
    return `${y}: Ein Baum kühlt auf ${pct(coolingShare(at, y))} der wiederbewaldbaren Fläche.${y < 2050 ? " Die Albedo wirkt erst mit dem Kronenschluss." : ""}`;
  },
  source: MODEL_SRC,
  notes: [
    "Dieselbe Rechnung wie für Aachen, jetzt für jede Zelle der Karte: Waldtyp, Wachstum und Albedo des Ortes bestimmen, ob ein Baum kühlt oder wärmt.",
    "Klick: das Jahr läuft von 2030 über 2050 bis 2100. Ein weiterer Klick markiert die drei Beispielorte.",
  ],
};
const albedo: AtlasSlideDef = {
  id: "albedo", title: "Netto-Anteil nach Albedo je Zelle, 2100", ch: "vergleich", layer: "netShare", years: [2100],
  takeaway: (at) => {
    const g = at.meta.global.areasGha, gha = (x: number) => x.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return `Bäume kühlen 2100 auf ${gha(g.kuehlt)} von ${gha(g.alle)} Gha wiederbewaldbarer Fläche; auf dem Rest überwiegt die Albedo.`;
  },
  source: `${MODEL_SRC} Albedo: Duveiller et al. 2018.`,
  notes: ["Anteil der CO₂-Wirkung, der nach dem Albedo-Effekt übrig bleibt: hoch in den Tropen, deutlich weniger oder negativ dort, wo ein Wald den Boden dunkler macht."],
};
const dacStrom: AtlasSlideDef = {
  id: "dacStrom", title: "Netto-Anteil von DAC je Zelle, 2026–2070", ch: "dac", layer: "dacNet", years: [2026, 2040, 2070],
  takeaway: (at, step) => { const y = yearAt(dacStrom, step); return `${y}: Im Median über die Landfläche bleiben ${pct(medianDacNet(at, y))} jeder entnommenen Tonne netto.`; },
  source: "Eigenes Modell: Sorbens-DAC mit Wärmepumpe (Sendi et al. 2022), Strommix REMIND-EU SSP2-NDC über premise.",
  notes: ["Netto-Anteil einer DAC-Tonne nach den Emissionen von Bau und Betrieb: Er hängt vom Strommix des Ortes ab und steigt, wenn der Strom sauberer wird."],
};
const dacAusbau: AtlasSlideDef = {
  id: "dacAusbau", title: "DACCS-Ausbau je Zelle, 2026–2100", ch: "dac", layer: "dacBuild", years: [2026, 2100],
  takeaway: (at) => `${Math.max(...at.meta.global.dacCapacityGt).toLocaleString("de-DE", { maximumFractionDigits: 1 })} Gt CO₂ pro Jahr ab sofort, ohne Wachstumsgrenze, um ab 2027 höchstens 1,5 °C zu halten; die Kapazität je Land ist auf Zellen nahe Sedimentbecken mit dem höchsten Netto-Anteil verteilt.`,
  source: "Eigene Rechnung: kleinste Weltkapazität für höchstens 1,5 °C ab 2027, ohne Wachstumsgrenze; Speicher Gidden et al. 2025.",
  notes: ["Ein Klick lässt den Ausbau von 2026 bis 2100 durchlaufen: gebaut wird dort, wo der Netto-Anteil am höchsten ist, sofort in voller Größe; nach 2041 reicht es."],
};
const atlas: AtlasSlideDef = {
  id: "atlas", title: "Atlas", layer: "deltaT", years: [2100], free: true,
  takeaway: () => "Jede Zelle anklicken: Waldtyp, Wachstum, Antrieb, Temperatur und DAC an diesem Ort.",
  source: "Alle Daten: woodway/export_woodway.py.",
  notes: ["Freier Teil: Ebene, Jahr und Ort frei wählen; Fragen aus dem Publikum direkt an der Karte beantworten."],
};

export const SLIDES: Record<AtlasSlideId, AtlasSlideDef> = { jedeZelle, albedo, dacStrom, dacAusbau, atlas };

export const atlasSteps = (id: AtlasSlideId): number => {
  const d = SLIDES[id];
  return d.years.length - 1 + (d.sitesFrom ? 1 : 0);
};

// The standalone atlas keeps 0–60 Mt/a; on the talk's slide that leaves 2100 almost empty, so the scale ends at the
// 95th percentile of the built cells and starts darker than the greys of land and "too cold".
const scales = new WeakMap<Atlas, Scale>();
function talkBuildScale(at: Atlas): Scale {
  let sc = scales.get(at);
  if (!sc) { sc = { stops: ["#3f9f9a", "#1f8a8a", "#0f6670", "#0a3d4a"], domain: [0, buildP95(at, 2030)], gamma: 0.6, unit: "Mt/a" }; scales.set(at, sc); }
  return sc;
}
const derived = new WeakMap<Atlas, Layer>();

/** The layer an atlas slide paints: the named layer, for the build-out with the scale fitted to the built cells. */
export function talkLayer(def: AtlasSlideDef, at: Atlas): Layer {
  const base = layerById(def.layer);
  if (def.id !== "dacAusbau") return base;
  let l = derived.get(at);
  if (!l) { l = { ...base, scaleFn: talkBuildScale }; derived.set(at, l); }
  return l;
}
