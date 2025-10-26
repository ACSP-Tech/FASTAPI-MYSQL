from ..utils.country import fetch_and_process_country_data
from ..model.country_table import Country, SummaryCache
from sqlmodel import select, func 
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from fastapi import HTTPException, status

from PIL import Image, ImageDraw, ImageFont # Requires 'Pillow' installed
from io import BytesIO # Used for in-memory binary streams

# ... (other imports) ...

async def generate_summary_image_data(refresh_time, session):
    """
    Generates the summary image and text, returning the binary data and text.
    """
    try:
        stmt = select(Country).order_by(Country.estimated_gdp.desc())
        result = await session.execute(stmt)
        countries = result.scalars().all()
        stmt2 = select(func.count()).select_from(Country)
        result2 = await session.execute(stmt2)
        total_count = result2.scalar_one()
        top_5 = countries[:5]

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
            gdp_value = f"${country.estimated_gdp:,g}" if country.estimated_gdp is not None else "N/A" 
            summary_text += f" {i+1}. {country.name}: {gdp_value}\n" # Use dot notation for name

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

        new_cache =  {
            "summary_image_data": image_data_bytes,
            "summary_text": summary_text,
            "filename": "cache/summary.png"
        }

        stmt = select(SummaryCache)
        result = await session.execute(stmt)
        existing_cache = result.scalars().first()

        if existing_cache:
            for key, value in new_cache.items():
                    setattr(existing_cache, key, value)
            
        else:
            create_cache = SummaryCache(**new_cache)
            session.add(create_cache)

        return countries
    
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Summary image not found"}
        )
    
    


async def fetch_external_url(session):
    try:
        processed_countries = await fetch_and_process_country_data()
        inserted_count = 0
        updated_count = 0

        #countries_for_summary = [] # List to hold data for image generation
        for country_data in processed_countries:
            # Check if country exists (case-insensitive)

            statement = select(Country).where(Country.name == country_data["name"].strip().title())
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
                session.add(existing_country)
                updated_count += 1
                
                # Append the updated object data for the summary image
                #countries_for_summary.append(existing_country.dict())
            else:
                # 3. INSERT new record
                new_country = Country(**new_data_for_model)
                session.add(new_country)
                inserted_count += 1
                
                # Append the new object data for the summary image
                #countries_for_summary.append(new_country.model_dump())

       

        # 4. Update global timestamp and generate image
        LAST_REFRESHED_TIMESTAMP = datetime.utcnow()
        process = await generate_summary_image_data(
            LAST_REFRESHED_TIMESTAMP,
            session
        )

        # 5. Commit all changes
        await session.commit()

        return process
    except HTTPException:
        await session.rollback()
        raise
    except Exception:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Summary image not found"}
        )
