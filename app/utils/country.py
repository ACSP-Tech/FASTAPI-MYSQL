import httpx
import random # <-- Imported the random module
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from pydantic import ValidationError

# --- API Endpoints and Constants ---

COUNTRIES_API_URL = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
EXCHANGE_RATE_API_URL = "https://open.er-api.com/v6/latest/USD"
API_TIMEOUT = 10  # Seconds

class ExternalAPIError(HTTPException):
    """Custom exception for 503 Service Unavailable errors."""
    def __init__(self, api_name: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "External data source unavailable",
                "details": f"Could not fetch data from {api_name}"
            }
        )

async def _fetch_json(client: httpx.AsyncClient, url: str, api_name: str):
    """Helper function to fetch and decode JSON with error handling."""
    try:
        response = await client.get(url, timeout=API_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError):
        # Handle network errors, timeouts, and non-200 HTTP status codes
        raise ExternalAPIError(api_name)
    except Exception:
        # Handle other unexpected errors (e.g., JSON decode failure)
        raise ExternalAPIError(api_name)

async def fetch_and_process_country_data() -> List[Dict[str, Any]]:
    """
    Fetches country data and exchange rates, processes the data 
    according to business rules, and returns a list of processed country dictionaries.
    """
    async with httpx.AsyncClient() as client:
        # 1. Fetch Country Data
        countries_data = await _fetch_json(
            client,
            COUNTRIES_API_URL,
            "Restcountries.com"
        )

        # 2. Fetch Exchange Rates
        rates_data = await _fetch_json(
            client,
            EXCHANGE_RATE_API_URL,
            "Open.er-api.com"
        )

        exchange_rates: Dict[str, float] = rates_data.get("rates", {})
        
        processed_countries: List[Dict[str, Any]] = []

        for country in countries_data:
            currency_code: Optional[str] = None
            exchange_rate: Optional[float] = None
            estimated_gdp: Optional[float] = None

            currencies = country.get("currencies")
            if currencies and isinstance(currencies, list) and len(currencies) > 0:
                currency_code = currencies[0].get("code")
            
            # --- Rule 1: Handle cases with a currency code ---
            if currency_code:
                # Get the rate from the fetched data
                rate = exchange_rates.get(currency_code)
                population = country.get("population", 0)
                
                if rate is None:
                    # --- Rule 3: Currency code not found in API ---
                    exchange_rate = None
                    estimated_gdp = None 
                else:
                    # Rate found: Perform the GDP calculation
                    exchange_rate = rate
                    
                    # Generate a random factor between 1000 and 2000
                    random_factor = random.uniform(1000.0, 2000.0) 
                    
                    # New GDP calculation: population × random(1000–2000) ÷ exchange_rate
                    if rate != 0:
                        estimated_gdp = (population * random_factor) / rate
                    else:
                        estimated_gdp = 0.0 # Avoid division by zero
            
            else:
                # --- Rule 2: Currencies array is empty or invalid ---
                # Set estimated_gdp to 0 as per rule (even if we initialized it to None, 
                # we explicitly set it to 0.0 here if currency is missing.)
                estimated_gdp = 0.0
                exchange_rate = None
                currency_code = None



            # Final Country Record for DB insertion
            processed_countries.append({
                "name": country.get("name"),
                "capital": country.get("capital"),
                "region": country.get("region"),
                "population": country.get("population"),
                "flag": country.get("flag"),
                "currency_code": currency_code,
                "exchange_rate": exchange_rate,
                "estimated_gdp": estimated_gdp
            })
            
        return processed_countries

            