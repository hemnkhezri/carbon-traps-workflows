const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, ImageRun,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType, LineRuleType, TabStopType, InternalHyperlink, Bookmark,
} = require("docx");

const FIG = "/home/claude/carbon-wf-forecast/figures/";
const FONT = "Times New Roman";

// Inline markup: **bold**, ~~italic~~, _{sub}, ^{sup}; cite markers; in the main text, numbered citations and
// cross-references to sections, tables, figures and the appendix become coloured internal hyperlinks.
var LINKS = true;
const LINKC = "0563C1";
const XREF = /(?:Figs?\.|Tables?|Sections?|Appendix) (?:\d+[a-z]?(?:\.\d+)?|[A-C]\b)(?:(?:, | and | or |–)(?:\d+[a-z]?(?:\.\d+)?|[A-C]\b))*/;
const anchorOf = (kind, n) => {
  const base = n.replace(/[a-z]$/, "");
  if (kind.startsWith("Fig")) return "fig_" + base;
  if (kind.startsWith("Table")) return "tab_" + base;
  if (kind.startsWith("Appendix")) return "app_" + base;
  return "sec_" + base.replace(".", "_");
};
const link = (anchor, text, z) => new InternalHyperlink({ anchor, children: [new TextRun({ ...z, text, color: LINKC })] });
function xrefRuns(t, z) {
  const kind = t.match(/^(Figs?\.|Tables?|Sections?|Appendix)/)[0];
  const out = []; const re = /(\d+[a-z]?(?:\.\d+)?|\b[A-C]\b)/g; let last = kind.length, m, first = true;
  out.push(...[]);
  while ((m = re.exec(t)) !== null) {
    if (m.index < kind.length) continue;
    const sep = t.slice(last, m.index);
    if (first) { out.push(link(anchorOf(kind, m[0]), kind + sep + m[0], z)); first = false; }
    else { out.push(new TextRun({ ...z, text: sep })); out.push(link(anchorOf(kind, m[0]), m[0], z)); }
    last = m.index + m[0].length;
  }
  if (last < t.length) out.push(new TextRun({ ...z, text: t.slice(last) }));
  return out;
}
function citeRuns(body, z) {  // body like "1,3–5"
  const out = [new TextRun({ ...z, text: "[" })];
  body.split(/(,|–)/).forEach(p => {
    if (p === "," || p === "–") out.push(new TextRun({ ...z, text: p }));
    else if (p) out.push(LINKS ? link("ref_" + p, p, z) : new TextRun({ ...z, text: p }));
  });
  out.push(new TextRun({ ...z, text: "]" }));
  return out;
}
function runs(text, size) {
  const z = size ? { size } : {};
  const out = [];
  const re = new RegExp("(\\*\\*[^*]+\\*\\*|~~[^~]+~~|\\[\\[[^\\]]+\\]\\]|⟦[^⟧]+⟧|_\\{[^}]+\\}|\\^\\{[^}]+\\}" + (LINKS ? "|" + XREF.source : "") + ")", "g");
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ ...z, text: text.slice(last, m.index) }));
    const t = m[0];
    if (t.startsWith("**")) {
      const lab = t.slice(2, -2), mm = lab.match(/^(Fig|Table)\. ?(\d+)\.$|^Table (\d+)\.$/);
      const r = new TextRun({ ...z, text: lab, bold: true });
      out.push(LINKS && mm ? new Bookmark({ id: (mm[1] === "Fig" ? "fig_" : "tab_") + (mm[2] || mm[3]), children: [r] }) : r);
    }
    else if (t.startsWith("~~")) out.push(new TextRun({ ...z, text: t.slice(2, -2), italics: true }));
    else if (t.startsWith("_{")) out.push(new TextRun({ ...z, text: t.slice(2, -1), subScript: true }));
    else if (t.startsWith("^{")) out.push(new TextRun({ ...z, text: t.slice(2, -1), superScript: true }));
    else if (t.startsWith("⟦")) out.push(...citeRuns(t.slice(1, -1), z));
    else if (t.startsWith("[[")) out.push(new TextRun({ ...z, text: "[" + t.slice(2, -2).trim() + "]", highlight: "yellow" }));
    else out.push(...xrefRuns(t, z));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ ...z, text: text.slice(last) }));
  return out;
}
const P = (t, opts = {}) => new Paragraph({ children: runs(t), alignment: AlignmentType.JUSTIFIED, ...opts });
const secAnchor = (t) => { let m = t.match(/^(\d+)\.(\d+)\.? /); if (m) return `sec_${m[1]}_${m[2]}`; m = t.match(/^(\d+)\. /); if (m) return `sec_${m[1]}`; m = t.match(/^Appendix ([A-Z])\./); return m ? `app_${m[1]}` : null; };
const headRun = (t) => { const a = LINKS ? secAnchor(t) : null; const r = new TextRun(t); return a ? [new Bookmark({ id: a, children: [r] })] : [r]; };
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, keepNext: true, children: headRun(t) });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, children: headRun((typeof TWO !== "undefined" && TWO) ? t.replace(/^(\d+\.\d+) /, "$1. ") : t) });
// Display equation: centred text, number at right margin
const EQ = (t, n) => new Paragraph({
  tabStops: (typeof TWO !== "undefined" && TWO) ? [{ type: TabStopType.CENTER, position: 2506 }, { type: TabStopType.RIGHT, position: 5013 }] : [{ type: TabStopType.CENTER, position: 4513 }, { type: TabStopType.RIGHT, position: 9026 }],
  spacing: { before: 120, after: 120 },
  children: [new TextRun({ text: "\t" }), ...runs(t), new TextRun({ text: `\t(${n})` })],
});

