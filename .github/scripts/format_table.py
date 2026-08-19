from pathlib import Path
import re


LISTING_FILES = (
    (Path("README.md"), "INTERNSHIPS_TABLE"),
    (Path("README-2026.md"), "INTERNSHIPS_2026_TABLE"),
)

def split_markdown_row(line: str) -> list[str] | None:
    """Split a Markdown table row without treating escaped pipes as separators."""
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None

    cells: list[str] = []
    cell: list[str] = []
    escaped = False
    for character in stripped[1:]:
        if character == "|" and not escaped:
            cells.append("".join(cell))
            cell = []
        else:
            cell.append(character)
        escaped = character == "\\" and not escaped

    if cell:
        cells.append("".join(cell))
    while cells and not cells[-1].strip():
        cells.pop()
    return cells


def normalize_table(block: str) -> str:
    lines = block.splitlines()
    out = []

    for line in lines:
        cells = split_markdown_row(line)
        if cells is None:
            out.append(line.rstrip())
            continue

        out.append("| " + " | ".join(cell.strip() for cell in cells) + " |")

    return "\n".join(out)

def main() -> None:
    for path, table_name in LISTING_FILES:
        text = path.read_text(encoding="utf-8")
        pattern = re.compile(
            rf"(<!-- BEGIN:{re.escape(table_name)} -->)([\s\S]*?)(<!-- END:{re.escape(table_name)} -->)"
        )

        def replacer(match: re.Match[str]) -> str:
            start, table, end = match.groups()
            return f"{start}\n{normalize_table(table.strip())}\n{end}"

        formatted, replacements = pattern.subn(replacer, text)
        if replacements != 1:
            raise RuntimeError(f"Expected one {table_name} table in {path}, found {replacements}")
        path.write_text(formatted.rstrip() + "\n", encoding="utf-8")

    print("Internship tables normalized.")


if __name__ == "__main__":
    main()
