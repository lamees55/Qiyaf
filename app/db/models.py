from datetime import datetime
from sqlalchemy import Column,Integer, String, Float, ForeignKey, DateTime, JSON, func
from sqlmodel import SQLModel, Field, Relationship 
from typing import List
# Instead of Base, we use SQLModel and add (table=True) for each class that represents a table
class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int = Field(default=None , primary_key=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str = Field()
    full_name: str = Field()

class Inspection(SQLModel, table=True):
    __tablename__ = "inspections"
    id: int = Field(default=None, primary_key=True, index=True) 
    title: str = Field() 
    status: str = Field(default="pending")
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    results: List["DetectionResult"] = Relationship(back_populates="inspection")
class DetectionResult(SQLModel, table=True):
    __tablename__ = "detection_results"
    id: int = Field(default=None, primary_key=True, index=True)
    inspection_id: int = Field(default=None, foreign_key="inspections.id")
    fault_type: str = Field()
    confidence: float = Field()
    box_coordinates: dict = Field(default={}, sa_column=Column(JSON))
    inspection: "Inspection" = Relationship(back_populates="results")