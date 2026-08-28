'use strict';

const pptxgen  = require('pptxgenjs');
const H        = require('/Users/timodiepers/.claude/plugins/cache/claude-scientific-writer/claude-scientific-writer/76d7923c8f87/skills/document-skills/pptx/scripts/html2pptx.js');
const fs       = require('fs');
const os       = require('os');
const path     = require('path');

const FIGS = '/Users/timodiepers/Documents/Coding/nbs/docs/slides/figures';
const OUT  = '/Users/timodiepers/Documents/Coding/nbs/docs/slides/presentation.pptx';

// ── Farben ──────────────────────────────────────────────────────────────────
const BG   = '#F7F9F5';
const DARK = '#1E3A2F';
const AMBD = '#7A3D0A';
const GRN  = '#2D6A4F';
const MID  = '#52B788';
const LITE = '#D8F3DC';
const AMB  = '#C97D1A';
const AMBL = '#FDF0D5';
const TXT  = '#1A2320';
const SUB  = '#4B5563';
const WHT  = '#FFFFFF';
const RULE = '#C5D5CA';

// ── Hilfsfunktionen ─────────────────────────────────────────────────────────
let _n = 0;
function write(html) {
  const p = path.join(os.tmpdir(), `nbs${_n++}.html`);
  fs.writeFileSync(p, html);
  return p;
}

function page(inner, bg) {
  bg = bg || BG;
  return `<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:Arial,sans-serif;color:${TXT};}
p,h2,h3,li{margin:0;padding:0;line-height:1.4;}
ul{padding-left:16pt;}
li{margin-bottom:4pt;}
</style></head>
<body style="width:720pt;height:405pt;background:${bg};display:flex;flex-direction:column;">${inner}</body></html>`;
}

// ── Layout ───────────────────────────────────────────────────────────────────
function hdr(title, theme, kicker) {
  var bg  = theme === 'amber' ? AMBD : DARK;
  var acc = theme === 'amber' ? AMB  : MID;
  var k = kicker ? '<p style="color:' + acc + ';font-size:10.5pt;margin-bottom:2pt;letter-spacing:0.6pt;">' + kicker + '</p>' : '';
  return '<div style="height:64pt;background:' + bg + ';border-bottom:3pt solid ' + acc + ';display:flex;flex-direction:column;justify-content:center;padding:0 32pt;flex-shrink:0;">' +
    k + '<p style="color:' + WHT + ';font-size:' + (kicker ? 19 : 21) + 'pt;font-weight:bold;">' + title + '</p></div>';
}

function full(inner) {
  return '<div style="flex:1;display:flex;flex-direction:column;gap:9pt;padding:17pt 32pt 15pt 32pt;">' + inner + '</div>';
}

function two(left, right, lw) {
  lw = lw || 265;
  return '<div style="flex:1;display:flex;gap:16pt;padding:17pt 32pt 15pt 32pt;">' +
    '<div style="width:' + lw + 'pt;flex-shrink:0;display:flex;flex-direction:column;gap:9pt;">' + left + '</div>' +
    '<div style="flex:1;display:flex;align-items:center;justify-content:center;">' + right + '</div>' +
    '</div>';
}

// ── Inhaltsbausteine ─────────────────────────────────────────────────────────
function P(t, sz, c) {
  return '<p style="font-size:' + (sz||13) + 'pt;color:' + (c||TXT) + ';line-height:1.4;">' + t + '</p>';
}
function SM(t) { return P(t, 11, SUB); }
function HR()  { return '<div style="height:1pt;background:' + RULE + ';"></div>'; }

function mono(text) {
  return '<p style="font-family:\'Courier New\',monospace;font-size:11pt;color:' + GRN + ';line-height:1.5;">' + text + '</p>';
}

function callout(text, theme) {
  var bg = theme === 'amber' ? AMBL : LITE;
  var bc = theme === 'amber' ? AMB  : GRN;
  return '<div style="background:' + bg + ';border-left:5pt solid ' + bc + ';padding:7pt 12pt;">' +
    '<p style="font-size:12pt;color:' + TXT + ';line-height:1.4;">' + text + '</p></div>';
}

// Bild einbinden; fehlt die Datei, erscheint ein Platzhalter mit Dateiname
function figImg(name, maxH) {
  var p = path.join(FIGS, name);
  if (fs.existsSync(p)) {
    return '<img src="file://' + p + '" style="max-width:100%;max-height:' + (maxH||282) + 'pt;">';
  }
  return '<div style="width:100%;height:' + (maxH||282) + 'pt;background:#ECF1EE;border:2pt dashed ' + RULE + ';display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6pt;">' +
    '<p style="font-size:12pt;color:' + SUB + ';font-weight:bold;">Bild einsetzen</p>' +
    '<p style="font-family:\'Courier New\',monospace;font-size:10pt;color:' + SUB + ';">' + name + '</p>' +
    '<p style="font-size:9.5pt;color:' + SUB + ';">Prompt in bild_prompts.md</p></div>';
}

function numbered(n, title, text) {
  return '<div style="display:flex;gap:11pt;align-items:flex-start;">' +
    '<div style="width:24pt;height:24pt;background:' + DARK + ';display:flex;align-items:center;justify-content:center;flex-shrink:0;">' +
    '<p style="color:' + MID + ';font-size:14pt;font-weight:bold;">' + n + '</p></div>' +
    '<div><p style="font-size:12pt;font-weight:bold;">' + title + '</p>' +
    '<p style="font-size:11pt;color:' + SUB + ';line-height:1.35;">' + text + '</p></div></div>';
}

