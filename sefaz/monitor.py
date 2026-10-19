"""Coleta periódica da disponibilidade da SEFAZ e consulta do estado atual/histórico."""
import asyncio
import os
from collections import defaultdict
from datetime import datetime, timedelta

import httpx

from database import get_session
from .classify import classify, worst, SEM_DADOS
from .models import SefazCheck
from .parser import parse_availability

SEFAZ_URL = os.getenv(
    "SEFAZ_STATUS_URL", "https://www.nfe.fazenda.gov.br/portal/disponibilidade.aspx"
)
POLL_SECONDS = int(os.getenv("SEFAZ_POLL_SECONDS", "60"))
WINDOW_MINUTES = int(os.getenv("SEFAZ_WINDOW_MINUTES", "15"))
RETENTION_DAYS = int(os.getenv("SEFAZ_RETENTION_DAYS", "7"))

# estado da última coleta (para a UI mostrar se a própria fonte caiu)
last_run = {"at": None, "ok": None, "error": None}


async def fetch_html() -> str:
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        r = await client.get(SEFAZ_URL, headers={"User-Agent": "Mozilla/5.0 sefaz-monitor"})
        r.raise_for_status()
        return r.text


def store(rows, now=None):
    now = now or datetime.utcnow()
    db = get_session()
    try:
        db.add_all(SefazCheck(checked_at=now, **r) for r in rows)
        db.query(SefazCheck).filter(
            SefazCheck.checked_at < now - timedelta(days=RETENTION_DAYS)
        ).delete()
        db.commit()
    finally:
        db.close()


async def check_once():
    """Faz uma coleta. Se a página da Fazenda não responder/mudar de formato, não grava nada."""
    try:
        rows = parse_availability(await fetch_html())
        if not rows:
            raise ValueError("Nenhum autorizador encontrado na página (layout mudou?)")
        store(rows)
        last_run.update(at=datetime.utcnow(), ok=True, error=None)
        return len(rows)
    except Exception as e:  # a fonte pode falhar; o loop não pode morrer
        last_run.update(at=datetime.utcnow(), ok=False, error=f"{type(e).__name__}: {e}")
        return 0


async def run_forever():
    while True:
        await check_once()
        await asyncio.sleep(POLL_SECONDS)


def _timeline(since):
    """{autorizador: {checked_at: {service: status}}} desde `since`."""
    db = get_session()
    try:
        q = (
            db.query(SefazCheck)
            .filter(SefazCheck.checked_at >= since)
            .order_by(SefazCheck.checked_at)
        )
        data = defaultdict(lambda: defaultdict(dict))
        for c in q:
            data[c.autorizador][c.checked_at][c.service] = c.status
        return data
    finally:
        db.close()


def _aggregate(services):
    status = None
    for s in services.values():
        status = s if status is None else worst(status, s)
    return status


def current_status(window_minutes=WINDOW_MINUTES):
    since = datetime.utcnow() - timedelta(minutes=window_minutes)
    result = []
    for aut, by_time in sorted(_timeline(since).items()):
        times = sorted(by_time)
        samples = [_aggregate(by_time[t]) for t in times]
        latest = by_time[times[-1]]
        down = sum(s == "down" for s in samples)
        result.append({
            "autorizador": aut,
            "state": classify(samples),
            "samples": len(samples),
            "failures": sum(s != "up" for s in samples),
            "availability_pct": round(100 * (len(samples) - down) / len(samples), 1),
            "last_check": times[-1].isoformat() + "Z",
            "services": latest,
        })
    return result


def history(autorizador, hours=24):
    since = datetime.utcnow() - timedelta(hours=hours)
    by_time = _timeline(since).get(autorizador, {})
    return [
        {"at": t.isoformat() + "Z", "status": _aggregate(by_time[t]), "services": by_time[t]}
        for t in sorted(by_time)
    ]
