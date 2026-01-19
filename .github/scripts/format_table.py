from pathlib import Path
import re

README = Path("README.md")

text = README.read_text(encoding="utf-8")

def normalize_table(block: str) -> str:
    lines = block.splitlines()
    out = []

    for line in lines:
        if "|" not in line:
            out.append(line.rstrip())
            continue

        cells = [c.strip() for c in line.split("|")[1:-1]]
        out.append("| " + " | ".join(cells) + " |")

    return "\n".join(out)

pattern = re.compile(
    r"(<!-- BEGIN:INTERNSHIPS_TABLE -->)([\s\S]*?)(<!-- END:INTERNSHIPS_TABLE -->)"
)

def replacer(match):
    start, table, end = match.groups()
    return f"{start}\n{normalize_table(table.strip())}\n{end}"

formatted = pattern.sub(replacer, text)

README.write_text(formatted + "\n", encoding="utf-8")

print("Internship table normalized.")
