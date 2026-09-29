"""p00 · Entorno: escribe outputs/env.json con las versiones de Python y de los paquetes instalados en .venv."""
from __future__ import annotations

import json
import platform
import sys
from importlib.metadata import distributions

from config import ROOT

pk = sorted(((d.metadata["Name"], d.version) for d in distributions()), key=lambda t: t[0].lower())
env = {"python": platform.python_version(), "executable": sys.executable, "platform": platform.platform(), "packages": dict(pk)}
out = ROOT / "outputs" / "env.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(env, indent=2, ensure_ascii=False), encoding="utf-8")
print(out, env["python"], len(pk), "paquetes")
