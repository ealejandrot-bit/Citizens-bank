"""Checklist de conexión a IBKR (solo lectura). Imprime OK / FALLA por punto.

Se conecta con readonly=True a IB Gateway (cuenta real en modo Read-Only, puerto 4001).
Este script no importa ni llama ninguna función que envíe, modifique o cancele órdenes
(lo verifica tests/test_safety.py). El punto 7 solo LEE posiciones y órdenes abiertas.

Si los 9 puntos pasan, escribe logs/check_connection_ok.json, que habilita la descarga de datos
reales y el backtest con ellos (SPEC, regla 3). Si alguno falla, borra ese archivo.

Uso:  python check_connection.py
"""
from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from ib_async import IB, Stock

from src.config import CHECK_OK_PATH, ROOT

SYMBOL = "GLD"
MAX_CLOCK_DIFF_S = 2.0
results: list[tuple[int, str, bool, str]] = []


def mask(account: str) -> str:
    """No imprimir el número de cuenta completo."""
    return account[:1] + "***" + account[-3:] if len(account) > 4 else "***"


def report(n: int, name: str, ok: bool, detail: str = "") -> bool:
    results.append((n, name, ok, detail))
    print(f"{n}. [{'OK' if ok else 'FALLA'}] {name}" + (f" — {detail}" if detail else ""), flush=True)
    return ok


def _num(x) -> bool:
    return x is not None and not (isinstance(x, float) and math.isnan(x)) and x > 0


