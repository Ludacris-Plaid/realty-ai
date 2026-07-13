from fastapi import APIRouter
from .v1.leads import router as leads_router
from .v1.agent import router as agent_router
from .v1.listings import router as listings_router
from .v1.documents import router as documents_router
from .v1.dashboard import router as dashboard_router

api_router = APIRouter()
api_router.include_router(leads_router, prefix="/leads", tags=["leads"])
api_router.include_router(agent_router, prefix="/agent", tags=["agent"])
api_router.include_router(listings_router, prefix="/listings", tags=["listings"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
