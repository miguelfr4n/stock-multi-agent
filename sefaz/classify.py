"""Classificação do estado de um autorizador a partir do histórico recente."""
from .parser import UP, DEGRADED, DOWN

DISPONIVEL = "DISPONIVEL"
INTERMITENTE = "INTERMITENTE"
INDISPONIVEL = "INDISPONIVEL"
SEM_DADOS = "SEM_DADOS"

# nº de últimas amostras consecutivas "down" para considerar fora do ar de vez
DOWN_STREAK = 3


def classify(samples):
    """samples: estados ('up'|'degraded'|'down') do mais antigo para o mais recente.

    - DISPONIVEL:   todas as amostras da janela estão ok
    - INDISPONIVEL: as últimas DOWN_STREAK amostras estão fora (ou todas, se houver menos)
    - INTERMITENTE: qualquer outra mistura (oscilou, ficou lento/instável ou acabou de cair)
    """
    if not samples:
        return SEM_DADOS
    if all(s == UP for s in samples):
        return DISPONIVEL
    tail = samples[-DOWN_STREAK:]
    if all(s == DOWN for s in tail):
        return INDISPONIVEL
    return INTERMITENTE


def worst(a, b):
    """Pior de dois estados de amostra (para agregar serviços de um autorizador)."""
    order = {UP: 0, DEGRADED: 1, DOWN: 2}
    return a if order[a] >= order[b] else b
