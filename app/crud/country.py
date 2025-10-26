from ..utils.country import fetch_and_process_country_data
from ..model.country_table import Country, SummaryCache
from sqlmodel import select, func, and_
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from fastapi import HTTPException, status, Response
import asyncio
from ..schema.country import ResStatus

from PIL import Image, ImageDraw, ImageFont # Requires 'Pillow' installed
from io import BytesIO # Used for in-memory binary streams

# ... (other imports) ...

async def generate_summary_image_data(refresh_time, session):
    """
    Generates the summary image and text, returning the binary data and text.
    """
    try:
        try:
            #optimizing speed
            # Define concurrent queries
            count_stmt = select(func.count(Country.id)).select_from(Country)
            top_5_stmt = select(Country).order_by(Country.estimated_gdp.desc()).limit(5)
            cache_stmt = select(SummaryCache) # Assuming fixed ID=1

            # Execute all three DB calls concurrently (Huge speed gain here!)
            (count_result, top_5_result, cache_result) = await asyncio.gather(
                session.execute(count_stmt),
                session.execute(top_5_stmt),
                session.execute(cache_stmt),
            )
            
            # Process results
            total_count = count_result.scalar_one()
            top_5 = top_5_result.scalars().all()
            existing_cache = cache_result.scalars().first()
            # stmt = select(Country).order_by(Country.estimated_gdp.desc())
            # result = await session.execute(stmt)
            # countries = result.scalars().all()
            # stmt2 = select(func.count()).select_from(Country)
            # result2 = await session.execute(stmt2)
            # total_count = result2.scalar_one()
            # top_5 = countries[:5]

            # # 1. Get Top 5 by Estimated GDP (Same logic as before)
            # sorted_countries = sorted(
            #     countries, 
            #     key=lambda x: x.get("estimated_gdp") if x.get("estimated_gdp") is not None else -1, 
            #     reverse=True
            # )
            # top_5 = sorted_countries[:5]
            
            # 2. Format content for drawing (Text Summary)
            summary_text = f"--- Country Data Refresh Summary ---\n"
            summary_text += f"Total number of countries: {total_count}\n"
            summary_text += f"Timestamp of last refresh: {refresh_time.strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
            summary_text += "Top 5 Countries by Estimated GDP:\n"
            
            for i, country in enumerate(top_5):
                # Use dot notation for model attributes
                gdp_value = f"{country.estimated_gdp:,g}" if country.estimated_gdp is not None else "N/A" 
                summary_text += f" {i+1}. {country.name}: {gdp_value}\n" # Use dot notation for name
        except Exception:
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Summary image not found in 1"})
        try:
            # 3. Generate the PNG binary data in memory using BytesIO
        
            img_width, img_height = 800, 400
            img = Image.new('RGB', (img_width, img_height), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)
            
            # NOTE: Ensure you handle font loading safely in a production environment
            font = ImageFont.load_default() 

            draw.text((10, 10), summary_text, fill=(0, 0, 0), font=font)
            
            # Create an in-memory binary stream
            img_byte_arr = BytesIO()
            # Save the image content (PNG format) to the stream
            img.save(img_byte_arr, format='PNG') 
            
            # Get the binary data (bytes) from the stream
            image_data_bytes = img_byte_arr.getvalue() 
        except Exception:
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Summary image not found in 2"})
        try:
            new_cache =  {
                "summary_image_data": image_data_bytes,
                "summary_text": summary_text,
                "filename": "cache/summary.png"
            }

            # stmt = select(SummaryCache)
            # result = await session.execute(stmt)
            # existing_cache = result.scalars().first()

            if existing_cache:
                for key, value in new_cache.items():
                        setattr(existing_cache, key, value)
                session.add(existing_cache)
            else:
                create_cache = SummaryCache(**new_cache)
                session.add(create_cache)

            return {"total_count": total_count}
        except Exception:
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Summary image not found in 3"})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    


