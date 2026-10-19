from sqlalchemy import Column, Integer, String, DateTime, Index
from datetime import datetime
from database import Base


class SefazCheck(Base):
    __tablename__ = "sefaz_checks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    autorizador = Column(String, nullable=False)
    service = Column(String, nullable=False)
    status = Column(String, nullable=False)  # up | degraded | down

    __table_args__ = (Index("ix_sefaz_checks_time_aut", "checked_at", "autorizador"),)
