"""Regla 2: ningún archivo del proyecto envía, modifica ni cancela órdenes."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROHIBIDO = re.compile(
    r"placeOrder|cancelOrder|reqGlobalCancel|bracketOrder|oneCancelsAll|whatIfOrder|"
    r"\b(MarketOrder|LimitOrder|StopOrder|StopLimitOrder|Order)\b"
)


def test_sin_funciones_de_ordenes():
    files = [ROOT / "check_connection.py", *ROOT.joinpath("src").rglob("*.py")]
    for f in files:
        assert not PROHIBIDO.search(f.read_text(encoding="utf-8")), f"Función de órdenes en {f.name}"


def test_conexiones_readonly():
    for f in [ROOT / "check_connection.py", ROOT / "src" / "data" / "ibkr_source.py"]:
        src = f.read_text(encoding="utf-8")
        assert "readonly=True" in src


def test_env_ignorado():
    gi = (ROOT / ".gitignore").read_text()
    assert ".env" in gi.split() and "data/" in gi.split()