def main() -> int:
    load_dotenv(ROOT / ".env")
    host = os.getenv("IB_HOST", "127.0.0.1")
    port = int(os.getenv("IB_PORT", "4001"))
    client_id = int(os.getenv("IB_CLIENT_ID", "1"))
    account = os.getenv("IB_ACCOUNT", "").strip()
    CHECK_OK_PATH.unlink(missing_ok=True)

    ib = IB()
    info = {"tipo_cuenta": None, "marketDataType": None}

    # 1. Conexión
    try:
        ib.connect(host, port, clientId=client_id, readonly=True, timeout=15)
        report(1, f"Conexión a {host}:{port}", ib.isConnected(), f"clientId={client_id}, readonly=True")
    except Exception as e:  # noqa: BLE001
        report(1, f"Conexión a {host}:{port}", False, f"{type(e).__name__}: {e}")
        for n, name in enumerate(
            ["Cuentas", "Hora servidor", "Contrato GLD", "Snapshot GLD", "Account summary",
             "Posiciones y órdenes abiertas", "Barras históricas", "Desconexión"], start=2):
            report(n, name, False, "sin conexión")
        return finish(info)

    # 2. Cuentas
    try:
        accounts = ib.managedAccounts()
        found = bool(account) and account in accounts
        if found:
            paper = account.upper().startswith("D")
            info["tipo_cuenta"] = "paper" if paper else "real"
            detail = f"{len(accounts)} cuenta(s); IB_ACCOUNT={mask(account)} es {info['tipo_cuenta'].upper()}"
        else:
            detail = f"IB_ACCOUNT {'vacío' if not account else mask(account)} no está en {[mask(a) for a in accounts]}"
        report(2, "IB_ACCOUNT entre las cuentas del login", found, detail)
        if found and not paper:
            print("   MODO SOLO LECTURA – cuenta real")
    except Exception as e:  # noqa: BLE001
        report(2, "IB_ACCOUNT entre las cuentas del login", False, str(e))

    # 3. Hora servidor vs. local
    try:
        server = ib.reqCurrentTime()
        local = datetime.now(timezone.utc)
        diff = abs((server - local).total_seconds())
        report(3, "Diferencia hora servidor vs. local < 2 s", diff < MAX_CLOCK_DIFF_S, f"{diff:.2f} s")
    except Exception as e:  # noqa: BLE001
        report(3, "Diferencia hora servidor vs. local < 2 s", False, str(e))

    # 4. Contrato GLD
    contract = None
    try:
        q = ib.qualifyContracts(Stock(SYMBOL, "SMART", "USD", primaryExchange="ARCA"))
        contract = q[0] if q and q[0] is not None and q[0].conId else None
        ok = (
            contract is not None and contract.secType == "STK" and contract.exchange == "SMART"
            and contract.currency == "USD" and contract.primaryExchange == "ARCA"
        )
        report(4, "GLD resuelto (STK, SMART, USD, ARCA)", ok,
               f"conId={contract.conId}" if contract is not None else "no resuelto")
    except Exception as e:  # noqa: BLE001
        report(4, "GLD resuelto (STK, SMART, USD, ARCA)", False, str(e))

    # 5. Snapshot (si no hay suscripción en tiempo real → datos con retraso)
    try:
        if contract is None:
            raise RuntimeError("sin contrato")
        tk = ib.reqTickers(contract)[0]
        if not any(_num(v) for v in (tk.bid, tk.ask, tk.last, tk.close)):
            ib.reqMarketDataType(3)
            ib.sleep(1)
            tk = ib.reqTickers(contract)[0]
        mdt = tk.marketDataType
        info["marketDataType"] = mdt
        names = {1: "tiempo real", 2: "congelado", 3: "con retraso", 4: "con retraso congelado"}
        ok = any(_num(v) for v in (tk.bid, tk.ask, tk.last, tk.close))
        report(5, "Snapshot GLD", ok,
               f"bid={tk.bid} ask={tk.ask} last={tk.last} close={tk.close} "
               f"marketDataType={mdt} ({names.get(mdt, '?')})")
    except Exception as e:  # noqa: BLE001
        report(5, "Snapshot GLD", False, str(e))

    # 6. Account summary
    try:
        summ = ib.accountSummary(account) if account else []
        nl = [v for v in summ if v.tag == "NetLiquidation"]
        report(6, "Account summary: NetLiquidation", bool(nl),
               f"{nl[0].value} {nl[0].currency}" if nl else "sin NetLiquidation")
    except Exception as e:  # noqa: BLE001
        report(6, "Account summary: NetLiquidation", False, str(e))

    # 7. Posiciones y órdenes abiertas (solo lectura; deben estar vacías)
    try:
        positions = ib.positions(account) if account else ib.positions()
        open_orders = ib.reqAllOpenOrders()  # consulta de lectura; no crea ni modifica órdenes
        ok = not positions and not open_orders
        report(7, "Posiciones y órdenes abiertas vacías", ok,
               f"posiciones={len(positions)}, órdenes abiertas={len(open_orders)}")
    except Exception as e:  # noqa: BLE001
        report(7, "Posiciones y órdenes abiertas vacías", False, str(e))

    # 8. Barras históricas
    try:
        if contract is None:
            raise RuntimeError("sin contrato")
        d = ib.reqHistoricalData(contract, "", "10 D", "1 day", "TRADES", useRTH=True, formatDate=1)[-5:]
        m = ib.reqHistoricalData(contract, "", "1 D", "5 mins", "TRADES", useRTH=True, formatDate=1)[-5:]
        ok = len(d) == 5 and len(m) == 5
        report(8, "5 barras diarias y 5 de 5 min", ok, f"diarias={len(d)}, 5min={len(m)}")
        for b in d:
            print(f"   1d  {b.date}  o={b.open} h={b.high} l={b.low} c={b.close} v={b.volume}")
        for b in m:
            print(f"   5m  {b.date}  o={b.open} h={b.high} l={b.low} c={b.close} v={b.volume}")
    except Exception as e:  # noqa: BLE001
        report(8, "5 barras diarias y 5 de 5 min", False, str(e))

    # 9. Desconexión
    try:
        ib.disconnect()
        report(9, "Desconexión limpia", not ib.isConnected())
    except Exception as e:  # noqa: BLE001
        report(9, "Desconexión limpia", False, str(e))

    return finish(info)


def finish(info: dict) -> int:
    ok = len(results) == 9 and all(r[2] for r in results)
    print(f"\nResultado: {sum(r[2] for r in results)}/9 OK — " + ("PASA" if ok else "NO PASA"))
    if ok:
        CHECK_OK_PATH.parent.mkdir(parents=True, exist_ok=True)
        CHECK_OK_PATH.write_text(json.dumps(
            {"fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), **info}, indent=2))
        print(f"Habilitado: descarga de datos y backtest con datos reales ({CHECK_OK_PATH.name}).")
    else:
        print("Bloqueado: no se descargan datos reales ni se corre backtest con ellos.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
