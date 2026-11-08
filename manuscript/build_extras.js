const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, AlignmentType, LevelFormat } = require("docx");
const F = "Times New Roman";
const p = (t, o = {}) => new Paragraph({ spacing: { after: 160, line: 300 }, alignment: AlignmentType.JUSTIFIED, ...o, children: [new TextRun({ text: t, font: F, size: 24, ...(o.run || {}) })] });
const num = { config: [{ reference: "b", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360, hanging: 240 } } } }] }] };
const H = ["Workflow schedulers are replayed against carbon forecasts that were actually issued.",
  "Issued forecasts keep about two-thirds of the oracle carbon saving.",
  "About one plan in seven emits more than a carbon-agnostic schedule.",
  "A gate on forecast-difference errors cuts these carbon traps on every grid.",
  "Carbon-aware plans miss far more deadlines unless slack is reserved."];
H.forEach(h => { if (h.length > 85) throw new Error("highlight too long: " + h); });
const hl = new Document({ numbering: num, sections: [{ children: [p("Highlights", { run: { bold: true } }),
  ...H.map(h => new Paragraph({ numbering: { reference: "b", level: 0 }, children: [new TextRun({ text: h, font: F, size: 24 })] }))] }] });
const title = "Mitigating Carbon Traps in Carbon-Aware Workflow Scheduling under Real Carbon-Intensity Forecasts";
const cl = new Document({ sections: [{ children: [
  p("9 November 2026"), p("To the Editor-in-Chief, Future Generation Computer Systems"),
  p("Dear Editor,"),
  p(`We are pleased to submit our manuscript "${title}" for consideration as a Full Length Article in Future Generation Computer Systems.`),
  p("Carbon-aware workflow schedulers move tasks into periods of cleaner electricity, but they have so far been evaluated with perfect knowledge of future carbon intensity. We replay deadline-constrained scientific workflows against the carbon-intensity forecasts that the Great Britain grid operator actually issued, and against model forecasts for four further grids, using our own schedulers and the official code of two recent workflow schedulers (CaWoSched and CWM). We show that forecasts keep only about two-thirds of the oracle saving, that about one plan in seven becomes a carbon trap that emits more than a carbon-agnostic schedule, and that carbon-aware plans miss far more deadlines when runtimes vary. We propose two lightweight remedies, a gate calibrated on errors of forecast differences, with a per-decision error bound, and a slack reserve, and show that the gate reduces traps on every grid and the reserve removes most deadline misses under moderate runtime noise, each at a modest cost in saving."),
  p("The work fits the journal's scope on complex workflow applications and on distributed resource management and scheduling, and it builds on and complements work recently published in FGCS on carbon-aware execution of scientific workflows and on WfCommons. All studies were planned and sealed before their data were used, and code, plans and raw results are openly available (https://github.com/hemnkhezri/carbon-traps-workflows; https://doi.org/10.5281/zenodo.24055544)."),
  p("In line with the journal's requirements for Full Length Articles, the manuscript is formatted in double column and single spacing and runs to 16 pages including figures, tables and references; a single-column version of the Word source is available on request. The manuscript has not been published and is not under consideration elsewhere. Both authors have approved the submission and declare no competing interests. The use of AI-assisted tools is declared in the manuscript."),
  p("Sincerely,"), p("Hemn Khezri (corresponding author), on behalf of both authors"),
  p("Young Researchers and Elite Club, Sardasht Branch, Islamic Azad University, Central Building, Shohada-ye 7 Tir Boulevard, Sardasht, West Azerbaijan Province, 5961933113, Iran — hemnkhezri21@gmail.com"),
] }] });
Packer.toBuffer(hl).then(b => fs.writeFileSync("FGCS_submission/Highlights.docx", b));
Packer.toBuffer(cl).then(b => fs.writeFileSync("FGCS_submission/Cover_letter_DRAFT.docx", b));
