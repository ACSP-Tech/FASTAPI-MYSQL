from fastapi import APIRouter, HTTPException, status, Depends
from ..databasesetup import get_db
from ..crud import fetch_external_url

router = APIRouter(tags=["Country Currency Exchange"])

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


# @router.get("/countries/image", status_code=status.HTTP_200_OK)
# async def get_summary_image():
#     """
#     Serve the generated summary image.
    
#     Returns:
#         200: Summary image file
#         404: Image not found
#     """
#     if not SUMMARY_IMAGE_PATH.exists():
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail={"error": "Summary image not found"}
#         )
    
#     return FileResponse(
#         path=SUMMARY_IMAGE_PATH,
#         media_type="image/png",
#         filename="summary.png"
#     )