from .utils.database import normalize_mysql_url
from .sec import DATABASE_URL 
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException

# async MySQL URL
ASYNC_DATABASE_URL = normalize_mysql_url(DATABASE_URL)

# SQLModel engine
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    future=True
)

# async session maker
async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# async session dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting an asynchronous database session."""
    async with async_session() as session:
        try:
            yield session
        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=409, detail="Integrity constraint violated (e.g., duplicate entry).")
        except SQLAlchemyError as e:
            await session.rollback()
            # Log the specific SQLAlchemy error for debugging
            print(f"SQLAlchemy Error: {e}") 
            raise HTTPException(status_code=500, detail="A database error occurred.")
        except Exception:
            await session.rollback()
            raise


# initialize and create db and tables
async def init_db() -> None:
    """Initializes the database and creates all tables defined in SQLModel metadata."""
    async with engine.begin() as conn:
        # Pass the metadata to run_sync to create tables in MySQL
        await conn.run_sync(SQLModel.metadata.create_all)
