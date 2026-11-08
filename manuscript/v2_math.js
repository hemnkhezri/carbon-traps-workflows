// Equation helpers (Word native math). Requires docx symbols in scope.
const { Math: OMath, MathRun, MathFraction, MathSubScript, MathSuperScript, MathSubSuperScript, MathSum, MathIntegral,
        MathRoundBrackets, MathSquareBrackets } = require("docx");
const mr = (t) => new MathRun(t);
const frac = (n, d) => new MathFraction({ numerator: n, denominator: d });
const sub = (b, s) => new MathSubScript({ children: b, subScript: s });
const sup = (b, s) => new MathSuperScript({ children: b, superScript: s });
const integ = (lo, hi, body) => new MathIntegral({ children: body, subScript: lo, superScript: hi });
const msum = (lo, body) => new MathSum({ children: body, subScript: lo });
const rb = (body) => new MathRoundBrackets({ children: body });
const sb = (body) => new MathSquareBrackets({ children: body });
const MEQ = (parts, n) => new Paragraph({
  tabStops: (typeof TWO !== "undefined" && TWO) ? [{ type: TabStopType.CENTER, position: 2506 }, { type: TabStopType.RIGHT, position: 5013 }] : [{ type: TabStopType.CENTER, position: 4513 }, { type: TabStopType.RIGHT, position: 9026 }],
  spacing: { before: 120, after: 120, line: 240, lineRule: LineRuleType.AUTO },
  children: [new TextRun({ text: "\t" }), new OMath({ children: parts }), new TextRun({ text: `\t(${n})` })],
});
