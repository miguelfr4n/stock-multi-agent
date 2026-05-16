from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    category = Column(String)
    unit = Column(String, default="un")
    cost_price = Column(Float, default=0.0)
    sale_price = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    stock = relationship("StockItem", back_populates="product", uselist=False)
    movements = relationship("Movement", back_populates="product")


class StockItem(Base):
    __tablename__ = "stock"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, ForeignKey("products.id"), unique=True)
    current_quantity = Column(Integer, default=0)
    min_quantity = Column(Integer, default=10)
    max_quantity = Column(Integer, default=100)
    location = Column(String, default="Depósito A")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="stock")


class Movement(Base):
    __tablename__ = "movements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, ForeignKey("products.id"))
    quantity = Column(Integer)  # positivo=entrada, negativo=saída
    movement_type = Column(String)  # "entrada", "saida", "ajuste", "perda"
    reason = Column(String)
    order_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="movements")


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True)
    product_id = Column(String, ForeignKey("products.id"))
    quantity = Column(Integer)
    customer_name = Column(String)
    order_type = Column(String, default="venda")  # "venda", "transferencia"
    status = Column(String, default="pendente")   # "pendente", "confirmado", "entregue", "cancelado"
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(String, primary_key=True)
    product_id = Column(String, ForeignKey("products.id"))
    quantity = Column(Integer)
    supplier = Column(String)
    unit_cost = Column(Float, default=0.0)
    status = Column(String, default="pendente")  # "pendente", "aprovado", "recebido", "cancelado"
    estimated_delivery = Column(DateTime, nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class StockRecommendation(Base):
    __tablename__ = "stock_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, ForeignKey("products.id"))
    recommendation = Column(String)  # "AUMENTAR", "MANTER", "DIMINUIR"
    current_min = Column(Integer)
    current_max = Column(Integer)
    suggested_min = Column(Integer)
    suggested_max = Column(Integer)
    justification = Column(Text)
    applied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
