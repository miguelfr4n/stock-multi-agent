import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from . import monitor

router = APIRouter()
_task = None


async def start_monitor():
    """Chamar no startup da aplicação: dispara a coleta periódica em background."""
    global _task
    if _task is None or _task.done():
        _task = asyncio.create_task(monitor.run_forever())


@router.get("/sefaz", include_in_schema=False)
async def sefaz_page():
    return FileResponse(Path(__file__).with_name("dashboard.html"))


@router.get("/sefaz/status")
async def sefaz_status(minutes: int = monitor.WINDOW_MINUTES):
    return {
        "window_minutes": minutes,
        "source": monitor.SEFAZ_URL,
        "poll_seconds": monitor.POLL_SECONDS,
        "collector": monitor.last_run,
        "data": monitor.current_status(minutes),
    }


@router.get("/sefaz/history/{autorizador}")
async def sefaz_history(autorizador: str, hours: int = 24):
    data = monitor.history(autorizador, hours)
    if not data:
        raise HTTPException(404, "Sem histórico para esse autorizador")
    return {"autorizador": autorizador, "data": data}


@router.post("/sefaz/check")
async def sefaz_check_now():
    """Força uma coleta imediata."""
    n = await monitor.check_once()
    return {"collected": n, "collector": monitor.last_run}
