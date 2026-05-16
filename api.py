import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from langchain_core.messages import HumanMessage

from database import get_db, init_db
from graph import inventory_graph
from tools.db_tools import (
    list_products,
    get_product,
    check_stock,
    get_stock_summary,
    get_products_below_minimum,
    list_orders,
    list_stock_recommendations,
)

app = FastAPI(
    title="Sistema de Controle de Estoque Multi-Agente",
    description="API com agentes LangGraph para gestão inteligente de estoque",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    init_db()


# ─── SCHEMAS ─────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    response: str
    agent_used: Optional[str] = None


# ─── ENDPOINT PRINCIPAL: CHAT ─────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint principal. Envia uma mensagem em linguagem natural e o sistema
    roteia automaticamente para o agente correto (inventário, pedidos,
    reposição, relatório ou advisor de estoque).
    """
    try:
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "next": "",
            "iterations": 0,
            "agents_used": [],
        }

        result = inventory_graph.invoke(initial_state)

        messages = result.get("messages", [])
        ai_messages = [
            m for m in messages
            if hasattr(m, "type") and m.type == "ai" and not getattr(m, "tool_calls", None)
        ]

        response_text = ai_messages[-1].content if ai_messages else "Não consegui processar sua solicitação."
        agents_used = result.get("agents_used", [])

        return ChatResponse(
            response=response_text,
            agent_used=" → ".join(agents_used) if agents_used else None,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── ENDPOINTS REST ───────────────────────────────────────────────────────────

@app.get("/products")
async def get_products():
    """Lista todos os produtos com seu estoque atual."""
    result = list_products.invoke({})
    return {"data": result}


@app.get("/products/{product_id}")
async def get_product_detail(product_id: str):
    """Retorna detalhes de um produto específico."""
    result = get_product.invoke({"product_id": product_id})
    return {"data": result}


@app.get("/products/{product_id}/stock")
async def get_product_stock(product_id: str):
    """Verifica o estoque de um produto."""
    result = check_stock.invoke({"product_id": product_id})
    return {"data": result}


@app.get("/dashboard")
async def dashboard():
    """Retorna resumo geral do estoque para o dashboard."""
    summary = get_stock_summary.invoke({})
    alerts = get_products_below_minimum.invoke({})
    recommendations = list_stock_recommendations.invoke({})
    return {
        "summary": summary,
        "alerts": alerts,
        "recommendations": recommendations,
    }


@app.get("/orders")
async def get_orders(status: Optional[str] = None):
    """Lista pedidos, com filtro opcional por status."""
    result = list_orders.invoke({"status": status})
    return {"data": result}


@app.get("/recommendations")
async def get_recommendations(product_id: Optional[str] = None):
    """Lista recomendações geradas pelo Stock Advisor."""
    result = list_stock_recommendations.invoke({"product_id": product_id})
    return {"data": result}


@app.post("/seed")
async def seed_database():
    """Popula o banco com dados de exemplo para testes."""
    from seed_data import seed
    try:
        seed()
        return {"message": "Banco de dados populado com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "inventory-agents"}
