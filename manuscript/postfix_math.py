"""Post-process the built .docx: turn math runs 'F̄' / 'Ā' (base letter + macron) into proper OMML bar accents,
so Word renders the overbar in equations. Usage: python3 postfix_math.py file.docx [...]"""
import re, sys, zipfile, shutil, os
ACC = '<m:acc><m:accPr><m:chr m:val="̄"/></m:accPr><m:e><m:r><m:t>{}</m:t></m:r></m:e></m:acc>'
for f in sys.argv[1:]:
    tmp = f + ".tmp"
    with zipfile.ZipFile(f) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for it in [i for i in zin.infolist() if not i.filename.endswith("/")]:
            data = zin.read(it.filename)
            if it.filename == "word/document.xml":
                x = data.decode("utf8")
                x, n1 = re.subn(r"<m:r><m:t(?: [^>]*)?>([A-Za-z])̄</m:t></m:r>", lambda m: ACC.format(m.group(1)), x)
                x, n2 = re.subn(r"<m:r><m:t(?: [^>]*)?>Ā</m:t></m:r>", ACC.format("A"), x)
                print(f, "accents:", n1 + n2)
                data = x.encode("utf8")
            zout.writestr(it, data)
    shutil.move(tmp, f)
