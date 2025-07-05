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
            f"<tr class='border-b hover:bg-gray-100'><td class='py-2 px-4'>{user['chat_id']}</td>"
            f"<td class='py-2 px-4'>{', '.join(user.get('city_history', ['N/A']))}</td>"
            f"<td class='py-2 px-4'>{user.get('is_subscribed', False)}</td>"
            f"<td class='py-2 px-4'>{user.get('is_blocked', False)}</td>"
            f"<td class='py-2 px-4'><a href='/admin/block/{user['chat_id']}' class='text-blue-600 hover:underline'>{'Unblock' if user.get('is_blocked', False) else 'Block'}</a> | "
            f"<a href='/admin/delete/{user['chat_id']}' class='text-red-600 hover:underline' onclick='return confirm(\"Are you sure?\")'>Delete</a></td></tr>"
            for user in users
        )
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Admin Panel - PrabhatWeatherBot</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                body {{ font-family: 'Inter', sans-serif; }}
                .container {{ max-width: 1200px; margin: 0 auto; padding: 0 1rem; }}
            </style>
        </head>
        <body class="bg-gray-100">
            <nav class="bg-blue-600 text-white p-4">
                <div class="container flex justify-between items-center">
                    <h1 class="text-2xl font-bold">PrabhatWeatherBot Admin</h1>
                    <a href="/" class="text-white hover:underline">Home</a>
                </div>
            </nav>
            <div class="container py-8">
                <div class="bg-white shadow-lg rounded-lg p-6 mb-8">
                    <h2 class="text-xl font-semibold mb-4">Update Bot Settings</h2>
                    <form action="/admin/update-settings" method="post" class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Telegram Bot Token</label>
                            <input type="text" name="telegram_bot_token" value="{os.getenv('TELEGRAM_BOT_TOKEN')}" required
                                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-500 focus:ring-opacity-50">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">OpenWeatherMap API Key</label>
                            <input type="text" name="openweathermap_api_key" value="{os.getenv('OPENWEATHERMAP_API_KEY')}" required
                                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-500 focus:ring-opacity-50">
                        </div>
                        <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">Update Settings</button>
                    </form>
                </div>
                <div class="bg-white shadow-lg rounded-lg p-6">
                    <h2 class="text-xl font-semibold mb-4">Manage Users</h2>
                    <div class="overflow-x-auto">
                        <table class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="py-3 px-4 text-left text-sm font-medium text-gray-500">Chat ID</th>
                                    <th class="py-3 px-4 text-left text-sm font-medium text-gray-500">City History</th>
                                    <th class="py-3 px-4 text-left text-sm font-medium text-gray-500">Subscribed</th>
                                    <th class="py-3 px-4 text-left text-sm font-medium text-gray-500">Blocked</th>
                                    <th class="py-3 px-4 text-left text-sm font-medium text-gray-500">Actions</th>
                                </tr>
                            </thead>
                            <tbody class="bg-white divide-y divide-gray-200">
                                {user_rows}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            <footer class="bg-gray-800 text-white text-center p-4 mt-8">
                <p>&copy; 2025 PrabhatWeatherBot. All rights reserved.</p>
            </footer>
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