// Stationen der Reise: 0=Blatt … 4=Planet, -1 = keine aktiv
const STUFEN = ['Blatt', 'Baum', 'Wald', 'Luft', 'Planet'];
function navigator(active, big) {
  var h = big ? 46 : 30;
  var fs_ = big ? 13 : 10.5;
  var chips = STUFEN.map(function (s, i) {
    var aktiv = i === active;
    var davor = active >= 0 && i < active;
    var bg = aktiv ? MID : (davor ? LITE : '#EDF2EF');
    var bd = aktiv ? DARK : (davor ? GRN : RULE);
    var col = aktiv ? WHT : (davor ? GRN : '#9AA8A1');
    var fw = aktiv ? 'bold' : 'normal';
    return '<div style="flex:1;height:' + h + 'pt;background:' + bg + ';border:1.5pt solid ' + bd +
      ';display:flex;align-items:center;justify-content:center;">' +
      '<p style="font-size:' + fs_ + 'pt;color:' + col + ';font-weight:' + fw + ';">' + s + '</p></div>';
  }).join('<div style="width:7pt;"></div>');
  return '<div style="display:flex;align-items:center;">' + chips + '</div>';
}

// Bäume-Zähler
function zaehler(wert, note, theme) {
  var bc = theme === 'amber' ? AMB : GRN;
  var bg = theme === 'amber' ? AMBL : LITE;
  return '<div style="background:' + bg + ';border-left:6pt solid ' + bc + ';padding:10pt 14pt;display:flex;align-items:center;gap:14pt;">' +
    '<p style="font-size:26pt;font-weight:bold;color:' + bc + ';">' + wert + '</p>' +
    '<div><p style="font-size:12pt;font-weight:bold;color:' + TXT + ';">Bäume-Zähler</p>' +
    '<p style="font-size:10.5pt;color:' + SUB + ';">' + note + '</p></div></div>';
}

// ── Tabellen ─────────────────────────────────────────────────────────────────
function cellDiv(content, w, isHead) {
  var ws = (w !== null && w !== undefined) ? 'width:' + w + 'pt;flex-shrink:0;' : 'flex:1;';
  var tc = isHead
    ? 'color:' + WHT + ';font-size:10.5pt;font-weight:bold;'
    : 'font-size:10.5pt;color:' + TXT + ';';
  return '<div style="' + ws + 'padding-right:8pt;"><p style="' + tc + 'line-height:1.35;">' + content + '</p></div>';
}
function thdRow(cols, cws) {
  var cells = cols.map(function(c,i){ return cellDiv(c, cws ? cws[i] : null, true); }).join('');
  return '<div style="display:flex;background:' + DARK + ';padding:6pt 10pt;">' + cells + '</div>';
}
function tdRow(cols, stripe, cws) {
  var bg = stripe ? '#EBF1EE' : BG;
  var cells = cols.map(function(c,i){ return cellDiv(c, cws ? cws[i] : null, false); }).join('');
  return '<div style="display:flex;background:' + bg + ';padding:5pt 10pt;border-bottom:1pt solid ' + RULE + ';">' + cells + '</div>';
}

// Akt-Trennfolie
function aktFolie(nummer, titel, unterzeile, bild, publikum) {
  return page(
    '<div style="flex:1;display:flex;">' +
    '<div style="width:355pt;background:' + DARK + ';display:flex;flex-direction:column;justify-content:center;padding:44pt 40pt;">' +
    '<p style="color:' + MID + ';font-size:12pt;letter-spacing:1.2pt;">AKT ' + nummer + '</p>' +
    '<div style="width:52pt;height:3pt;background:' + MID + ';margin:12pt 0 16pt 0;"></div>' +
    '<p style="color:' + WHT + ';font-size:30pt;font-weight:bold;line-height:1.15;">' + titel + '</p>' +
    '<p style="color:' + MID + ';font-size:13.5pt;margin-top:14pt;line-height:1.4;">' + unterzeile + '</p>' +
    '<p style="color:#6FA888;font-size:11pt;margin-top:26pt;">' + publikum + '</p>' +
    '</div>' +
    '<div style="flex:1;display:flex;align-items:center;justify-content:center;padding:22pt;">' + figImg(bild, 340) + '</div>' +
    '</div>', DARK);
}


// Quellenzeile unter einem Inhalt
function quelle(t) {
  return '<p style="font-size:10pt;color:' + SUB + ';font-style:italic;line-height:1.35;">' + t + '</p>';
}

// Abbildung über die volle Breite, mit optionaler Bildunterschrift
function figFull(name, caption, maxH) {
  return '<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6pt;">' +
    figImg(name, maxH || 250) +
    (caption ? '<p style="font-size:10.5pt;color:' + SUB + ';font-style:italic;">' + caption + '</p>' : '') +
    '</div>';
}

// Grosse Aussage, mittig
function statement(text, sub, theme) {
  var acc = theme === 'amber' ? AMB : GRN;
  return '<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16pt;padding:30pt 56pt;">' +
    '<p style="font-size:26pt;font-weight:bold;color:' + acc + ';text-align:center;line-height:1.3;">' + text + '</p>' +
    (sub ? '<p style="font-size:14pt;color:' + TXT + ';text-align:center;line-height:1.45;">' + sub + '</p>' : '') +
    '</div>';
}