// Double-column layout: items spanning both columns (wide figures, tables, algorithm) go into one-column sections.
const WIDE = new WeakSet(), CAP = new WeakSet(), NOTE = new WeakSet();
const wide = (x) => { if (typeof TWO !== "undefined" && TWO) WIDE.add(x); return x; };
function figure(file, w, h, caption) {
  const two = typeof TWO !== "undefined" && TWO, isWide = w >= 500;
  const k = !two ? 1 : (isWide ? 692 / w : 1.012727);
  return [
    wide2(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 200, line: 240, lineRule: LineRuleType.AUTO },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(FIG + file), transformation: { width: Math.round(w * k), height: Math.round(h * k) } })] }), isWide),
    wide2(new Paragraph({ alignment: AlignmentType.JUSTIFIED, style: "Caption", children: runs(caption) }), isWide),
  ];
}
function wide2(x, cond) { return cond ? wide(x) : x; }

const border = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
function table(rows, W) {
  if (typeof TWO !== "undefined" && TWO) { const s = W.reduce((a, b) => a + b, 0); W = W.map(w => Math.round(w * 10386 / s)); W[W.length - 1] += 10386 - W.reduce((a, b) => a + b, 0); }
  const cell = (text, i, { head, top, bottom }) => new TableCell({
    width: { size: W[i], type: WidthType.DXA },
    margins: { top: 50, bottom: 50, left: 80, right: 80 },
    borders: { top: top ? border : none, bottom: bottom ? border : none, left: none, right: none },
    children: [new Paragraph({ spacing: { line: 240, after: 0 }, children: runs(head ? `**${text}**` : text) })],
  });
  return wide(new Table({
    width: { size: W.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: W,
    rows: rows.map((r, ri) => new TableRow({ tableHeader: ri === 0, cantSplit: true,
      children: r.map((c, ci) => cell(c, ci, { head: ri === 0, top: ri <= 1, bottom: ri === 0 || ri === rows.length - 1 })) })),
  }));
}
const tnote = (t) => { const p = new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { before: 60, after: 200, line: 240 }, children: runs(t, (typeof TWO !== "undefined" && TWO) ? 13 : 18) }); NOTE.add(p); return p; };
const caption = (t) => { const p = new Paragraph({ keepNext: true, alignment: AlignmentType.JUSTIFIED, style: "Caption", spacing: { before: 200, after: 80, line: 276 }, children: runs(t) }); CAP.add(p); return p; };


// Table 1 (small font via TableText style)
function smallTable(rows, W, hl = -1) {
  if (typeof TWO !== "undefined" && TWO) { const s = W.reduce((a, b) => a + b, 0); W = W.map(w => Math.round(w * 10386 / s)); W[W.length - 1] += 10386 - W.reduce((a, b) => a + b, 0); }
  const cell = (text, i, { head, top, bottom, shade, last }) => new TableCell({
    width: { size: W[i], type: WidthType.DXA },
    margins: { top: 40, bottom: 40, left: 60, right: 60 },
    shading: undefined,  // Elsevier: no shading in table cells
    borders: { top: top ? border : none, bottom: bottom ? border : none, left: none, right: none },
    children: [new Paragraph({ style: "TableText", keepNext: !last, children: runs(head ? `**${text}**` : text) })],
  });
  return wide(new Table({
    width: { size: W.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: W,
    rows: rows.map((r, ri) => new TableRow({ tableHeader: ri === 0, cantSplit: true,
      children: r.map((c, ci) => cell(c, ci, { head: ri === 0 || ri === hl, top: ri <= 1 || ri === hl,
        bottom: ri === 0 || ri === rows.length - 1 || ri === hl, shade: ri === hl, last: ri === rows.length - 1 })) })),
  }));
}
