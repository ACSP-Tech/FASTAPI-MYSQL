from fastapi import APIRouter, HTTPException, status, Depends, Response, Query
from ..databasesetup import get_db
from ..crud.country import fetch_external_url, get_image, delete_country, status_fetch, named_country, db_country
from typing import Optional, List
from ..schema.country import Count, ResStatus

router = APIRouter(tags=["Country Currency Exchange"])

@router.get("/countries", response_model=List[Count], status_code=status.HTTP_200_OK)
async def get_all_countries(
    region: Optional[str] = Query(None, description="Filter countries by region (e.g., Africa)"),
    currency: Optional[str] = Query(None, description="Filter countries by currency code (e.g., NGN)"),
    sort: Optional[str] = Query(None, description="Sort criteria: 'gdp_desc' or 'gdp_asc'") ,
    session = Depends(get_db)
):
    """
    Retrieves all countries from the database, supporting filtering by region and currency, 
    and sorting by estimated GDP.
    """
    try:
        return await db_country(region, currency, sort, session)
    except HTTPException as e:
        # Re-raise 404 or other expected HTTP errors
        raise e
    except Exception as e:
        # Handle unexpected errors during DB query or retrieval
        #print(f"Error serving summary image from DB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={ "error": "Internal server error" }
        )

@router.post("/countries/refresh", status_code=status.HTTP_201_CREATED)
async def all_countries_and_exchange_rate_endpoint(session=Depends(get_db)):
    try:
        """
        Endpoint to Fetch all countries and exchange rates, then cache them in the database
        - Match existing countries by name (case-insensitive comparison)
        - If country exists: Update all fields including recalculating estimated_gdp with a new random multiplier
        - If country doesn't exist: Insert new record
        - The random multiplier (1000-2000) would be generated fresh on each refresh for each country
        - successful refresh would update the global last_refreshed_at timestamp
        - When /countries/refresh runs:
            - After saving countries in the database, generate an image (e.g., cache/summary.png) containing:
                - Total number of countries
                - Top 5 countries by estimated GDP
                - Timestamp of last refresh
            - Save the generated image on disk at cache/summary.png.'
        - Add a new endpoint:
            - GET /countries/image → Serve the generated summary image
            - If no image exists, return:
                - { "error": "Summary image not found" }
        - Store or update everything in MySQL as cached data.
        - Error Handling: Return consistent JSON responses:
            - 404  { "error": "Country not found" }
            - 400  { "error": "Validation failed" }
            - 500  { "error": "Internal server error" }
        """
        return await fetch_external_url(session)
    except HTTPException as Httpexc:
        raise Httpexc 
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={ "error": "Internal server error" }
        )


@router.get("/countries/image", status_code=status.HTTP_200_OK)
async def get_summary_image_endpoint(session=Depends(get_db)):
    """
    Serve the generated summary image.
    
    Returns:
        200: Summary image file
        404: Image not found
    """
    try:
        return await get_image(session)
    except HTTPException as e:
        # Re-raise 404 or other expected HTTP errors
        raise e
    except Exception as e:
        # Handle unexpected errors during DB query or retrieval
        #print(f"Error serving summary image from DB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={ "error": "Internal server error" }
        )



@router.get("/status", response_model=ResStatus, status_code=status.HTTP_200_OK)
async def get_status_endpoint(session = Depends(get_db)):
    """
    Shows the total number of country records and the last refresh timestamp.
    """
    try:
        return await status_fetch(session)
    except HTTPException as e:
        # Re-raise 404 or other expected HTTP errors
        raise e
    except Exception as e:
        # Handle unexpected errors during DB query or retrieval
        #print(f"Error serving summary image from DB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={ "error": "Internal server error", "detail": str(e)}
        )


@router.get("/countries/{name}", status_code=status.HTTP_200_OK)
async def get_country_by_name(name: str, session = Depends(get_db)):
    """
    Retrieves a single country record by its name (case-insensitive).
    """
    try:
        return await named_country(name, session)
    except HTTPException as e:
        # Re-raise 404 or other expected HTTP errors
        raise e
    except Exception as e:
        # Handle unexpected errors during DB query or retrieval
        #print(f"Error serving summary image from DB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={ "error": "Internal server error" }
        )
    
    
@router.delete("/countries/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_country_endpoint(name: str, session = Depends(get_db)):
    """
    Deletes a country record by name (case-insensitive) and handles the required 
    404 and 500 JSON responses.
    """ 
    try:
        return await delete_country(name, session)
    except HTTPException as e:
        # Re-raise 404 or other expected HTTP errors
        raise e
    except Exception as e:
        # Handle unexpected errors during DB query or retrieval
        #print(f"Error serving summary image from DB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={ "error": "Internal server error" }
        )

    