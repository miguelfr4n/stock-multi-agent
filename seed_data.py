import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from datetime import datetime, timedelta
import random
from database import get_session, init_db
from models import Product, StockItem, Movement


PRODUCTS = [
    {"id": "CAFE_GOURMET_500G",  "name": "Café Gourmet 500g",         "category": "Alimentos",    "unit": "un", "cost_price": 18.0,  "sale_price": 32.90},
    {"id": "ARROZ_TIPO1_5KG",    "name": "Arroz Tipo 1 5kg",           "category": "Alimentos",    "unit": "sc", "cost_price": 12.0,  "sale_price": 19.90},
    {"id": "OLEO_SOJA_900ML",    "name": "Óleo de Soja 900ml",         "category": "Alimentos",    "unit": "un", "cost_price": 5.50,  "sale_price": 8.90},
    {"id": "DETERGENTE_500ML",   "name": "Detergente Neutro 500ml",    "category": "Limpeza",      "unit": "un", "cost_price": 1.80,  "sale_price": 3.50},
    {"id": "PAPEL_HIGI_12UN",    "name": "Papel Higiênico 12 rolos",   "category": "Higiene",      "unit": "pct","cost_price": 9.0,   "sale_price": 15.90},
    {"id": "AGUA_MINERAL_20L",   "name": "Água Mineral 20L",           "category": "Bebidas",      "unit": "gl", "cost_price": 8.0,   "sale_price": 14.50},
    {"id": "SABAO_PO_1KG",       "name": "Sabão em Pó 1kg",            "category": "Limpeza",      "unit": "cx", "cost_price": 7.0,   "sale_price": 12.90},
    {"id": "REFRIGERANTE_2L",    "name": "Refrigerante 2L",            "category": "Bebidas",      "unit": "un", "cost_price": 4.20,  "sale_price": 7.50},
]

STOCK_CONFIG = [
    {"product_id": "CAFE_GOURMET_500G", "current_quantity": 28,  "min_quantity": 20,  "max_quantity": 120, "location": "Prateleira A1"},
    {"product_id": "ARROZ_TIPO1_5KG",   "current_quantity": 8,   "min_quantity": 15,  "max_quantity": 80,  "location": "Depósito B2"},
    {"product_id": "OLEO_SOJA_900ML",   "current_quantity": 55,  "min_quantity": 20,  "max_quantity": 100, "location": "Prateleira A3"},
    {"product_id": "DETERGENTE_500ML",  "current_quantity": 3,   "min_quantity": 10,  "max_quantity": 60,  "location": "Prateleira C1"},
    {"product_id": "PAPEL_HIGI_12UN",   "current_quantity": 40,  "min_quantity": 10,  "max_quantity": 50,  "location": "Depósito A1"},
    {"product_id": "AGUA_MINERAL_20L",  "current_quantity": 150, "min_quantity": 20,  "max_quantity": 80,  "location": "Depósito C3"},
    {"product_id": "SABAO_PO_1KG",      "current_quantity": 22,  "min_quantity": 10,  "max_quantity": 60,  "location": "Prateleira C2"},
    {"product_id": "REFRIGERANTE_2L",   "current_quantity": 18,  "min_quantity": 30,  "max_quantity": 150, "location": "Depósito B1"},
]


def generate_movements(db, product_id: str, days: int = 90):
    """Gera histórico de movimentações realistas para análise do advisor."""
    velocity_map = {
        "CAFE_GOURMET_500G": (4, 8, True),    # (min_dia, max_dia, crescendo)
        "ARROZ_TIPO1_5KG":   (2, 5, False),
        "OLEO_SOJA_900ML":   (1, 3, False),
        "DETERGENTE_500ML":  (3, 7, True),
        "PAPEL_HIGI_12UN":   (1, 4, False),
        "AGUA_MINERAL_20L":  (0, 1, False),   # produto parado
        "SABAO_PO_1KG":      (1, 3, False),
        "REFRIGERANTE_2L":   (5, 12, True),
    }

    min_v, max_v, growing = velocity_map.get(product_id, (1, 5, False))

    for day_offset in range(days, 0, -1):
        date = datetime.utcnow() - timedelta(days=day_offset)

        # Tendência crescente: mais saídas nos dias mais recentes
        if growing:
            factor = 1 + (days - day_offset) / days
            qty = int(random.randint(min_v, max_v) * factor)
        else:
            qty = random.randint(min_v, max_v)

        if qty > 0:
            movement = Movement(
                product_id=product_id,
                quantity=-qty,
                movement_type="saida",
                reason="Venda ao cliente",
                created_at=date,
            )
            db.add(movement)

        # Entradas periódicas (a cada ~30 dias)
        if day_offset % 28 == 0:
            entrada = random.randint(40, 80)
            movement_in = Movement(
                product_id=product_id,
                quantity=entrada,
                movement_type="entrada",
                reason="Reposição de estoque",
                created_at=date + timedelta(hours=2),
            )
            db.add(movement_in)


def seed():
    init_db()
    db = get_session()
    try:
        # Limpa dados existentes
        db.query(Movement).delete()
        db.query(StockItem).delete()
        db.query(Product).delete()
        db.commit()

        # Insere produtos
        for p in PRODUCTS:
            product = Product(**p)
            db.add(product)
        db.commit()

        # Insere estoque
        for s in STOCK_CONFIG:
            stock = StockItem(**s)
            db.add(stock)
        db.commit()

        # Gera histórico de movimentações
        for s in STOCK_CONFIG:
            generate_movements(db, s["product_id"])
        db.commit()

        print(f"✅ Seed concluído: {len(PRODUCTS)} produtos, estoque e histórico de 90 dias criados.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
