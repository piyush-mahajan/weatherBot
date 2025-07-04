from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from app.bot import setup_bot, handle_update
from app.database import init_db
from app.admin import router as admin_router
import os
import logging
from contextlib import asynccontextmanager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize MongoDB and Telegram bot
    try:
        logger.info("Initializing application")
        init_db()  # Initialize MongoDB connection
        await setup_bot()  # Initialize Telegram bot
        logger.info("Application initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise
    yield
    # Shutdown: Cleanup if needed
    logger.info("Shutting down application")

app = FastAPI(lifespan=lifespan)

app.include_router(admin_router, prefix="/admin")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html>
        <head><title>Weather Bot</title></head>
        <body>
            <h1>PrabhatWeatherBot</h1>
            <p>Welcome to the Weather Bot API. Use <a href="/admin">Admin Panel</a> to manage users and settings.</p>
        </body>
    </html>
    """

@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    try:
        update = await request.json()
        logger.info(f"Received webhook update: {update}")
        await handle_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))