// Folie: Überschrift plus grosse Abbildung
function figPage(title, kicker, img, caption, theme) {
  return page(hdr(title, theme || null, kicker) + full(figFull(img, caption, 268)));
}

// Zeile der Reisetabelle "die Tonne / der Wald"
function reiseTabelle(zeilen) {
  var out = thdRow(['', 'die Tonne', 'der Wald'], [92, null, null]);
  zeilen.forEach(function (z, i) {
    out += tdRow([z[0], z[1], z[2]], i % 2 === 1, [92, null, null]);
  });
  return '<div style="display:flex;flex-direction:column;">' + out + '</div>';
}

// ── Hauptprogramm ────────────────────────────────────────────────────────────
async function main() {
  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_16x9';
  pptx.title  = 'Retten Bäume das Klima?';
  pptx.author = 'Timo Diepers';

  // F1 — Titel
  await H(write(page(
    '<div style="flex:1;background:' + DARK + ';display:flex;flex-direction:column;justify-content:center;padding:50pt 64pt;">' +
    '<div style="width:64pt;height:3pt;background:' + MID + ';margin-bottom:22pt;"></div>' +
    '<p style="color:' + WHT + ';font-size:40pt;font-weight:bold;line-height:1.15;">Retten Bäume das Klima?</p>' +
    '<p style="color:' + MID + ';font-size:17pt;margin-top:14pt;">Eine Reise durch die Systemgrenzen</p>' +
    '</div>', DARK)), pptx);

  // F2 — Das Häkchen
  await H(write(page(hdr('Das Häkchen') + two(
    P('Flugbuchung, letzter Schritt vor dem Bezahlen:', 12.5) +
    '<div style="background:' + LITE + ';border-left:6pt solid ' + GRN + ';padding:13pt 16pt;">' +
    '<p style="font-size:17pt;font-weight:bold;color:' + DARK + ';">„CO₂ kompensiert."</p>' +
    '<p style="font-size:11.5pt;color:' + SUB + ';margin-top:4pt;">ein paar Euro, ein Klick</p></div>' +
    P('Ab diesem Moment passieren zwei Dinge <b>gleichzeitig</b>:', 12.5),
    '<div style="display:flex;flex-direction:column;gap:14pt;">' +
    '<div style="background:#FBEAE7;border-left:6pt solid #C0392B;padding:13pt 16pt;">' +
    '<p style="font-size:15pt;font-weight:bold;color:#A5321F;">2 Tonnen CO₂ gehen in die Luft</p>' +
    '<p style="font-size:12pt;color:' + TXT + ';">jetzt, sofort</p></div>' +
    '<div style="background:' + LITE + ';border-left:6pt solid ' + GRN + ';padding:13pt 16pt;">' +
    '<p style="font-size:15pt;font-weight:bold;color:' + GRN + ';">irgendwo werden 11 Bäume gepflanzt</p>' +
    '<p style="font-size:12pt;color:' + TXT + ';">auch jetzt</p></div>' +
    '</div>'
  ))), pptx);

  // F2b — Unsere Maßeinheit
  await H(write(figPage('Unsere Maßeinheit', 'FÜR DEN GANZEN VORTRAG', 's0_einheit.png',
    'das Zertifikat rechnet mit rund 0,18 tCO₂ je Baum — genau die Größenordnung, die reale Anbieter angeben')), pptx);

  // F3 — Zwei Reisende
  await H(write(page(hdr('Zwei Reisende') + full(
    reiseTabelle([
      ['startet', 'sofort', 'sofort'],
      ['wirkt', 'ab der ersten Sekunde', '?'],
      ['bleibt', '?', '?'],
    ]) +
    '<div style="flex:1;display:flex;align-items:center;justify-content:center;">' +
    '<p style="font-size:24pt;font-weight:bold;color:' + GRN + ';text-align:center;">Treffen die sich je?<br>Und wenn ja: wann?</p></div>'
  ))), pptx);

  // F4 — Wie man das prüft
  await H(write(page(hdr('Wie man so etwas prüft') + two(
    P('Dafür braucht es zunächst kein Klimamodell — sondern einen <b>Kasten</b> und drei Fragen:', 12.5) +
    '<div style="display:flex;flex-direction:column;gap:9pt;">' +
    numbered('1', 'Was kommt rein?', '') +
    numbered('2', 'Was geht raus?', '') +
    numbered('3', 'Was bleibt liegen — und wie lange?', 'die Frage, auf die alles hinausläuft') +
    '</div>',
    '<div style="display:flex;flex-direction:column;gap:11pt;">' +
    P('Wir malen diesen Kasten heute <b>fünfmal</b>, jedes Mal größer:', 12.5) +
    navigator(-1, true) +
    quelle('Blatt · Baum · Wald · die Luft darüber · der ganze Planet') +
    '</div>'
  ))), pptx);

  // F5 — Was ein Baum den ganzen Tag macht
  await H(write(figPage('Was ein Baum den ganzen Tag macht', 'BLATT', 's1_sonne.png',
    'von 100 Einheiten Sonnenlicht auf einem Blatt · Gates (1980), Monteith & Unsworth (2013), Zhu, Long & Ort (2010)')), pptx);

  // F6 — Ein Baum ist eine Wasserpumpe
  await H(write(page(hdr('Ein Baum ist zuerst eine Wasserpumpe', null, 'BLATT') + two(
    navigator(0) +
    '<div style="display:flex;flex-direction:column;">' +
    thdRow(['von 100 Einheiten Sonne', ''], [null, 46]) +
    tdRow(['zurückgeworfen', '20'], false, [null, 46]) +
    tdRow(['als Wärme abgestrahlt', '21'], true, [null, 46]) +
    tdRow(['an die Luft abgegeben', '13'], false, [null, 46]) +
    tdRow(['<b>verdunstetes Wasser</b>', '<b>45</b>'], true, [null, 46]) +
    tdRow(['<b>zu Zucker gemacht</b>', '<b>1</b>'], false, [null, 46]) +
    '</div>',
    '<div style="display:flex;flex-direction:column;gap:12pt;">' +
    callout('Die berühmte Photosynthese ist energetisch eine <b>Randnotiz</b> — ein bis zwei Prozent.') +
    P('Und trotzdem reden alle über genau diesen kleinsten Posten.', 13.5) +
    P('Warum?', 20, GRN) +
    '</div>'
  ))), pptx);

  // F7 — Wo der Zucker landet
  await H(write(figPage('Wo der Zucker landet', 'BAUM', 's2_zucker.png',
    'Kohlenstoffnutzungseffizienz NPP/GPP ≈ 0,45–0,55 · Waring et al. (1998), DeLucia et al. (2007)')), pptx);

  // F8 — Der größte Speicher
  await H(write(page(hdr('Der größte Speicher steht nicht — er liegt', null, 'WALD') + two(
    navigator(2) +
    P('Ein Hektar Wald bei 45 °N:', 12.5) +
    '<div style="display:flex;flex-direction:column;">' +
    thdRow(['Speicher', 'je ha', 'bleibt'], [null, 58, 92]) +
    tdRow(['Blätter, Feinwurzeln', '~8 tC', 'Jahre'], false, [null, 58, 92]) +
    tdRow(['Holz', '~92 tC', 'Jahrzehnte'], true, [null, 58, 92]) +
    tdRow(['<b>Boden</b>', '<b>~100 tC</b>', '<b>Jahrhunderte</b>'], false, [null, 58, 92]) +
    '</div>' +
    quelle('Größenordnungen nach Jobbágy &amp; Jackson (2000)') +
    callout('Und dieser Speicher hat eine <b>Leckrate</b>: Feuer, Käfer, Dürre.', 'amber'),
    figImg('s3_speicher.png')
  ))), pptx);

  // F9 — Zwischenstand Wald
  await H(write(page(hdr('Zwischenstand: der Wald') + full(
    '<div style="display:flex;gap:14pt;">' +
    '<div style="flex:1;background:' + LITE + ';border-left:6pt solid ' + GRN + ';padding:13pt 16pt;">' +
    '<p style="font-size:15pt;font-weight:bold;color:' + GRN + ';">langsam</p>' +
    '<p style="font-size:12pt;">Jahrzehnte, bis der Speicher gefüllt ist</p></div>' +
    '<div style="flex:1;background:' + AMBL + ';border-left:6pt solid ' + AMB + ';padding:13pt 16pt;">' +
    '<p style="font-size:15pt;font-weight:bold;color:' + AMBD + ';">nicht garantiert</p>' +
    '<p style="font-size:12pt;">was drin ist, muss nicht drin bleiben</p></div>' +
    '</div>' +
    reiseTabelle([
      ['wirkt', 'ab der ersten Sekunde', 'nach Jahrzehnten'],
      ['bleibt', '?', 'solange nichts passiert'],
    ]) +
    SM('Jetzt wechseln wir zum anderen Reisenden.')
  ))), pptx);

  // F10 — Wohin die Tonne verschwindet
  await H(write(figPage('Wohin die Tonne verschwindet', 'DIE TONNE', 's4_tonne.png',
    'Impulsantwort des Kohlenstoffkreislaufs · Joos et al. (2013)')), pptx);

  // F11 — Warum ein Prozent gewinnt
  await H(write(page(hdr('Warum ein Prozent gewinnt') + two(
    '<div style="display:flex;flex-direction:column;">' +
    thdRow(['', 'am Blatt', 'in der Luft'], [88, 76, null]) +
    tdRow(['<b>Wasser</b>', '45 von 100', 'nach 9 Tagen wieder unten'], false, [88, 76, null]) +
    tdRow(['<b>Kohlenstoff</b>', '1 von 100', 'nach 100 Jahren noch zu 41 % da'], true, [88, 76, null]) +
    '</div>',
    '<div style="display:flex;align-items:center;justify-content:center;height:100%;">' +
    '<p style="font-size:21pt;font-weight:bold;color:' + GRN + ';line-height:1.35;">Klima ist nicht das,<br>was am meisten Energie bewegt.<br><br>Klima ist das,<br>was liegen bleibt.</p></div>'
  ), 300)), pptx);

  // F12 — Alle Uhren
  await H(write(figPage('Alle Uhren nebeneinander', 'DER DREHPUNKT', 's5_uhren.png',
    'alles im System hat eine Uhr — nur die Buchung hat keine')), pptx);

  // F13 — Zweite Uhr
  await H(write(figPage('Es gibt noch eine zweite Uhr', 'DER WALD TUT MEHR', 's6_zwei_uhren.png',
    'ein Wald ist auch dunkler und feuchter als das, was vorher da war')), pptx);

  // F14 — Messungen
  await H(write(page(hdr('Was Messungen dazu sagen') + full(
    '<div style="display:flex;flex-direction:column;gap:8pt;">' +
    numbered('1', 'Lee et al. (2011), Nature', 'Nördlich von etwa 45 °N ist Wald tagsüber wärmer als offenes Land, südlich davon kühler.') +
    numbered('2', 'Alkama &amp; Cescatti (2016), Science', 'Satellitendaten realer Waldverluste 2003–2012 — derselbe Effekt, weltweit, mit klarem Nord-Süd-Verlauf.') +
    numbered('3', 'Duveiller et al. (2018), Nat. Commun.', 'Karten der Temperaturwirkung für jeden Vegetationsübergang.') +
    numbered('4', 'Winckler et al. (2019)', 'Ein Teil der Wirkung bleibt lokal, ein ebenso großer Teil wird vom Wind verteilt.') +
    '</div>' +
    callout('Alle diese Messungen zeigen die <b>Oberfläche</b> — nicht den Planeten. Genau deshalb reicht Erzählen ab hier nicht mehr.')
  ))), pptx);

  // F15 — Ab hier rechnen
  await H(write(page(hdr('Ab hier müssen wir rechnen', 'amber') + full(
    P('Drei Fragen hat die Geschichte aufgeworfen, die man nicht erzählen, sondern nur rechnen kann:', 13) +
    '<div style="display:flex;flex-direction:column;gap:10pt;">' +
    numbered('1', 'Wie vergleicht man Kohlenstoff, Albedo und Verdunstung?', 'Drei völlig verschiedene Effekte, eine Bilanz.') +
    numbered('2', 'Wie wird aus einem Stück Wald eine Größe für den Planeten?', 'Lokal gemessen, global gefragt.') +
    numbered('3', 'Wie wird aus all dem eine Temperatur?', 'Und wann?') +
    '</div>' +
    SM('Für ein paar Folien wird es technisch — danach kommen die Ergebnisse.')
  ))), pptx);

  // F16 — gemeinsame Währung
  await H(write(page(hdr('Problem 1: eine gemeinsame Währung', null, 'DIE LUFT') + full(
    P('Jeder Effekt wird in dieselbe Einheit übersetzt: <b>wie stark er das Energiegleichgewicht der Erde verschiebt</b> — in Watt pro Quadratmeter.', 12.5) +
    figFull('gl_4.png', null, 250)
  ))), pptx);

  // F17 — Flächenwichtung
  await H(write(page(hdr('Problem 2: von einem Waldstück zum Planeten', null, 'DIE LUFT') + two(
    navigator(3) +
    mono('ΔF_global = (A_Wald / A_Erde) · ΔF_lokal') +
    P('Ein Megahektar ist <b>2·10⁻⁵</b> der Erdoberfläche. Lokal +1,15 W/m² werden global zu +2,3·10⁻⁵ W/m².', 12.5) +
    quelle('Betts (2000), Nature · Bright et al. (2015)'),
    '<div style="display:flex;flex-direction:column;gap:11pt;">' +
    '<div style="background:' + LITE + ';border-left:6pt solid ' + GRN + ';padding:11pt 14pt;">' +
    '<p style="font-size:13pt;font-weight:bold;color:' + GRN + ';">Kohlenstoff</p>' +
    '<p style="font-size:11.5pt;">wirkt überall — egal, wo er weggenommen wurde</p></div>' +
    '<div style="background:' + AMBL + ';border-left:6pt solid ' + AMB + ';padding:11pt 14pt;">' +
    '<p style="font-size:13pt;font-weight:bold;color:' + AMBD + ';">Albedo und Verdunstung</p>' +
    '<p style="font-size:11.5pt;">wirken nur dort, wo der Wald steht</p></div>' +
    callout('Deshalb sind „im Wald ist es kühler" und „der Planet wird kühler" zwei verschiedene Aussagen.') +
    '</div>'
  ))), pptx);

  // F18 — Antrieb zu Temperatur
  await H(write(page(hdr('Problem 3: aus Antrieb wird Temperatur', null, 'DER PLANET') + full(
    P('Der Ozean schluckt <b>91 %</b> der Zusatzenergie und gibt sie über Jahrhunderte zurück — die dritte Uhr.', 12.5) +
    figFull('gl_5.png', null, 250)
  ))), pptx);

  // F19 — FaIR
  await H(write(page(hdr('Das Modell') + two(
    P('<b>FaIR v2.2</b>', 15, GRN) +
    '<ul>' +
    '<li>' + P('Impulsantwortmodell: vier Kohlenstoffboxen, Ozean-Schichtmodell', 12) + '</li>' +
    '<li>' + P('am CMIP6-Ensemble kalibriert', 12) + '</li>' +
    '<li>' + P('in IPCC AR6 für die Erwärmungsprojektionen benutzt', 12) + '</li>' +
    '<li>' + P('läuft auf einem Laptop in Sekunden', 12) + '</li>' +
    '</ul>' +
    quelle('Millar et al. (2017) · Leach et al. (2021) · AR6-Kalibrierung'),
    callout('Bewusst kein Erdsystemmodell: Wir stellen eine <b>Bilanzfrage</b>, keine Regionalprognose. Jede Zahl im Vortrag ist reproduzierbar.')
  ))), pptx);

  // F20 — Architektur
  await H(write(figPage('Die Stationen sind die Bausteine', 'DER PAYOFF', 'architektur.png',
    'wir haben das Modell nicht erklärt — wir sind hindurchgelaufen')), pptx);

  // F21 — Messlatte
  await H(write(page(hdr('Die Messlatte') + two(
    P('Wie viele Bäume braucht es tatsächlich für eine Tonne?', 13) +
    mono('Erwärmung, die die Tonne verursacht') +
    mono('─────────────────────────────────') +
    mono('Erwärmung, die der Wald verhindert') +
    SM('beide Seiten je Tonne, Zeitraum bis 2100'),
    '<div style="display:flex;flex-direction:column;gap:12pt;">' +
    '<div style="background:' + LITE + ';border-left:6pt solid ' + GRN + ';padding:12pt 16pt;">' +
    '<p style="font-size:20pt;font-weight:bold;color:' + GRN + ';">1</p>' +
    '<p style="font-size:12pt;">die Rechnung vom Anfang stimmt</p></div>' +
    '<div style="background:' + AMBL + ';border-left:6pt solid ' + AMB + ';padding:12pt 16pt;">' +
    '<p style="font-size:20pt;font-weight:bold;color:' + AMBD + ';">größer als 1</p>' +
    '<p style="font-size:12pt;">so viel mehr Wald bräuchte es</p></div>' +
    '</div>'
  ))), pptx);

  // F22 — Fläche laut Zertifikat
  await H(write(page(hdr('Was das Zertifikat für unseren Flug bucht') + two(
    '<div style="display:flex;flex-direction:column;">' +
    thdRow(['Pflanzort', 'Bäume', 'Fläche'], [null, 62, 68]) +
    tdRow(['0 °N tropisch', '5', '27 m²'], false, [null, 62, 68]) +
    tdRow(['30 °N', '9', '45 m²'], true, [null, 62, 68]) +
    tdRow(['45 °N', '11', '55 m²'], false, [null, 62, 68]) +
    tdRow(['60 °N boreal', '11', '55 m²'], true, [null, 62, 68]) +
    '</div>' +
    SM('In den Tropen reichen rechnerisch weniger Bäume — dort steht mehr Biomasse je Hektar.'),
    callout('Damit die Ergebnisse fair sind, pflanzen wir im Modell <b>genau so viel, wie das Zertifikat verlangt</b> — nicht mehr, nicht weniger.')
  ))), pptx);

  // F23 — Station für Station
  await H(write(page(hdr('Station für Station: was übrig bleibt') + two(
    P('45 °N — Bäume für unseren einen Flug:', 12.5) +
    '<div style="display:flex;flex-direction:column;">' +
    thdRow(['Station', 'Bäume'], [null, 62]) +
    tdRow(['wie das Zertifikat rechnet', '<b>11</b>'], false, [null, 62]) +
    tdRow(['der Baum wächst erst', '27'], true, [null, 62]) +
    tdRow(['Boden und Störungen', '67'], false, [null, 62]) +
    tdRow(['Albedo und Verdunstung', '<b>82</b>'], true, [null, 62]) +
    '</div>' +
    SM('SSP2-4.5 · bis 2100 · FaIR v2.2'),
    figImg('r2_reise_45N.png')
  ))), pptx);

  // F24 — Treffen sie sich
  await H(write(figPage('Treffen sie sich?', 'DIE ANTWORT', 'r1_treffen.png',
    'links: mit den 11 Bäumen des Zertifikats — nie · rechts: mit 82 Bäumen')), pptx);

  // F25 — Ort
  await H(write(page(hdr('Derselbe Flug, anderer Pflanzort') + two(
    '<div style="display:flex;flex-direction:column;">' +
    thdRow(['Pflanzort', 'verkauft', 'nötig'], [null, 68, 62]) +
    tdRow(['0 °N tropisch', '5 Bäume', '8'], false, [null, 68, 62]) +
    tdRow(['30 °N', '9', '34'], true, [null, 68, 62]) +
    tdRow(['45 °N', '11', '82'], false, [null, 68, 62]) +
    tdRow(['<b>60 °N boreal</b>', '<b>11</b>', '<b>443</b>'], true, [null, 68, 62]) +
    '</div>' +
    callout('In den Tropen fehlen drei Bäume. In Nordskandinavien fehlen 432 — statt 55 m² bräuchte der Flug dort <b>2200 m²</b>, ein halber Fußballplatz.', 'amber'),
    figImg('r3_orte.png')
  ))), pptx);

  // F26 — Einmal rauszoomen
  await H(write(page(hdr('Einmal rauszoomen', null, 'EINMAL, UND NUR EINMAL') + two(
    P('Bisher ging es um <b>einen</b> Flug. Jetzt einmal der Blick auf die Welt:', 12.5) +
    '<div style="display:flex;flex-direction:column;">' +
    thdRow(['', ''], [null, 108]) +
    tdRow(['ein Flug', '11 → 82 Bäume'], false, [null, 108]) +
    tdRow(['<b>alle Flüge eines Jahres</b>', '<b>rund 1 GtCO₂</b>'], true, [null, 108]) +
    tdRow(['dafür nötige Fläche bei 45 °N', '<b>20 Mha</b>'], false, [null, 108]) +
    '</div>' +
    quelle('Luftverkehr 2024: 942 MtCO₂ (IATA)'),
    callout('Ein einziges Jahr Luftverkehr bräuchte bei 45 °N <b>mehr Neuwald, als die Great Green Wall in 18 Jahren geschafft hat.</b>', 'amber')
  ))), pptx);

  // F26b — Vergleich mit echten Programmen
  await H(write(figPage('Im Vergleich zu echten Programmen', 'MASSSTAB', 'r4_vergleich.png',
    'Bonn Challenge / IUCN · UNCCD Great Green Wall · FAO FRA 2020 · IATA (2024)')), pptx);

  // F26c — was hängen bleiben soll
  await H(write(page(hdr('Zwei Sätze, die hängen bleiben', null, 'MASSSTAB') + full(
    '<div style="display:flex;flex-direction:column;gap:12pt;">' +
    numbered('1', 'Ein Jahr Luftverkehr', 'bräuchte bei 45 °N rund 20 Mha Neuwald — mehr, als die Great Green Wall seit 2007 geschafft hat (18 Mha).') +
    numbered('2', 'Die Bonn Challenge komplett', '350 Mha, das größte Aufforstungsprogramm der Welt, entspricht bei 45 °N rund 17 GtCO₂ — knapp fünf Monate der weltweiten Emissionen.') +
    '</div>' +
    callout('Und zurück zum Anfang: Das Zertifikat verkauft <b>11 Bäume</b> für den Flug. Physikalisch wären es bei 45 °N <b>82</b>.')
  ))), pptx);

  // F27 — wärmere Welt
  await H(write(page(hdr('Und in einer wärmeren Welt?') + two(
    P('Je wärmer der Hintergrund:', 12.5) +
    '<ul>' +
    '<li>' + P('desto stärker atmet der Boden', 12.5) + '</li>' +
    '<li>' + P('desto häufiger die Störungen', 12.5) + '</li>' +
    '<li>' + P('desto schwächer die Senke', 12.5) + '</li>' +
    '</ul>' +
    callout('Die Welt, in der am meisten kompensiert würde, ist die, in der Kompensation am schlechtesten funktioniert.', 'amber'),
    figImg('12_ssp_sensitivity.png')
  ))), pptx);

  // F28 — Tabelle gefüllt
  await H(write(page(hdr('Die Tabelle vom Anfang, gefüllt') + full(
    reiseTabelle([
      ['wirkt', 'ab der ersten Sekunde', 'nach Jahrzehnten'],
      ['bleibt', 'Jahrhunderte', 'solange nichts passiert'],
      ['wirkt wo', 'überall', 'Kohlenstoff überall, Albedo nur vor Ort'],
    ]) +
    '<div style="flex:1;display:flex;align-items:center;justify-content:center;">' +
    '<p style="font-size:20pt;font-weight:bold;color:' + AMBD + ';text-align:center;">Treffen sie sich?<br>Nicht bei der Fläche, die gebucht wurde.</p></div>'
  ))), pptx);

  // F29 — Antwort
  await H(write(page(hdr('Also: retten Bäume das Klima?') + full(
    P('<b>Ja — als Senke. Nein — als Freikaufschein.</b>', 16, GRN) +
    '<div style="display:flex;flex-direction:column;gap:8pt;">' +
    numbered('1', 'Ein Wald ist ein Speicher mit Anlaufzeit und Leckrate', 'kein Rückgängigmachen.') +
    numbered('2', 'Wo gepflanzt wird, entscheidet', 'Faktor 1,4 oder Faktor 40.') +
    numbered('3', 'Was lokal kühlt, muss global nicht kühlen', 'Oberfläche ist nicht Planet.') +
    numbered('4', 'Kompensation verrechnet zwei verschiedene Uhren', 'sofort und für immer gegen Jahrzehnte und vielleicht.') +
    '</div>'
  ))), pptx);

  // F30 — Was ausgeschlossen bleibt
  await H(write(page(hdr('Was auch unser Kasten ausschließt') + two(
    '<ul>' +
    '<li>' + P('Biodiversität und Ökosystemleistungen', 12.5) + '</li>' +
    '<li>' + P('regionaler Wasserhaushalt, Abfluss, Dürrerisiko', 12.5) + '</li>' +
    '<li>' + P('Flächenkonkurrenz zur Nahrungsmittelproduktion', 12.5) + '</li>' +
    '<li>' + P('Landrechte und Verteilungsfragen', 12.5) + '</li>' +
    '</ul>' +
    HR() +
    mono('github.com/[repo]/nbs') +
    SM('Modell, Parameter und alle Abbildungen reproduzierbar'),
    callout('Eine Bilanz beantwortet exakt die Frage, die man ihr stellt. Die Arbeit steckt darin, den Kasten richtig zu ziehen.')
  ))), pptx);

  // ── Anhänge ───────────────────────────────────────────────────────────────
  await H(write(page(hdr('Anhang A — Die Bilanz an jeder Station') + full(
    '<div style="display:flex;flex-direction:column;">' +
    thdRow(['Station', 'Bilanz'], [96, null]) +
    tdRow(['Blatt', '0 = (1−α)S↓ − εσT⁴ − H − LE − Ẇ_chem'], false, [96, null]) +
    tdRow(['Baum', 'dC_B/dt = GPP − R_a − Λ'], true, [96, null]) +
    tdRow(['Wald', 'R_n = H + LE + G,  β = H/LE'], false, [96, null]) +
    tdRow(['Luft', 'ΔN = ΔF − λΔT,  ΔF = ΔF_CO₂ + f_A(ΔF_α + ΔF_LE)'], true, [96, null]) +
    tdRow(['Planet', 'C dΔT/dt = ΔF − λΔT − γ(ΔT − ΔT_d)'], false, [96, null]) +
    tdRow(['Zeit', 'ΔT(t) = ∫₀ᵗ R(t−t′) ΔF(t′) dt′'], true, [96, null]) +
    '</div>' +
    SM('ausführliche Fassung mit Zahlenwerten: gl_1.png bis gl_6.png, kv_1.png bis kv_6.png')
  ))), pptx);

  await H(write(page(hdr('Anhang B — Parameter') + full(
    '<div style="display:flex;flex-direction:column;">' +
    thdRow(['Parameter', 'Wert', 'Quelle'], [128, null, 168]) +
    tdRow(['Wachstum', 'Chapman-Richards, B_max 100–200 tC/ha, k 0,03–0,08 a⁻¹', 'IPCC, Pan et al. (2011)'], false, [128, null, 168]) +
    tdRow(['ΔF_α lokal', '−0,30 (0 °N) … +1,15 W/m² (60 °N)', 'Bonan (2008), Duveiller (2018)'], true, [128, null, 168]) +
    tdRow(['ΔF_LE lokal', '−1,5 (0 °N) … −0,1 W/m² (60 °N)', 'Bonan (2008)'], false, [128, null, 168]) +
    tdRow(['Q₁₀', '2,0', 'Davidson &amp; Janssens (2006)'], true, [128, null, 168]) +
    tdRow(['SOC-Angleichung μ', '0,03 a⁻¹', 'Modellannahme'], false, [128, null, 168]) +
    tdRow(['Störungsrate', '0,5 %/a tropisch, 1,0 %/a boreal, +50 % bis 2150', 'Modellannahme'], true, [128, null, 168]) +
    tdRow(['λ', '1,3 W/m²K', 'Sherwood et al. (2020)'], false, [128, null, 168]) +
    tdRow(['A_Erde', '5,1006·10¹⁴ m²', '—'], true, [128, null, 168]) +
    '</div>'
  ))), pptx);

  await H(write(page(hdr('Anhang C — Ergebnisse vollständig (SSP2-4.5, bis 2100)') + full(
    '<div style="display:flex;flex-direction:column;">' +
    thdRow(['Station', '0 °N', '30 °N', '45 °N', '60 °N'], [null, 74, 74, 74, 74]) +
    tdRow(['wie das Zertifikat rechnet', '1,00', '1,00', '1,00', '1,00'], false, [null, 74, 74, 74, 74]) +
    tdRow(['der Baum wächst erst', '1,43', '1,70', '2,50', '2,50'], true, [null, 74, 74, 74, 74]) +
    tdRow(['Boden und Störungen', '1,54', '3,46', '6,14', '11,86'], false, [null, 74, 74, 74, 74]) +
    tdRow(['<b>Albedo und Verdunstung</b>', '<b>1,43</b>', '<b>3,78</b>', '<b>7,48</b>', '<b>40,58</b>'], true, [null, 74, 74, 74, 74]) +
    '</div>' +
    SM('Erwärmungsschuld bei zertifikatsgroßer Fläche [mK·a]: 0 °N 38 · 30 °N 88 · 45 °N 90 · 60 °N 101')
  ))), pptx);

  await H(write(page(hdr('Anhang D — Literatur') + full(
    '<div style="display:flex;gap:16pt;">' +
    '<div style="flex:1;display:flex;flex-direction:column;gap:3pt;">' +
    P('<b>Blatt, Baum, Bestand</b>', 11, GRN) +
    quelle('Gates (1980) · Jarvis &amp; McNaughton (1986)') +
    quelle('Monteith &amp; Unsworth (2013)') +
    quelle('Zhu, Long &amp; Ort (2010)') +
    quelle('Waring et al. (1998) · DeLucia et al. (2007)') +
    quelle('Jobbágy &amp; Jackson (2000) · Pan et al. (2011)') +
    quelle('Davidson &amp; Janssens (2006)') +
    '</div>' +
    '<div style="flex:1;display:flex;flex-direction:column;gap:3pt;">' +
    P('<b>Biophysik der Landnutzung</b>', 11, GRN) +
    quelle('Betts (2000) · Bala et al. (2007)') +
    quelle('Bonan (2008) · Lee et al. (2011)') +
    quelle('Bright et al. (2015, 2017)') +
    quelle('Alkama &amp; Cescatti (2016)') +
    quelle('Duveiller et al. (2018)') +
    quelle('Winckler et al. (2019)') +
    '</div>' +
    '<div style="flex:1;display:flex;flex-direction:column;gap:3pt;">' +
    P('<b>Klimasystem und Bilanzierung</b>', 11, GRN) +
    quelle('Myhre et al. (1998) · Etminan et al. (2016)') +
    quelle('Joos et al. (2013)') +
    quelle('Millar et al. (2017) · Leach et al. (2021)') +
    quelle('Sherwood et al. (2020)') +
    quelle('von Schuckmann et al. (2020) · IPCC AR6') +
    quelle('Kirschbaum (2006) · Levasseur et al. (2010) · Sierra et al. (2021)') +
    '</div>' +
    '</div>'
  ))), pptx);

  await pptx.writeFile({ fileName: OUT });
  console.log('Fertig:', OUT);
}

main().catch(function(e){ console.error(e); process.exit(1); });
