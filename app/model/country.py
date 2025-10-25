from typing import Optional
import uuid
from sqlmodel import SQLModel, Field, Column
from datetime import datetime
from sqlalchemy import String, func, DateTime, Integer, FLOAT
class Country(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()),sa_column=Column(String(36), primary_key=True, nullable=False))
    name: str = Field(sa_column=Column(String, unique=True, nullable=False, index=True))
    capital: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True, index=True))
    region: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True, index=True))
    population: Optional[int] = Field(default=None, sa_column=Column(Integer, nullable=True, index=True))
    currency_code: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True, index=True))
    exchange_rate: Optional[float] = Field(default=None, sa_column=Column(FLOAT, nullable=True, index=True))
    estimated_gdp: Optional[float] = Field(default=None, sa_column=Column(FLOAT, nullable=True, index=True))
    flag_url: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True, index=True))
    last_refreshed_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False))

