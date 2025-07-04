from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse
from app.bot import setup_bot, handle_update
from app.database import init_db
from app.admin import router as admin_router
from dotenv import load_dotenv
import os
import uvicorn

load_dotenv()
app = FastAPI()
security = HTTPBasic()

# Initialize MongoDB client
init_db()

# Setup Telegram webhook
@app.on_event("startup")
async def startup_event():
    await setup_bot()

# Webhook endpoint for Telegram updates
@app.post("/telegram-webhook")
async def webhook(request: Request):
    update = await request.json()
    await handle_update(update)
    return {"status": "ok"}

# Admin panel authentication
def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = os.getenv("ADMIN_USERNAME")
    correct_password = os.getenv("ADMIN_PASSWORD")
    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Include admin routes
app.include_router(admin_router, prefix="/admin", dependencies=[Depends(verify_admin)])

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Telegram Weather Bot Server"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)