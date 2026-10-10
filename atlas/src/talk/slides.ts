import type { Atlas } from "@/data/types";
import type { LayerId } from "@/model/layers";
import type { AtlasSlideId } from "./sequence";
import { coolingShare, dacCapacityGt, medianDacNet, netShareArea } from "./stats";

export interface AtlasSlideDef {
  id: AtlasSlideId; title: string; ch?: "vergleich" | "dac"; layer: LayerId;
  years: number[];                       // year per step; the map animates between them
  sitesFrom?: number;                    // step from which the three example sites are marked
  takeaway(at: Atlas, step: number): string; source: string; notes: string[]; free?: boolean;
}

const pct = (x: number) => `${Math.round(100 * x).toLocaleString("de-DE")} %`;
const yearAt = (d: { years: number[] }, step: number) => d.years[Math.max(0, Math.min(d.years.length - 1, step))];

const MODEL_SRC = "Eigenes Modell: typischer Wald der Zelle, gepflanzt 2026, FaIR (Leach et al. 2021), SSP2-4,5; Fläche Walker et al. 2022.";

const jedeZelle: AtlasSlideDef = {
  id: "jedeZelle", title: "Jede Zelle, jedes Jahr", ch: "vergleich", layer: "deltaT", years: [2030, 2050, 2100], sitesFrom: 3,
  takeaway: (at, step) => { const y = yearAt(jedeZelle, step); return y < 2050 ? `${y}: Auf ${pct(coolingShare(at, y))} der Fläche kühlt ein junger Baum schon — die Albedo holt erst später auf.` : `${pct(coolingShare(at, y))} der wiederbewaldbaren Fläche: dort kühlt ein Baum im Jahr ${y}.`; },
  source: MODEL_SRC,
  notes: [
    "Dieselbe Rechnung wie für Aachen, jetzt für jede Zelle der Karte: Waldtyp, Wachstum und Albedo des Ortes bestimmen, ob ein Baum kühlt oder wärmt.",
    "Klick: das Jahr läuft von 2030 über 2050 bis 2100. Ein weiterer Klick markiert die drei Beispielorte.",
  ],
};
const albedo: AtlasSlideDef = {
  id: "albedo", title: "Wo die Albedo den Kohlenstoff auffrisst", ch: "vergleich", layer: "netShare", years: [2100],
  takeaway: (at) => {
    const g = at.meta.global.areasGha, gha = (x: number) => x.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return `Wo Bäume kühlen (${gha(g.kuehlt)} Gha), bleiben ${pct(netShareArea(at, 2100, true))} ihrer CO₂-Wirkung; über alle ${gha(g.alle)} Gha wiederbewaldbarer Fläche nur ${pct(netShareArea(at, 2100, false))}.`;
  },
  source: `${MODEL_SRC} Albedo: Duveiller et al. 2018.`,
  notes: ["Anteil der CO₂-Wirkung, der nach dem Albedo-Effekt übrig bleibt: hoch in den Tropen, deutlich weniger oder negativ dort, wo ein Wald den Boden dunkler macht."],
};
const dacStrom: AtlasSlideDef = {
  id: "dacStrom", title: "DAC wird mit dem Strom sauber", ch: "dac", layer: "dacNet", years: [2026, 2040, 2070],
  takeaway: (at, step) => { const y = yearAt(dacStrom, step); return `${y}: Im Median bleiben ${pct(medianDacNet(at, y))} jeder entnommenen Tonne.`; },
  source: "Eigenes Modell: Sorbens-DAC mit Wärmepumpe (Sendi et al. 2022), Strommix REMIND-EU SSP2-NDC über premise.",
  notes: ["Netto-Anteil einer DAC-Tonne nach den Emissionen von Bau und Betrieb: Er hängt vom Strommix des Ortes ab und steigt, wenn der Strom sauberer wird."],
};
const dacAusbau: AtlasSlideDef = {
  id: "dacAusbau", title: "Wo DAC gebaut wird", ch: "dac", layer: "dacBuild", years: [2026, 2100],
  takeaway: (at) => `${dacCapacityGt(at, 2100).toLocaleString("de-DE", { maximumFractionDigits: 1 })} Gt CO₂ pro Jahr im Jahr 2100, an den Speichern mit dem höchsten Netto-Anteil.`,
  source: "Eigene Optimierung (Gidden et al. 2025 Speicher, Hochlauf +20 %/a).",
  notes: ["Ein Klick lässt den Ausbau von 2026 bis 2100 durchlaufen: die Optimierung baut dort, wo der Netto-Anteil am höchsten ist."],
};
const atlas: AtlasSlideDef = {
  id: "atlas", title: "Atlas", layer: "deltaT", years: [2100], free: true,
  takeaway: () => "Jede Zelle anklicken: Waldtyp, Wachstum, Antrieb, Temperatur und DAC an diesem Ort.",
  source: "Alle Daten: atlas/export_atlas.py.",
  notes: ["Freier Teil: Ebene, Jahr und Ort frei wählen; Fragen aus dem Publikum direkt an der Karte beantworten."],
};

export const SLIDES: Record<AtlasSlideId, AtlasSlideDef> = { jedeZelle, albedo, dacStrom, dacAusbau, atlas };

export const atlasSteps = (id: AtlasSlideId): number => {
  const d = SLIDES[id];
  return d.years.length - 1 + (d.sitesFrom ? 1 : 0);
};
