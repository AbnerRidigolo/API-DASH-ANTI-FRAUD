"""
database.py — Configuração do banco de dados SQLite com SQLAlchemy.
Persiste os resultados de análise de fraude entre reinicializações da API.
"""

from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./antifraude.db")

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class MissionUnitDB(Base):
    __tablename__ = "mission_units"

    mu_id            = Column(String,  primary_key=True, index=True)
    missionario_nome = Column(String,  nullable=False)
    missao_nome      = Column(String,  nullable=False)
    recompensa_rs    = Column(Float,   nullable=False)
    status           = Column(String,  nullable=False)
    fraud_score      = Column(Float,   nullable=False)
    fraud_nivel      = Column(String,  nullable=False)
    n_flags          = Column(Integer, nullable=False, default=0)
    analisado_em     = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Cria as tabelas se ainda não existirem."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency do FastAPI — fornece sessão e fecha ao terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
