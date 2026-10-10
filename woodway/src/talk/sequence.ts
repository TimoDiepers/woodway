import { DECK_TITLES, deckIndex } from "./deckSlides";

export type AtlasSlideId = "jedeZelle" | "albedo" | "dacStrom" | "dacAusbau" | "atlas";
export type Item = { kind: "deck"; i: number } | { kind: "atlas"; id: AtlasSlideId };

export const ANCHORS: { id: AtlasSlideId; after: string }[] = [
  { id: "jedeZelle", after: "Temperaturwirkung eines Baums je Ort" },
  { id: "albedo", after: "Temperaturwirkung eines Baums je Ort" },
  { id: "dacStrom", after: "DAC-Modell" },
  { id: "dacAusbau", after: "DAC-Ausbau" },
  { id: "atlas", after: "Woodway: alle Ergebnisse interaktiv" },
];

export const SEQUENCE: Item[] = DECK_TITLES.flatMap((title, i) => [
  { kind: "deck", i } as Item,
  ...ANCHORS.filter((a) => a.after === title).map((a) => ({ kind: "atlas", id: a.id }) as Item),
]);

export const MAIN_END = SEQUENCE.findIndex((s) => s.kind === "deck" && s.i === deckIndex("Danke") + 1);
