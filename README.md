🌍 Country Data & Currency Exchange API

An asynchronous data management service built with FastAPI and SQLModel, designed to fetch, process, and cache global country data, calculate estimated GDP, and provide filtered/sorted access via a high-performance REST API.This project implements optimized database operations using asyncio.gather for concurrent queries and atomic bulk transaction staging to ensure speed and data integrity.

✨ Key FeaturesAsynchronous 

Data Fetching: Utilizes httpx to concurrently pull data from external Country and Exchange Rate APIs.Calculated Caching: Computes an Estimated GDP (USD) using population, exchange rates, and a random multiplier, caching the results in a MySQL database.
Atomic Bulk UPSERT: Uses session.add_all within a single await session.commit() block to update and insert hundreds of country records atomically, preventing data inconsistencies.Image Caching: Generates a summary image (Top 5 GDP countries, total count) in memory (BytesIO + Pillow) and stores the binary data directly in the database (BLOB column).
Full CRUD & Filtering: Provides endpoints for fetching all countries with filters (region, currency, sorting), retrieving single countries, and deletion.
Deployment Ready: Configured to use the asynchronous aiomysql driver for production stability, with explicit connection pool cleanup (engine.dispose()).🚀 

Setup and Installation
Prerequisites
Python 3.10+A running MySQL/MariaDB instance.1. 
Environment SetupClone the repository and set up your virtual environment:Bashgit clone [YOUR_REPO_URL]
cd FASTAPI-MYSQL
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
2. Install DependenciesYour project requires specific asynchronous and image processing libraries:Bashpip install -r requirements.txt
# Key packages: fastapi, uvicorn, sqlmodel, httpx, aiomysql, Pillow
3. Environment VariablesCreate a .env file in your root directory and configure your database connection URL. Remember to use the standard URL format, and the normalize_mysql_url utility will handle conversion to the required mysql+aiomysql:// driver.Code snippet# .env file
DATABASE_URL="mysql://user:password@host:port/dbname"
4. Database InitializationRun your Alembic migrations to create the initial tables (country, summarycache):Bashalembic upgrade head

🔌 API Endpoints
The service runs on http://127.0.0.1:8000 (or your Railway deployment URL).
MethodEndpointDescription
POST/countries/refreshTriggers the entire process: Fetches data, calculates GDP, performs bulk UPSERT on all countries, updates the summary image cache, and commits atomically.GET/statusReturns the Total Count of countries and the Last Refresh Timestamp from the cache.
GET/countries/imageServes the generated PNG summary image (Top 5 GDP countries) directly from the database cache.
GET/countriesLists all countries. Supports filters (?region=Asia, ?currency=EUR) and sorting (?sort=gdp_desc).
GET/countries/{name}Retrieves a single country by name (case-insensitive lookup).
DELETE/countries/{name}Deletes a country record by name (case-insensitive).Error HandlingAll endpoints return standardized JSON error bodies:Status CodeResponse BodyUsage400 Bad Request{"error": "Validation failed"}Invalid user input (e.g., empty filter/path parameter).404 Not Found{"error": "Country not found"}Record requested via GET/DELETE was not found, or cache is uninitialized.500 Server Error{"error": "Internal server error"}General failure during DB transaction or image generation.

⚙️ Project Structure & Technology
The project is structured around clear separation of concerns:
Core Technologies Technology Role FastAPI High-performance API framework.SQLModelData modeling and asynchronous ORM (built on SQLAlchemy 2.0).MySQL / aiomysqlPersistent database storage using the fast asynchronous driver.Pillow (PIL)In-memory image generation (BytesIO).httpxAsynchronous network client for external API calls.AlembicDatabase migrations and schema control.Architectural Designapp/databasesetup.py: Initializes the AsyncEngine and AsyncSession, implementing URL normalization and explicit engine.dispose() for safe shutdown.app/crud/country.py: Contains the complex business logic, including the bulk UPSERT staging in fetch_external_url and concurrent queries in generate_summary_image_data.app/model/country_table.py: Defines the Country and SummaryCache models with explicit length constraints for MySQL compatibility.app/routers/country.py: Defines all public API endpoints and delegates logic to the CRUD layer.