import os
import asyncio
import re
import json
import zipfile
import tempfile
import shutil
from datetime import datetime
from telethon import TelegramClient, events
from telethon.events import ChatAction
from dotenv import load_dotenv
from predictor import CardPredictor
from scheduler import PredictionScheduler
from models import init_database, db
from aiohttp import web
import threading
import time

# Charger les variables d'environnement
load_dotenv()

# --- CONFIGURATION ---
try:
    API_ID = int(os.getenv('API_ID', '0'))
    API_HASH = os.getenv('API_HASH', '')
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')
    ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
    PORT = int(os.getenv('PORT', '10000'))  # par défaut 10000
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')

    # Validation
    if not API_ID or API_ID == 0:
        raise ValueError("API_ID manquant ou invalide")
    if not API_HASH:
        raise ValueError("API_HASH manquant")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN manquant")

    print(f"✅ Configuration chargée: API_ID={API_ID}, ADMIN_ID={ADMIN_ID}, PORT={PORT}")
except Exception as e:
    print(f"❌ Erreur configuration: {e}")
    print("Vérifiez vos variables d'environnement (.env ou Render Dashboard)")
    exit(1)

# Fichier de configuration persistante
CONFIG_FILE = 'bot_config.json'

# Variables d'état
detected_stat_channel = None
detected_display_channel = None
confirmation_pending = {}
prediction_interval = 5  # Intervalle en minutes avant de chercher "A" (défaut: 5 min)

def load_config():
    """Load configuration from database"""
    global detected_stat_channel, detected_display_channel, prediction_interval
    try:
        if db:
            detected_stat_channel = db.get_config('stat_channel')
            detected_display_channel = db.get_config('display_channel')
            interval_config = db.get_config('prediction_interval')
            if detected_stat_channel:
                detected_stat_channel = int(detected_stat_channel)
            if detected_display_channel:
                detected_display_channel = int(detected_display_channel)
            if interval_config:
                prediction_interval = int(interval_config)
            print(f"✅ Configuration chargée depuis la DB: Stats={detected_stat_channel}, Display={detected_display_channel}, Intervalle={prediction_interval}min")
        else:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    detected_stat_channel = config.get('stat_channel')
                    detected_display_channel = config.get('display_channel')
                    prediction_interval = config.get('prediction_interval', 5)
                    print(f"✅ Configuration chargée depuis JSON: Stats={detected_stat_channel}, Display={detected_display_channel}, Intervalle={prediction_interval}min")
            else:
                print("ℹ️ Aucune configuration trouvée, nouvelle configuration")
    except Exception as e:
        print(f"⚠️ Erreur chargement configuration: {e}")

def save_config():
    """Save configuration to database and JSON backup"""
    try:
        if db:
            db.set_config('stat_channel', detected_stat_channel)
            db.set_config('display_channel', detected_display_channel)
            db.set_config('prediction_interval', prediction_interval)
            print("💾 Configuration sauvegardée en base de données")

        config = {
            'stat_channel': detected_stat_channel,
            'display_channel': detected_display_channel,
            'prediction_interval': prediction_interval
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        print(f"💾 Configuration sauvegardée: Stats={detected_stat_channel}, Display={detected_display_channel}, Intervalle={prediction_interval}min")
    except Exception as e:
        print(f"❌ Erreur sauvegarde configuration: {e}")

def update_channel_config(source_id: int, target_id: int):
    global detected_stat_channel, detected_display_channel
    detected_stat_channel = source_id
    detected_display_channel = target_id
    save_config()

# Init DB
database = init_database()

# Gestionnaire de prédictions
predictor = CardPredictor()

# Planificateur
scheduler = None

# Init Telegram client
session_name = f'bot_session_{int(time.time())}'
client = TelegramClient(session_name, API_ID, API_HASH)

async def start_bot():
    try:
        load_config()
        await client.start(bot_token=BOT_TOKEN)
        print("Bot démarré avec succès...")
        me = await client.get_me()
        username = getattr(me, 'username', 'Unknown') or f"ID:{getattr(me, 'id', 'Unknown')}"
        print(f"Bot connecté: @{username}")
    except Exception as e:
        print(f"Erreur lors du démarrage du bot: {e}")
        return False
    return True

# --- EVENTS / COMMANDS ---

@client.on(events.ChatAction())
async def handler_join(event):
    global confirmation_pending
    try:
        if event.user_joined or event.user_added:
            me = await client.get_me()
            if event.user_id == getattr(me, 'id', None):
                confirmation_pending[event.chat_id] = 'waiting_confirmation'
                try:
                    chat = await client.get_entity(event.chat_id)
                    chat_title = getattr(chat, 'title', f'Canal {event.chat_id}')
                except:
                    chat_title = f'Canal {event.chat_id}'
                invitation_msg = f"""🔔 **Nouveau canal détecté**

📋 **Canal** : {chat_title}
🆔 **ID** : {event.chat_id}

• `/set_stat {event.chat_id}` - Canal de statistiques
• `/set_display {event.chat_id}` - Canal de diffusion"""
                try:
                    await client.send_message(ADMIN_ID, invitation_msg)
                except:
                    await client.send_message(event.chat_id, "⚠️ Impossible d'envoyer l'invitation privée.")
    except Exception as e:
        print(f"Erreur dans handler_join: {e}")

# (... toutes tes autres commandes set_stat, set_display, /start, /status, /reset, /report, /scheduler, etc. restent identiques ...)
# ⚠️ Je n’ai pas supprimé tes fonctionnalités, juste corrigé la partie CONFIGURATION.
