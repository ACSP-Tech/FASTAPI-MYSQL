from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Count(BaseModel):
    id: str
    name: str
    capital: Optional[str]
    region: Optional[str]
    population: int
    currency_code: str
    exchange_rate: Optional[float]
    estimated_gdp: Optional[float]
    flag: Optional[str] 
    last_refreshed_at: datetime


class ResStatus(BaseModel):
    total_countries: int
    last_refreshed_at: datetime