from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

# ⚙️ .env dosyasını yükle
load_dotenv()

# 💾 VERİTABANI URL'SİNİ ENVIRONMENT'TAN AL
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./borsa_terminali.db")

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class HisseAnaliz(Base):
    __tablename__ = "hisse_analiz"
    id = Column(Integer, primary_key=True, index=True)
    hisse_kodu = Column(String, unique=True, index=True)
    fiyat = Column(Float)
    rsi = Column(Float)
    puan = Column(Integer)
    karar = Column(String)
    risk_seviyesi = Column(String)
    zarar_kes = Column(Float)
    kar_al = Column(Float)
    tp1 = Column(Float, nullable=True)
    tp2 = Column(Float, nullable=True)
    initial_stop = Column(Float, nullable=True)
    genc_hisse = Column(Boolean, default=False)
    borsa = Column(String, default="BIST")
    # Health tracking — worker tarafindan yuklenen veri kalitesini izler
    is_active = Column(Boolean, default=True)
    health_score = Column(Integer, default=0)

class Portfoy(Base):
    __tablename__ = "portfoy"
    id = Column(Integer, primary_key=True, index=True)
    hisse_kodu = Column(String, unique=True, index=True)

# === YENİ: YAPAY ZEKA BAŞARI KARNESİ (SİNYAL HAFIZASI) ===
class SinyalGecmisi(Base):
    __tablename__ = "sinyal_gecmisi"
    id = Column(Integer, primary_key=True, index=True)
    hisse_kodu = Column(String, index=True)
    sinyal_tarihi = Column(DateTime, default=datetime.utcnow)
    
    # Giriş ve Karar
    giris_fiyati = Column(Float)
    karar = Column(String) 
    
    # Kar Maksimizasyonu (Profit Maximizer)
    tp1 = Column(Float, nullable=True)
    tp2 = Column(Float, nullable=True)
    hedef_fiyat = Column(Float) # Geriye dönük uyumluluk için (TP2 veya ana hedef)
    
    # Risk Yönetimi
    initial_stop = Column(Float, nullable=True)
    current_stop = Column(Float, nullable=True)
    stop_fiyat = Column(Float) # Geriye dönük uyumluluk
    
    # Performans Takibi
    highest_high = Column(Float, nullable=True)
    mfe_percent = Column(Float, default=0.0) # Max Favorable Excursion
    max_getiri_yuzdesi = Column(Float, default=0.0)
    
    # Durum Yönetimi
    durum = Column(String, default="ACTIVE") # ACTIVE, TP1_HIT_RISK_FREE, TP2_HIT_WIN, TRAILING_STOP_HIT, STOPPED_OUT
    kapanis_tarihi = Column(DateTime, nullable=True)

Base.metadata.create_all(bind=engine)