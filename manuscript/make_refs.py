"""Format the cited BibTeX entries in Elsevier numbered style (elsarticle-num), in order of first citation.
Usage: python3 make_refs.py refs.bib cite_order.json refs.json"""
import json
import re
import sys

import bibtexparser

lib = bibtexparser.parse_string(open(sys.argv[1], encoding="utf8").read())
E = {e.key: {f.key.lower(): f.value for f in e.fields} | {"_type": e.entry_type.lower()} for e in lib.entries}
order = json.load(open(sys.argv[2]))
# keys renamed in the updated Zotero export (same works)
ALIAS = {"schweisgut_carbon-aware_2026": "torquati_carbon-aware_2027", "angelopoulos_conformal_2024": "angelopoulos_conformal_2024-1"}
order = [ALIAS.get(k, k) if ALIAS.get(k) in E else k for k in order]


def clean(s):
    s = re.sub(r"\\&", "&", s)
    s = re.sub(r"[{}]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def initials(given):
    out = []
    for part in given.split():
        sub = [p for p in part.split("-") if p]
        out.append("-".join(p[0] + "." for p in sub))
    return " ".join(out).replace(". ", ".")


def author(a):
    a = a.strip()
    if a.startswith("{") and a.endswith("}"):
        return clean(a)
    if "," in a:
        last, given = [x.strip() for x in a.split(",", 1)]
    else:
        parts = a.split(); last, given = parts[-1], " ".join(parts[:-1])
    return (initials(clean(given)) + " " + clean(last)).strip()


def authors(e, field="author"):
    if field not in e:
        return ""
    A = [author(a) for a in re.split(r"\s+and\s+", e[field])]
    return ", ".join(A)


def pages(p):
    return clean(p).replace("--", "–")


def fmt(e):
    t, au, ti, y = e["_type"], authors(e), clean(e.get("title", "")), e.get("year", "")
    doi = f" https://doi.org/{e['doi']}." if "doi" in e else (f" {e['url']}." if "url" in e else "")
    lead = f"{au}, " if au else ""
    if t == "article":
        vol = clean(e.get("volume", "")); num = clean(e.get("number", ""))
        s = f"{lead}{ti}, {clean(e['journal'])} {vol}{f' ({num})' if num else ''} ({y})"
        if "pages" in e:
            s += f" {pages(e['pages'])}"
        return s + "." + doi
    if t in ("inproceedings", "incollection"):
        ed = authors(e, "editor")
        s = f"{lead}{ti}, in: {ed + (' (Ed.), ' if ' and ' not in e['editor'] else ' (Eds.), ') if ed else ''}{clean(e['booktitle'])}"
        if "series" in e and "volume" in e:
            s += f", {clean(e['series'])}, vol. {clean(e['volume'])}"
        elif "volume" in e and clean(e["volume"]) != y:
            s += f", vol. {clean(e['volume'])}"
        if "address" in e and "publisher" in e and t == "incollection":
            s += f", {clean(e['publisher'])}, {clean(e['address'])}"; e = dict(e); e.pop("publisher")
        if "publisher" in e:
            s += f", {clean(e['publisher'])}"
        s += f", {y}"
        if "pages" in e:
            s += f", pp. {pages(e['pages'])}"
        return s + "." + doi
    if t == "techreport":
        inst = clean(e.get("institution", "")); addr = clean(e.get("address", ""))
        if not au:
            return f"{inst}, {ti}, Technical report{', ' + addr if addr else ''}, {y}." + doi
        return f"{lead}{ti}, Technical report, {inst}{', ' + addr if addr else ''}, {y}." + doi
    # misc
    note = clean(e.get("annote", ""))
    m = re.search(r"arXiv:\s*(\S+)", note)
    if m:
        aid = re.sub(r'v\d+$', '', m.group(1)); return f"{lead}{ti}, arXiv preprint arXiv:{aid}, {y}. https://arxiv.org/abs/{aid}."
    if "Official Journal" in note:
        return f"{lead}{ti}, Official Journal of the European Union, {y}." + doi
    return f"{lead}{ti}, {y}." + doi


missing = [k for k in order if k not in E]
if missing:
    sys.exit(f"missing keys: {missing}")
json.dump([fmt(E[k]) for k in order], open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
print(len(order), "references")
