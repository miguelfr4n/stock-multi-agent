import os
import sys

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timedelta

from sefaz.classify import classify, DISPONIVEL, INTERMITENTE, INDISPONIVEL, SEM_DADOS
from sefaz.parser import parse_availability

HTML = """
<table>
 <tr><th>Autorizador</th><th>Autorização<sup>4</sup></th><th>Status Serviço<sup>4</sup></th></tr>
 <tr><td>SP</td><td><img src="imagens/bola_verde_P.png"></td><td><img src="imagens/bola_verde_P.png"></td></tr>
 <tr><td>MG</td><td><img src="imagens/bola_amarela_P.png"></td><td><img src="imagens/bola_verde_P.png"></td></tr>
 <tr><td>SVRS</td><td><img src="imagens/bola_vermelha_P.png"></td><td><img src="imagens/bola_vermelha_P.png"></td></tr>
</table>
"""


def test_parse():
    rows = parse_availability(HTML)
    assert len(rows) == 6
    assert {"autorizador": "MG", "service": "Autorização", "status": "degraded"} in rows
    assert {"autorizador": "SVRS", "service": "Status Serviço", "status": "down"} in rows


def test_classify():
    assert classify([]) == SEM_DADOS
    assert classify(["up"] * 5) == DISPONIVEL
    assert classify(["up", "down", "up", "up"]) == INTERMITENTE
    assert classify(["up", "degraded", "up"]) == INTERMITENTE
    assert classify(["up", "up", "down"]) == INTERMITENTE  # acabou de cair
    assert classify(["up", "down", "down", "down"]) == INDISPONIVEL
    assert classify(["down"]) == INDISPONIVEL


def test_end_to_end():
    from database import init_db
    from sefaz import monitor

    init_db()
    now = datetime.utcnow()
    for i, st in enumerate(["up", "down", "up"]):
        rows = [{"autorizador": "SP", "service": "Autorização", "status": st}]
        monitor.store(rows, now=now - timedelta(minutes=3 - i))
    monitor.store([{"autorizador": "MG", "service": "Autorização", "status": "up"}], now=now)

    by_aut = {a["autorizador"]: a for a in monitor.current_status()}
    assert by_aut["SP"]["state"] == INTERMITENTE
    assert by_aut["MG"]["state"] == DISPONIVEL
    assert len(monitor.history("SP")) == 3