async def fetch_external_url(session):
    try:
        processed_countries = await fetch_and_process_country_data()
        inserted_count = 0
        updated_count = 0
        invalid_countries = []

        countries_to_stage = []
        #countries_for_summary = [] # List to hold data for image generation
        for country_data in processed_countries:
            # --- CUSTOM VALIDATION STEP ---
            validation_errors = {}
            
            validation_errors = {}
            if not country_data.get("name"):
                validation_errors["name"] = "is required"
            if country_data.get("population") is None:
                validation_errors["population"] = "is required"
            if country_data.get("currency_code") is None:
                # This catches Antarctica and other countries missing currency codes
                validation_errors["currency_code"] = "is required (Missing currency code from external API)"
            
            if validation_errors:
                invalid_countries.append({
                    "error": "Validation failed",
                    "details": validation_errors,
                    "name": country_data.get("name", "Unknown Country"),
                })
                continue # Skip invalid record
            
            # Normalize name for lookup (using your model's logic)
            country_name_normalized = country_data["name"].strip().title()

            # Check if country exists (case-insensitive)
            statement = select(Country).where(Country.name == country_name_normalized)
            result = await session.execute(statement)
            existing_country = result.scalars().first()
            

            # Prepare new data for Country object creation/update
            new_data_for_model = {
                k: v for k, v in country_data.items() 
                if k in Country.__fields__ # I don't have id fields comming in
            }
            new_data_for_model["last_refreshed_at"] = datetime.utcnow()
            
            if existing_country:
                # 2. UPDATE existing record
                for key, value in new_data_for_model.items():
                    setattr(existing_country, key, value)
                
                # SQLModel adds the object back to the session for tracking changes
                countries_to_stage.append(existing_country)
                #session.add(existing_country)
                updated_count += 1
                
                # Append the updated object data for the summary image
                #countries_for_summary.append(existing_country.dict())
            else:
                # 3. INSERT new record
                new_country = Country(**new_data_for_model)
                countries_to_stage.append(new_country)
                #session.add(new_country)
                inserted_count += 1
                
                # Append the new object data for the summary image
                #countries_for_summary.append(new_country.model_dump())

        # 2. Bulk Stage all Country objects (Faster than sequential session.add calls)
        session.add_all(countries_to_stage)


        # 4. Update global timestamp and generate image
        LAST_REFRESHED_TIMESTAMP = datetime.utcnow()

        process = await generate_summary_image_data(
            LAST_REFRESHED_TIMESTAMP,
            session
        )

        # 5. Commit all changes
        await session.commit()

        return {
            "message": "Country data refresh complete.",
            "status": "success",
            "valid_countries_updated": updated_count,
            "valid_countries_inserted": inserted_count,
            "invalid_countries_skipped": len(invalid_countries),
            "errors": invalid_countries, # Return the list of skipped countries and their errors
            "last_refreshed_at": LAST_REFRESHED_TIMESTAMP.isoformat()
        }
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

async def get_image(session):
    try:
            # 1. Query the single summary cache record (ID=1)
            # Assuming the SummaryCache record has a fixed ID (e.g., 1)
            stmt = select(SummaryCache)
            result = await session.execute(stmt)
            summary_cache = result.scalars().first()

            if not summary_cache or not summary_cache.summary_image_data:
                # 2. Return 404 if no record exists or if the data field is empty/null
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={ "error": "Summary image not found. Run /countries/refresh first." }
                )
            
            # 3. Serve the binary data from the database
            return Response(
                content=summary_cache.summary_image_data, 
                media_type="image/png" # Crucial for the browser to display the PNG correctly
            )

    except HTTPException as e:
        # Re-raise 404 or other expected HTTP errors
        raise e


