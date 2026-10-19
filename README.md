# 📦 Stock Multi-Agent

Sistema de controle de estoque inteligente com múltiplos agentes de IA usando **LangGraph** e **DeepSeek**.

## Visão Geral

Cada operação é roteada automaticamente para o agente especializado correto, com base na linguagem natural do usuário.

```
Usuário → Supervisor → [ Inventário | Pedidos | Reposição | Relatórios | Stock Advisor ]
```

## Agentes

| Agente | Responsabilidade |
|--------|-----------------|
| 🧠 **Supervisor** | Analisa a mensagem e roteia para o agente correto |
| 🗃️ **Inventário** | Consulta e atualiza níveis de estoque |
| 🛒 **Pedidos** | Processa pedidos de venda e transferência |
| 📦 **Reposição** | Gerencia ordens de compra e recebimento |
| 📊 **Relatórios** | Gera resumos, históricos e alertas |
| 🤖 **Stock Advisor** | Analisa comportamento e recomenda ajustes de estoque |

## Stack

- **LangGraph** — Orquestração de agentes
- **DeepSeek** (`deepseek-chat`) — LLM
- **LangChain** — Tools e integração com LLM
- **FastAPI** — API REST
- **SQLAlchemy + SQLite** — Banco de dados
- **HTML/CSS/JS** — Interface de chat

## Estrutura do Projeto

```
inventory-agents/
├── main.py                  # Ponto de entrada
├── api.py                   # FastAPI
├── graph.py                 # Grafo LangGraph
├── state.py                 # Estado compartilhado
├── database.py              # Conexão com banco
├── models.py                # Modelos SQLAlchemy
├── seed_data.py             # Dados de teste
├── interface.html           # Interface de chat
├── tools/
│   └── db_tools.py          # 20 ferramentas de banco de dados
└── agents/
    ├── base.py              # Loop ReAct compartilhado
    ├── supervisor.py        # Roteamento
    ├── inventory.py
    ├── order.py
    ├── restock.py
    ├── report.py
    └── stock_advisor.py
```

## Instalação

```bash
# 1. Clonar o repositório
git clone https://github.com/miguel-franca/stock-multi-agent.git
cd stock-multi-agent

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente
cp .env.example .env
# Edite o .env e insira sua DEEPSEEK_API_KEY
```

## Configuração

Edite o arquivo `.env`:

```env
DEEPSEEK_API_KEY=sua_chave_aqui
DATABASE_URL=sqlite:///./inventory.db
```

Obtenha sua chave em: [platform.deepseek.com/api-keys](https://platform.deepseek.com/api-keys)

## Executando

```bash
python main.py
```

O servidor sobe na porta **8081**.

| URL | Descrição |
|-----|-----------|
| `http://localhost:8081/docs` | Documentação interativa (Swagger) |
| `http://localhost:8081/chat` | Endpoint principal (POST) |
| `interface.html` | Interface de chat (abrir no navegador) |

## Populando Dados de Teste

```bash
# Via API
curl -X POST http://localhost:8081/seed

# Ou direto pelo Python
python seed_data.py
```

Cria 8 produtos com histórico de 90 dias de movimentações.

## Exemplos de Uso

Via interface de chat ou `POST /chat`:

```json
{ "message": "Liste todos os produtos do estoque" }
{ "message": "Faça um pedido de 10 unidades de CAFE_GOURMET_500G para o cliente João" }
{ "message": "Quais produtos estão abaixo do estoque mínimo?" }
{ "message": "Analise o REFRIGERANTE_2L e recomende ajuste de estoque" }
{ "message": "Gere um relatório resumo do estoque" }
{ "message": "Crie uma ordem de compra de 50 unidades do DETERGENTE_500ML para o fornecedor Limpeza Total" }
```

## Stock Advisor — Como Funciona

O agente analisa os seguintes indicadores para recomendar `AUMENTAR`, `MANTER` ou `DIMINUIR` o estoque:

| Indicador | Descrição |
|-----------|-----------|
| **Velocidade de vendas** | Média diária/semanal/mensal dos últimos 90 dias |
| **Cobertura** | Quantos dias o estoque atual vai durar |
| **Tendência** | Crescente, estável ou decrescente |
| **Rupturas** | Quantas vezes o produto ficou sem estoque |

### Critérios de Decisão

- **AUMENTAR** → cobertura < 7 dias, rupturas recorrentes ou tendência crescente
- **MANTER** → cobertura entre 15–45 dias, demanda estável
- **DIMINUIR** → cobertura > 60 dias, produto parado, tendência decrescente

## Endpoints REST

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/chat` | Chat com agentes |
| `GET` | `/products` | Listar produtos |
| `GET` | `/products/{id}/stock` | Estoque de um produto |
| `GET` | `/dashboard` | Resumo geral |
| `GET` | `/orders` | Listar pedidos |
| `GET` | `/recommendations` | Recomendações do advisor |
| `POST` | `/seed` | Popular banco com dados de teste |

## Monitor SEFAZ

Painel que acompanha a disponibilidade dos autorizadores da NF-e (SVRS, SVAN, SP, MG...) lendo a página pública
da Fazenda (`nfe.fazenda.gov.br/portal/disponibilidade.aspx`) a cada 60s e guardando o histórico no banco.

| Estado | Regra (janela de 15 min) |
|--------|--------------------------|
| 🟢 Disponível | todas as coletas ok |
| 🟡 Intermitente | oscilou, ficou lento/instável ou acabou de cair |
| 🔴 Indisponível | últimas 3 coletas fora do ar |

- Dashboard: `http://localhost:8081/sefaz`
- API: `GET /sefaz/status`, `GET /sefaz/history/{autorizador}`, `POST /sefaz/check`
- Variáveis opcionais: `SEFAZ_POLL_SECONDS`, `SEFAZ_WINDOW_MINUTES`, `SEFAZ_RETENTION_DAYS`, `SEFAZ_STATUS_URL`
- Testes: `pytest tests`

## Licença

MIT
