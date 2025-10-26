from typing import Optional
import uuid
from sqlmodel import SQLModel, Field, Column
from datetime import datetime
from sqlalchemy import String, func, DateTime, Integer, FLOAT
from pydantic import field_validator

class Country(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()),sa_column=Column(String(36), primary_key=True, nullable=False))
    name: str = Field(sa_column=Column(String(100), unique=True, nullable=False, index=True))
    capital: Optional[str] = Field(default=None, sa_column=Column(String(100), nullable=True))
    region: Optional[str] = Field(default=None, sa_column=Column(String(100), nullable=True))
    population: int = Field(default=None, sa_column=Column(Integer, nullable=False, index=True))
    currency_code: str = Field(default=None, sa_column=Column(String(3), nullable=False, index=True))
    exchange_rate: float = Field(default=None, sa_column=Column(FLOAT, nullable=True))
    estimated_gdp: float = Field(default=None, sa_column=Column(FLOAT, nullable=True))
    flag: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))
    last_refreshed_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False))
    @field_validator("name", "region", mode="before")
    @classmethod
    def normalize_name_region(cls, value):
        """Normalize name and region to title case."""
        if isinstance(value, str) and value:
            return value.strip().title()
        return value
    
    @field_validator("currency_code", mode="before")
    @classmethod
    def normalize_currency_code(cls, value):
        """Normalize currency_code to uppercase."""
        if isinstance(value, str) and value:
            return value.strip().upper()
        return value
    

class SummaryCache(SQLModel, table=True):
    # We use a fixed ID since there will only ever be one summary record
    id: str = Field(default_factory=lambda: str(uuid.uuid4()),sa_column=Column(String(36), primary_key=True, nullable=False))
    
    # Stores the PNG image data as binary (BLOB)
    summary_image_data: bytes 
    summary_text: str = Field(sa_column=Column(String(2048), nullable=False))
    filename: str = Field(sa_column=Column(String(100), nullable=False))
    last_refreshed_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False))
