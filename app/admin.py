from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.database import get_db
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

class BotSettings(BaseModel):
    telegram_bot_token: str
    openweathermap_api_key: str

@router.get("/", response_class=HTMLResponse)
async def admin_panel():
    db = get_db()
    try:
        logger.info("Accessing admin panel")
        users = list(db["users"].find())
        user_rows = "".join(
            f"<tr><td>{user['chat_id']}</td><td>{user.get('city', 'N/A')}</td><td>{user.get('is_subscribed', False)}</td><td>{user.get('is_blocked', False)}</td>"
            f"<td><a href='/admin/block/{user['chat_id']}'>{'Unblock' if user.get('is_blocked', False) else 'Block'}</a> | "
            f"<a href='/admin/delete/{user['chat_id']}' onclick='return confirm(\"Are you sure?\")'>Delete</a></td></tr>"
            for user in users
        )
        return f"""
        <html>
            <head><title>Admin Panel</title></head>
            <body>
                <h1>Admin Panel - Weather Bot</h1>
                <h2>Update Bot Settings</h2>
                <form action="/admin/update-settings" method="post">
                    <label>Telegram Bot Token:</label><br>
                    <input type="text" name="telegram_bot_token" value="{os.getenv('TELEGRAM_BOT_TOKEN')}" required><br>
                    <label>OpenWeatherMap API Key:</label><br>
                    <input type="text" name="openweathermap_api_key" value="{os.getenv('OPENWEATHERMAP_API_KEY')}" required><br>
                    <button type="submit">Update Settings</button>
                </form>
                <h2>Manage Users</h2>
                <table border="1">
                    <tr><th>Chat ID</th><th>City</th><th>Subscribed</th><th>Blocked</th><th>Actions</th></tr>
                    {user_rows}
                </table>
            </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error in admin_panel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error accessing admin panel: {str(e)}")

@router.post("/update-settings")
async def update_settings(settings: BotSettings):
    try:
        logger.info("Updating bot settings")
        with open(".env", "w") as f:
            f.write(f"TELEGRAM_BOT_TOKEN={settings.telegram_bot_token}\n")
            f.write(f"OPENWEATHERMAP_API_KEY={settings.openweathermap_api_key}\n")
            f.write(f"MONGO_URI={os.getenv('MONGO_URI')}\n")
            f.write(f"ADMIN_USERNAME={os.getenv('ADMIN_USERNAME')}\n")
            f.write(f"ADMIN_PASSWORD={os.getenv('ADMIN_PASSWORD')}\n")
        os.environ["TELEGRAM_BOT_TOKEN"] = settings.telegram_bot_token
        os.environ["OPENWEATHERMAP_API_KEY"] = settings.openweathermap_api_key
        return {"message": "Settings updated successfully"}
    except Exception as e:
        logger.error(f"Error in update_settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating settings: {str(e)}")

@router.get("/block/{chat_id}")
async def block_user(chat_id: str):
    db = get_db()
    try:
        logger.info(f"Blocking/unblocking user with chat_id: {chat_id}")
        user = db["users"].find_one({"chat_id": chat_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        new_block_status = not user.get("is_blocked", False)
        db["users"].update_one({"chat_id": chat_id}, {"$set": {"is_blocked": new_block_status}})
        return {"message": f"User {chat_id} {'blocked' if new_block_status else 'unblocked'}"}
    except Exception as e:
        logger.error(f"Error in block_user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error blocking/unblocking user: {str(e)}")

@router.get("/delete/{chat_id}")
async def delete_user(chat_id: str):
    db = get_db()
    try:
        logger.info(f"Deleting user with chat_id: {chat_id}")
        result = db["users"].delete_one({"chat_id": chat_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": f"User {chat_id} deleted"}
    except Exception as e:
        logger.error(f"Error in delete_user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")