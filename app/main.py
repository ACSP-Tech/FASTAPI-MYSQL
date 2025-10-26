#importing the necessary requirements
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .databasesetup import init_db, engine
from .setup_main import configure_cors, register_exception_handlers
from .middleware import LoggingMiddleware 

#importing routers
from .routers import root


# --- Lifespan Context Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    Initializes the database at startup.
    """
    await init_db()
    # The 'yield' signals that the startup phase is complete and the app is ready to serve requests
    try:
        yield
    finally:
        await engine.dispose()
        print("Application Shutdown: Cleanup complete.")

# --- FastAPI Application Instance ---

# Calling an instance of FastAPI with the lifespan context manager
app = FastAPI(
    title="Country Currency Exchange API",
    description="Asynchronous API for country and currency data management.",
    version="1.0.0",
    lifespan=lifespan
)

# Defining the CORS function and any other custom middleware
configure_cors(app)

#handling pydantic validations error
register_exception_handlers(app)

# Adding logging middleware
app.add_middleware(LoggingMiddleware)

#including routes
app.include_router(root.router)