from fastapi import APIRouter
from .v1.leads import router as leads_router
from .v1.listings import router as listings_router
from .v1.documents import router as documents_router
from .v1.dashboard import router as dashboard_router
from .v1.gmail import router as gmail_router
# from .v1.messages import router as messages_router  # ORM not available in container

api_router = APIRouter()
api_router.include_router(leads_router, prefix="/leads", tags=["leads"])
api_router.include_router(listings_router, prefix="/listings", tags=["listings"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(gmail_router, prefix="/gmail", tags=["gmail"])
# api_router.include_router(messages_router, prefix="/messages", tags=["messages"])
