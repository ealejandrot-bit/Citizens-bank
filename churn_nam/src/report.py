"""Renderiza reports/pNN.md a partir de outputs/pNN/*.json | *.csv | *.png (ningún número se escribe a mano).

- Primera línea fija: config.project.report_header.
- Opcional: outputs/pNN/_meta.json con {"title": str, "order": [archivos], "notes": {archivo: texto}} para título,
  orden y una nota por archivo (sin cifras a mano).
- CSV → tabla markdown; JSON → tabla clave / valor (o lista de registros); PNG → imagen enlazada.

Uso: python src/report.py NN
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from config import HEADER, P, ROOT


def md_table(df: pd.DataFrame, digits: int = 4) -> str:
    """Tabla markdown sin dependencias externas (pandas.to_markdown requiere tabulate, fuera de requirements.txt)."""
    def cell(v):
        if isinstance(v, float):
            return "" if pd.isna(v) else f"{v:,.{digits}g}"
        return str(v).replace("|", "\\|").replace("\n", " ")
    head = "| " + " | ".join(str(c) for c in df.columns) + " |"
    sep = "|" + "|".join(":--" for _ in df.columns) + "|"
    body = ["| " + " | ".join(cell(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([head, sep] + body)


def _fmt_json(obj) -> str:
    if isinstance(obj, list) and obj and all(isinstance(x, dict) for x in obj):
        return md_table(pd.DataFrame(obj))
    if isinstance(obj, dict):
        rows = [{"clave": k, "valor": json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v} for k, v in obj.items()]
        return md_table(pd.DataFrame(rows))
    return f"```\n{json.dumps(obj, ensure_ascii=False, indent=2)}\n```"


def render(fase: int) -> Path:
    out = P.out(fase)
    meta_p = out / "_meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
    files = [f for f in sorted(out.iterdir()) if f.suffix in (".json", ".csv", ".png") and f.name != "_meta.json"]
    order = meta.get("order", [])
    files = [out / o for o in order if (out / o).exists()] + [f for f in files if f.name not in order]
    lines = [HEADER, "", f"# p{fase:02d} · {meta.get('title', f'fase {fase}')}", ""]
    for f in files:
        lines += [f"## {f.stem}", ""]
        if f.name in meta.get("notes", {}):
            lines += [meta["notes"][f.name], ""]
        if f.suffix == ".csv":
            lines.append(md_table(pd.read_csv(f)))
        elif f.suffix == ".json":
            lines.append(_fmt_json(json.loads(f.read_text(encoding="utf-8"))))
        else:
            lines.append(f"![{f.stem}](../{f.relative_to(ROOT).as_posix()})")
        lines += ["", f"_Fuente: `{f.relative_to(ROOT).as_posix()}`_", ""]
    rp = P.reports / f"p{fase:02d}.md"
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text("\n".join(lines), encoding="utf-8")
    return rp


if __name__ == "__main__":
    print(render(int(sys.argv[1])))
