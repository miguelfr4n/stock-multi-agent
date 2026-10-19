"""Parser da página pública de disponibilidade da NF-e (Portal Nacional).

Fonte: https://www.nfe.fazenda.gov.br/portal/disponibilidade.aspx
Cada linha da tabela é um autorizador (SVRS, SVAN, SP, MG...) e cada coluna
um serviço (Autorização, Status Serviço...), com uma bolinha verde/amarela/vermelha.
"""
from html.parser import HTMLParser

UP, DEGRADED, DOWN = "up", "degraded", "down"


def _icon_status(src: str):
    src = src.lower()
    if "verde" in src:
        return UP
    if "amarela" in src:
        return DEGRADED
    if "vermelha" in src:
        return DOWN
    return None


class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []  # cada linha: lista de células, cada célula = {"text", "status"}
        self._row = None
        self._cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = {"text": "", "status": None, "header": tag == "th"}
        elif tag == "img" and self._cell is not None:
            a = dict(attrs)
            status = _icon_status(a.get("src") or "")
            if status:
                self._cell["status"] = status

    def handle_data(self, data):
        if self._cell is not None:
            self._cell["text"] += data

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._cell["text"] = " ".join(self._cell["text"].split())
            self._row.append(self._cell)
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None


def parse_availability(html: str):
    """Retorna lista de dicts {autorizador, service, status} (status: up|degraded|down)."""
    parser = _TableParser()
    parser.feed(html)

    header = None
    results = []
    for row in parser.rows:
        # a tabela de disponibilidade tem o cabeçalho começando por "Autorizador"
        if header is None:
            if row and row[0]["text"].lower().startswith("autorizador"):
                header = [c["text"] for c in row]
            continue
        if not any(c["status"] for c in row[1:]):
            continue
        name = row[0]["text"]
        if not name:
            continue
        for i, cell in enumerate(row[1:], start=1):
            if cell["status"] and i < len(header):
                results.append({
                    "autorizador": name,
                    "service": header[i].rstrip("0123456789 "),  # tira o sobrescrito "4"
                    "status": cell["status"],
                })
    return results
