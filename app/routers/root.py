from fastapi import APIRouter, Response
from ..databasesetup import get_db
from fastapi import Depends
from sqlmodel import text

router = APIRouter(tags=["Root"])

# Render liveness check
@router.get("/")
async def root():
    """
    root endpoint
    """
    return {"app_name": "Country Currency Exchange API",
            "redoc": "check out the documentation via redoc"}

@router.head("/")
async def root_head():
    """
    head health check endpoint
    """
    return Response(status_code=200)

@router.get("/internal/keepalive")
async def keepalive(session=Depends(get_db)):
    await session.execute(text("SELECT 1"))
    return {"ok": True}

