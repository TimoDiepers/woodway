import { en } from "@/i18n/en";
import { de } from "@/i18n/de";
import { translate } from "@/i18n/useT";

describe("i18n", () => {
  it("same keys in both languages, none empty", () => {
    expect(Object.keys(de).sort()).toEqual(Object.keys(en).sort());
    for (const [k, v] of Object.entries({ ...en, ...de })) expect(v, k).not.toBe("");
  });
  it("fills variables", () => {
    expect(translate("en", "panel.coolsFrom", { year: 2031 })).toBe("Cools the climate from 2031 on");
    expect(translate("de", "panel.coolsFrom", { year: 2031 })).toBe("Kühlt das Klima ab 2031");
  });
  it("the build-out sentence and its source name the spreading rule", () => {
    expect(en["panel.dacBuild"]).toBe("{mt} Mt CO₂/a capacity here in {year} (the country's capacity spread over its best cells)");
    expect(de["panel.dacBuild"]).toBe("{mt} Mt CO₂/a Kapazität hier im Jahr {year} (Kapazität des Landes, verteilt auf seine besten Zellen)");
    expect(en["src.build"]).toMatch(/spread evenly over its cells near a sediment basin with the top 10 % net share/);
    expect(de["src.build"]).toMatch(/gleichmäßig auf seine Zellen nahe einem Sedimentbecken mit den besten 10 % Netto-Anteil/);
  });
  it("same placeholders in both languages", () => {
    const vars = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    for (const k of Object.keys(en) as (keyof typeof en)[]) expect(vars(de[k]), k).toEqual(vars(en[k]));
  });
});
