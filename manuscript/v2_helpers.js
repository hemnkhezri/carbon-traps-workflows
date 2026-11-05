const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, ImageRun,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType, LineRuleType, TabStopType,
} = require("docx");

const FIG = "/home/claude/carbon-wf-forecast/figures/";
const FONT = "Times New Roman";

// Inline markup: **bold**, _italic_, cite markers -> yellow placeholder
function runs(text) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|~~[^~]+~~|\[\[[^\]]+\]\])/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index) }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true }));
    else if (t.startsWith("~~")) out.push(new TextRun({ text: t.slice(2, -2), italics: true }));
    else out.push(new TextRun({ text: "[" + t.slice(2, -2).trim() + "]", highlight: "yellow" }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last) }));
  return out;
}
const P = (t, opts = {}) => new Paragraph({ children: runs(t), alignment: AlignmentType.JUSTIFIED, ...opts });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, keepNext: true, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, children: [new TextRun(t)] });
// Display equation: centred text, number at right margin
const EQ = (t, n) => new Paragraph({
  tabStops: [{ type: TabStopType.CENTER, position: 4513 }, { type: TabStopType.RIGHT, position: 9026 }],
  spacing: { before: 120, after: 120 },
  children: [new TextRun({ text: "\t" }), ...runs(t), new TextRun({ text: `\t(${n})` })],
});

function figure(file, w, h, caption) {
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 200 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(FIG + file), transformation: (typeof TWO !== 'undefined' && TWO) ? { width: Math.round(w * 0.53), height: Math.round(h * 0.53) } : { width: w, height: h } })] }),
    new Paragraph({ alignment: AlignmentType.JUSTIFIED, style: "Caption", children: runs(caption) }),
  ];
}

const border = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
function table(rows, W) {
  const cell = (text, i, { head, top, bottom }) => new TableCell({
    width: { size: W[i], type: WidthType.DXA },
    margins: { top: 50, bottom: 50, left: 80, right: 80 },
    borders: { top: top ? border : none, bottom: bottom ? border : none, left: none, right: none },
    children: [new Paragraph({ spacing: { line: 240, after: 0 }, children: runs(head ? `**${text}**` : text) })],
  });
  return new Table({
    width: { size: W.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: W,
    rows: rows.map((r, ri) => new TableRow({ tableHeader: ri === 0, cantSplit: true,
      children: r.map((c, ci) => cell(c, ci, { head: ri === 0, top: ri <= 1, bottom: ri === 0 || ri === rows.length - 1 })) })),
  });
}
const caption = (t) => new Paragraph({ keepNext: true, spacing: { before: 200, after: 80 }, children: runs(t) });


// Table 1 (small font via TableText style)
function smallTable(rows, W, hl = -1) {
  const cell = (text, i, { head, top, bottom, shade }) => new TableCell({
    width: { size: W[i], type: WidthType.DXA },
    margins: { top: 40, bottom: 40, left: 60, right: 60 },
    shading: shade ? { type: ShadingType.CLEAR, fill: "EEF4FB" } : undefined,
    borders: { top: top ? border : none, bottom: bottom ? border : none, left: none, right: none },
    children: [new Paragraph({ style: "TableText", children: runs(head ? `**${text}**` : text) })],
  });
  return new Table({
    width: { size: W.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: W,
    rows: rows.map((r, ri) => new TableRow({ tableHeader: ri === 0, cantSplit: true,
      children: r.map((c, ci) => cell(c, ci, { head: ri === 0 || ri === hl, top: ri <= 1 || ri === hl,
        bottom: ri === 0 || ri === rows.length - 1 || ri === hl, shade: ri === hl })) })),
  });
}