async def delete_country(name, session):
    try:
        # 1. Normalize name for case-insensitive lookup
        normalized_name = name.strip().title()    
        # 2. Delete the country where name matches the normalized input
        # NOTE: Using delete().where() returns the number of rows affected.
        stmt = select(Country).where(Country.name == normalized_name)
        result = await session.execute(stmt)
        country_to_delete = result.scalars().first()
        
        # rowcount indicates how many rows were affected (deleted)
        if not country_to_delete:
            # Country not found
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={ "error": "Country not found" }
            )
        #delete session
        await session.delete(country_to_delete)
        # Commit the deletion
        await session.commit() 
        # 4. Return 204 No Content on success (FastAPI handles the response body correctly)
        return
    except HTTPException:
        # Re-raise 404 immediately
        await session.rollback()
        raise
    except Exception as e:
        # Rollback and handle internal server errors
        await session.rollback()
        print(f"Error deleting country '{name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={ "error": "Internal server error" }
        )

async def status_fetch(session):
    try:
        # 1. Define Concurrent Queries
        # Get total count of countries
        count_stmt = select(func.count(Country.name)).select_from(Country)
        # Get last refresh timestamp from cache (assuming ID=1)
        cache_stmt = select(SummaryCache)

        # 2. Execute concurrently to save time
        (count_result, cache_result) = await asyncio.gather(
            session.execute(count_stmt),
            session.execute(cache_stmt),
        )

        total_countries = count_result.scalar_one_or_none()
        summary_cache = cache_result.scalars().first()

        # 3. Handle 404 if data hasn't been cached (i.e., refresh never ran)
        if summary_cache is None or total_countries is None or total_countries == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={ "error": "Country not found" }
            )
        
        # 4. Format and return the required response
        return ResStatus(
            total_countries = total_countries,
            last_refreshed_at =  summary_cache.last_refreshed_at.isoformat()
        )

    except HTTPException:
        # Re-raise explicit HTTP exceptions (404)
        raise
    except Exception as e:
        # Return consistent 500 JSON response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={ "error": "Internal server error" }
        )

async def named_country(filt_name, session):
    try:
        name = filt_name.strip()
        if not name:
            # Check for empty name if FastAPI allows it (though usually handled by router)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={ "error": "Validation failed" }
            )

        # 1. Normalize the input name for case-insensitive lookup
        normalized_name = name.strip().title()
        
        # 2. Query the database for the matching country
        stmt = select(Country).where(Country.name == normalized_name)
        result = await session.execute(stmt)
        country = result.scalars().first()

        if not country:
            # 3. Return 404 if no country is found
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={ "error": "Country not found" }
            )

        # 4. Return the Country model instance
        return country

    except HTTPException:
        # Re-raise explicit HTTP exceptions (like 404)
        raise
    except Exception as e:
        # Handle internal server errors
        print(f"Error retrieving country '{name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={ "error": "Internal server error" }
        )
    
async def db_country(region, currency, sort, session):
    try:
        # Build dynamic filters
        filters = []
        
        if region is not None:
            normalized_region = region.strip().title()
            filters.append(Country.region == normalized_region)   
        if currency is not None:
            normalized_currency = currency.strip().upper()
            filters.append(Country.currency_code == normalized_currency)

        
        stmt = select(Country).where(and_(*filters) if filters else True)

        if sort is not None:
            sort_lower = sort.strip().lower()
            if sort_lower == 'gdp_desc':
                stmt = stmt.order_by(Country.estimated_gdp.desc())
            elif sort_lower == 'gdp_asc':
                stmt = stmt.order_by(Country.estimated_gdp.asc())
            
        # 3. Execute Query
        result = await session.execute(stmt)
        countries = result.scalars().all()
        
        # 4. Handle Empty Results for Filtered Queries
        # If no results and filters were applied, return 404 as requested
        if not countries:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={ "error": "Country not found" }
            )
        
        # 5. Return the list of Country model instances (can be empty if no filters applied)
        return countries
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={ "error": "Internal server error", "detail": str(e)}
        )
