import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, LargeBinary, Float, DateTime, Date, func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

# Cloud-Ready Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

# Handle 'postgres://' -> 'postgresql://' fix for SQLAlchemy 2.0 (common in HeroKu/Streamlit Cloud)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Release(Base):
    __tablename__ = 'releases'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    release_date = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
    
    packs = relationship("Pack", back_populates="release")

class Squad(Base):
    __tablename__ = 'squads'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    
    packs = relationship("Pack", back_populates="squad")

class Pack(Base):
    __tablename__ = 'packs'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    release_id = Column(Integer, ForeignKey('releases.id'))
    squad_id = Column(Integer, ForeignKey('squads.id'))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
    
    release = relationship("Release", back_populates="packs")
    squad = relationship("Squad", back_populates="packs")
    scenarios = relationship("Scenario", back_populates="pack")
    templates = relationship("Template", secondary="pack_template_maps", back_populates="packs")

class Scenario(Base):
    __tablename__ = 'scenarios'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    status = Column(String)
    score = Column(Float)
    diff_summary = Column(String) # For storing text-based discrepancies
    llm_insight = Column(String, nullable=True) # AI-generated business summary
    comparison_mode = Column(String, default="TEXT_TABLE") 
    created_at = Column(DateTime, server_default=func.now())
    pack_id = Column(Integer, ForeignKey('packs.id'))
    template_id = Column(Integer, ForeignKey('templates.id'), nullable=True) # Linked to Golden Copy
    
    pack = relationship("Pack", back_populates="scenarios")
    template = relationship("Template")

class Template(Base):
    __tablename__ = 'templates'
    id = Column(Integer, primary_key=True)
    template_name = Column(String, unique=True)
    file_blob = Column(LargeBinary) # The "Golden Copy"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
    
    packs = relationship("Pack", secondary="pack_template_maps", back_populates="templates")

class PackTemplateMap(Base):
    __tablename__ = 'pack_template_maps'
    id = Column(Integer, primary_key=True)
    pack_id = Column(Integer, ForeignKey('packs.id'))
    template_id = Column(Integer, ForeignKey('templates.id'))
    created_at = Column(DateTime, server_default=func.now())
