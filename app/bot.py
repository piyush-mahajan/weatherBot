from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from app.database import get_db
from app.weather import get_weather
import os
import asyncio
import httpx
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global Application instance
application = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    logger.info(f"Received /start command from chat_id: {chat_id}")
    db = get_db()
    try:
        # Initialize user in database if not exists
        user = db["users"].find_one({"chat_id": chat_id})
        if not user:
            db["users"].insert_one({"chat_id": chat_id, "city_history": [], "is_subscribed": False, "is_blocked": False})
            logger.info(f"Initialized new user with chat_id: {chat_id}")
        keyboard = [
            [InlineKeyboardButton("Subscribe", callback_data="subscribe"),
             InlineKeyboardButton("Unsubscribe", callback_data="unsubscribe")],
            [InlineKeyboardButton("Get Weather", callback_data="get_weather")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Welcome to the Weather Bot! Choose an option:", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in start: {str(e)}")
        await update.message.reply_text("An error occurred. Please try again.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = str(query.message.chat_id)
    db = get_db()
    try:
        logger.info(f"Button callback received: {query.data} for chat_id: {chat_id}")
        user = db["users"].find_one({"chat_id": chat_id})
        if not user:
            logger.error(f"User not found for chat_id: {chat_id}")
            await query.message.reply_text("Please use /start to initialize your account.")
            return
        if query.data == "subscribe":
            if user.get("is_subscribed"):
                await query.message.reply_text("You are already subscribed! Send a city name to get weather updates.")
            else:
                db["users"].update_one({"chat_id": chat_id}, {"$set": {"is_subscribed": True}})
                logger.info(f"Subscribed chat_id: {chat_id}")
                await query.message.reply_text("Subscribed successfully! Please send a city name (e.g., Mumbai).")
        elif query.data == "unsubscribe":
            if user.get("is_subscribed"):
                db["users"].update_one({"chat_id": chat_id}, {"$set": {"is_subscribed": False}})
                logger.info(f"Unsubscribed chat_id: {chat_id}")
                await query.message.reply_text("Unsubscribed successfully! You can resubscribe anytime.")
            else:
                await query.message.reply_text("You are not subscribed!")
        elif query.data == "get_weather":
            if user.get("is_subscribed") and user.get("city_history"):
                weather_data = []
                for city in user["city_history"]:
                    weather = await get_weather(city)
                    weather_data.append(weather)
                response = "\n".join(weather_data)
                await query.message.reply_text(f"Your weather history:\n{response}")
            else:
                await query.message.reply_text("Please subscribe and set at least one city first.")
    except Exception as e:
        logger.error(f"Error in button_callback: {str(e)}")
        await query.message.reply_text("An error occurred. Please try again.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db()
    try:
        chat_id = str(update.message.chat_id)
        text = update.message.text.strip()
        logger.info(f"Message received from chat_id: {chat_id}, text: {text}")
        user = db["users"].find_one({"chat_id": chat_id})
        if not user:
            logger.error(f"User not found for chat_id: {chat_id}")
            await update.message.reply_text("Please use /start to begin.")
            return
        if user.get("is_subscribed"):
            city = text
            weather = await get_weather(city)
            if "Error" in weather:
                await update.message.reply_text(f"Invalid city name: {city}. Please try again (e.g., Mumbai, Pune).")
                return
            # Update city history, avoid duplicates
            city_history = user.get("city_history", [])
            if city not in city_history:
                city_history.append(city)
                db["users"].update_one({"chat_id": chat_id}, {"$set": {"city_history": city_history}})
                logger.info(f"Added {city} to city_history for chat_id: {chat_id}")
            await update.message.reply_text(f"Weather for {city}:\n{weather}")
        else:
            await update.message.reply_text("Please subscribe first using the Subscribe button.")
    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}")
        await update.message.reply_text("An error occurred. Please try again.")

async def send_weather_updates():
    while True:
        db = get_db()
        try:
            logger.info("Sending weather updates")
            users = db["users"].find({"is_subscribed": True})
            async with httpx.AsyncClient() as client:
                bot = Bot(os.getenv("TELEGRAM_BOT_TOKEN"))
                for user in users:
                    if user.get("city_history") and not user.get("is_blocked", False):
                        for city in user["city_history"]:
                            weather = await get_weather(city)
                            await bot.send_message(chat_id=user["chat_id"], text=weather)
        except Exception as e:
            logger.error(f"Error in send_weather_updates: {str(e)}")
        await asyncio.sleep(6 * 3600)  # Every 6 hours

async def setup_bot():
    global application
    try:
        logger.info("Initializing Telegram bot application")
        # Validate token
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set")
        
        # Initialize Application with minimal configuration
        application = Application.builder().token(token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Initialize application
        await application.initialize()
        logger.info("Application initialized successfully")
        
        # Set webhook
        webhook_url = os.getenv("WEBHOOK_URL", "https://weatherbot-qqj4.onrender.com/telegram-webhook")
        async with httpx.AsyncClient() as client:
            logger.info(f"Setting webhook to {webhook_url}")
            response = await client.get(f"https://api.telegram.org/bot{token}/setWebhook?url={webhook_url}")
            response_data = response.json()
            logger.info(f"Webhook set response: {response_data}")
            if not response_data.get("ok"):
                raise ValueError(f"Failed to set webhook: {response_data.get('description')}")
        
        # Start weather update loop
        asyncio.create_task(send_weather_updates())
    except Exception as e:
        logger.error(f"Error in setup_bot: {str(e)}")
        raise  # Re-raise to ensure startup fails if bot initialization fails

async def handle_update(update_dict):
    global application
    try:
        logger.info(f"Received update: {update_dict}")
        if application is None:
            logger.error("Application not initialized")
            raise ValueError("Application not initialized")
        update = Update.de_json(update_dict, application.bot)
        if update is None:
            logger.error("Failed to parse update")
            return
        await application.process_update(update)
    except Exception as e:
        logger.error(f"Error in handle_update: {str(e)}")