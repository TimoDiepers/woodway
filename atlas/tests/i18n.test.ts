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
});
