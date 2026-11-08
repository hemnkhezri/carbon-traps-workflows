// Build Manuscript v2: helpers + math + revision sections + content; placeholders filled from v2_fill.json.
const fs = require("fs"), path = require("path"), vm = require("vm");
const TWO = process.env.LAYOUT === "2col";
const fill = fs.existsSync(path.join(__dirname, "v2_fill.json")) ? JSON.parse(fs.readFileSync(path.join(__dirname, "v2_fill.json"), "utf8")) : {};
let src = ["v2_helpers.js", "v2_math.js", "v2_revision.js", "v2_content.js"].map(f => fs.readFileSync(path.join(__dirname, f), "utf8")).join("\n");
src = src.replace(/«([A-Z0-9_]+)»/g, (m, k) => (k in fill ? fill[k].replace(/"/g, '\\"') : `[TO FILL: ${k}]`));
// Numbered citations (Elsevier style) in order of first appearance, when cite_order.json exists (pass 2).
const ORDER = fs.existsSync(path.join(__dirname, "cite_order.json")) ? JSON.parse(fs.readFileSync(path.join(__dirname, "cite_order.json"), "utf8")) : null;
const REFS = fs.existsSync(path.join(__dirname, "refs.json")) && ORDER ? JSON.parse(fs.readFileSync(path.join(__dirname, "refs.json"), "utf8")) : null;
if (ORDER) {
  const num = Object.fromEntries(ORDER.map((k, i) => [k, i + 1]));
  src = src.replace(/\[\[cite: [^\]]+\]\](?:\s*\[\[cite: [^\]]+\]\])*/g, (m) => {
    const ns = [...m.matchAll(/\[\[cite: ([^\]]+)\]\]/g)].map(x => { if (!(x[1] in num)) throw new Error("uncited key " + x[1]); return num[x[1]]; });
    const u = [...new Set(ns)].sort((a, b) => a - b); const parts = [];
    for (let i = 0; i < u.length; ) { let j = i; while (j + 1 < u.length && u[j + 1] === u[j] + 1) j++;
      parts.push(j - i >= 2 ? `${u[i]}–${u[j]}` : (j > i ? `${u[i]},${u[j]}` : `${u[i]}`)); i = j + 1; }
    return "⟦" + parts.join(",") + "⟧";
  });
  src = src.replace('P("[Insert with the Zotero Word plug-in, Elsevier numbered style.]"),',
    "...REFS.map((r, i) => new Paragraph({ alignment: AlignmentType.LEFT, indent: { left: TWO ? 360 : 480, hanging: TWO ? 360 : 480 }, spacing: { line: TWO ? 200 : 260, after: TWO ? 20 : 60 }, children: [new Bookmark({ id: `ref_${i + 1}`, children: [new TextRun({ text: `[${i + 1}]`, size: TWO ? 15 : 20 })] }), new TextRun({ text: `\\t` + r, size: TWO ? 15 : 20 })], tabStops: [{ type: TabStopType.LEFT, position: 480 }] })),");
}
src += `
const { Footer, PageNumber, SectionType } = require("docx");
const all = [...front, ...intro, ...related, ...model, ...scheds, ...design, ...results, ...discussion, ...conclusion, ...declarations, ...appendices];
const STY = {
    default: { document: { run: { font: FONT, size: TWO ? 18 : 24 }, paragraph: { spacing: { line: TWO ? 228 : 360, lineRule: LineRuleType.AUTO, after: 120 } } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: TWO ? 22 : 28, bold: true }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: TWO ? 20 : 24, bold: true, italics: true }, paragraph: { spacing: { before: 240, after: 80 }, outlineLevel: 1 } },
      { id: "Caption", name: "Caption", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: TWO ? 17 : 20 }, paragraph: { spacing: { line: TWO ? 240 : 276, after: TWO ? 160 : 240 } } },
      { id: "TableText", name: "Table Text", basedOn: "Normal", quickFormat: true, run: { font: FONT, size: TWO ? 16 : 18 }, paragraph: { spacing: { line: 220, after: 0 } } },
    ],
  };
const PAGE = { size: { width: 11906, height: 16838 }, margin: TWO ? { top: 1000, bottom: 1000, left: 900, right: 900 } : { top: 1440, bottom: 1440, left: 1440, right: 1440 } };
const LN = TWO ? undefined : { countBy: 1, restart: require("docx").LineNumberRestartFormat.CONTINUOUS, distance: 300 };
const FOOT = { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT] })] })] }) };
let sections;
if (!TWO) {
  sections = [{ properties: { page: PAGE, lineNumbers: LN }, footers: FOOT, children: all }];
} else {
  // one-column front matter, then two columns; wide figures, tables and the algorithm span the page in one-column sections
  const body = all.slice(front.length);
  const flag = body.map(x => WIDE.has(x));
  for (let i = 0; i < body.length; i++) if (CAP.has(body[i]) && i + 1 < body.length && WIDE.has(body[i + 1])) flag[i] = true;
  for (let i = 1; i < body.length; i++) if (NOTE.has(body[i]) && flag[i - 1]) flag[i] = true;
  sections = [{ properties: { page: PAGE, lineNumbers: LN, column: { count: 1 } }, footers: FOOT, children: front }];
  let i = 0;
  while (i < body.length) {
    let j = i; while (j < body.length && flag[j] === flag[i]) j++;
    sections.push({ properties: { type: SectionType.CONTINUOUS, page: PAGE, lineNumbers: LN, column: flag[i] ? { count: 1 } : { count: 2, space: 400 } }, footers: FOOT, children: body.slice(i, j) });
    i = j;
  }
}
const doc = new Document({ styles: STY, sections });
const sdoc = new Document({ styles: STY, sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } }, children: supplementary }] });
if (!TWO) Packer.toBuffer(sdoc).then(b => fs.writeFileSync(path.join(__dirname, "Supplementary_Material.docx"), b));
Packer.toBuffer(doc).then(b => { fs.writeFileSync(path.join(__dirname, TWO ? "Manuscript_2col.docx" : "Manuscript_v2.docx"), b); console.log("ok", all.length, "sections", sections.length); });
`;
vm.runInNewContext(src, { require, console, Buffer, __dirname, path, REFS, TWO }, { filename: "build_v2(concat)" });
