from fastapi import APIRouter

api_router = APIRouter()

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

@api_router.get("/")
async def root():
    return {"message": "Welcome to the AI Trading Copilot API!"}
