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

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
try:
    API_ID = int(os.getenv('API_ID') or '0')
    API_HASH = os.getenv('API_HASH') or ''
    BOT_TOKEN = os.getenv('BOT_TOKEN') or ''
    ADMIN_ID = int(os.getenv('ADMIN_ID') or '0')
    PORT = int(os.getenv('PORT') or '10000')

    # Validation des variables requises
    if not API_ID or API_ID == 0:
        raise ValueError("API_ID manquant ou invalide")
    if not API_HASH:
        raise ValueError("API_HASH manquant")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN manquant")

    print(f"✅ Configuration chargée: API_ID={API_ID}, ADMIN_ID={ADMIN_ID}, PORT={PORT}")
except API_ID= 29177661
API_HASH= a8639172fa8d35dbfd8ea46286d349ab
BOT_TOKEN= 8442253971:AAEisYucgZ49Ej2b-mK9_6DhNrqh9WOc_XU
ADMIN_ID=1190237801
RENDER_DEPLOYMENT=true
PORT=10000



WEBHOOK_URL=https://twok-joker.onrenjjjder.com as e:
    print(f"❌ Erreur configuration: {e}")
    print("Vérifiez vos variables d'environnement")
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
            # Fallback vers l'ancien système JSON si DB non disponible
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
            # Sauvegarde en base de données
            db.set_config('stat_channel', detected_stat_channel)
            db.set_config('display_channel', detected_display_channel)
            db.set_config('prediction_interval', prediction_interval)
            print("💾 Configuration sauvegardée en base de données")

        # Sauvegarde JSON de secours
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
    """Update channel configuration"""
    global detected_stat_channel, detected_display_channel
    detected_stat_channel = source_id
    detected_display_channel = target_id
    save_config()

# Initialize database
database = init_database()

# Gestionnaire de prédictions
predictor = CardPredictor()

# Planificateur automatique
scheduler = None

# Initialize Telegram client with unique session name
import time
session_name = f'bot_session_{int(time.time())}'
client = TelegramClient(session_name, API_ID, API_HASH)

async def start_bot():
    """Start the bot with proper error handling"""
    try:
        # Load saved configuration first
        load_config()

        await client.start(bot_token=BOT_TOKEN)
        print("Bot démarré avec succès...")

        # Get bot info
        me = await client.get_me()
        username = getattr(me, 'username', 'Unknown') or f"ID:{getattr(me, 'id', 'Unknown')}"
        print(f"Bot connecté: @{username}")

    except Exception as e:
        print(f"Erreur lors du démarrage du bot: {e}")
        return False

    return True

# --- INVITATION / CONFIRMATION ---
@client.on(events.ChatAction())
async def handler_join(event):
    """Handle bot joining channels/groups"""
    global confirmation_pending

    try:
        print(f"ChatAction event: {event}")
        print(f"user_joined: {event.user_joined}, user_added: {event.user_added}")
        print(f"user_id: {event.user_id}, chat_id: {event.chat_id}")

        if event.user_joined or event.user_added:
            me = await client.get_me()
            me_id = getattr(me, 'id', None)
            print(f"Mon ID: {me_id}, Event user_id: {event.user_id}")

            if event.user_id == me_id:
                confirmation_pending[event.chat_id] = 'waiting_confirmation'

                # Get channel info
                try:
                    chat = await client.get_entity(event.chat_id)
                    chat_title = getattr(chat, 'title', f'Canal {event.chat_id}')
                except:
                    chat_title = f'Canal {event.chat_id}'

                # Send private invitation to admin
                invitation_msg = f"""🔔 **Nouveau canal détecté**

📋 **Canal** : {chat_title}
🆔 **ID** : {event.chat_id}

**Choisissez le type de canal** :
• `/set_stat {event.chat_id}` - Canal de statistiques
• `/set_display {event.chat_id}` - Canal de diffusion

Envoyez votre choix en réponse à ce message."""

                try:
                    await client.send_message(ADMIN_ID, invitation_msg)
                    print(f"Invitation envoyée à l'admin pour le canal: {chat_title} ({event.chat_id})")
                except Exception as e:
                    print(f"Erreur envoi invitation privée: {e}")
                    # Fallback: send to the channel temporarily for testing
                    await client.send_message(event.chat_id, f"⚠️ Impossible d'envoyer l'invitation privée. Canal ID: {event.chat_id}")
                    print(f"Message fallback envoyé dans le canal {event.chat_id}")
    except Exception as e:
        print(f"Erreur dans handler_join: {e}")

@client.on(events.NewMessage(pattern=r'/set_stat (-?\d+)'))
async def set_stat_channel(event):
    """Set statistics channel (only admin in private)"""
    global detected_stat_channel, confirmation_pending

    try:
        # Only allow in private chat with admin
        if event.is_group or event.is_channel:
            return

        if event.sender_id != ADMIN_ID:
            await event.respond("❌ Seul l'administrateur peut configurer les canaux")
            return

        # Extract channel ID from command
        match = event.pattern_match
        channel_id = int(match.group(1))

        # Check if channel is waiting for confirmation
        if channel_id not in confirmation_pending:
            await event.respond("❌ Ce canal n'est pas en attente de configuration")
            return

        detected_stat_channel = channel_id
        confirmation_pending[channel_id] = 'configured_stat'

        # Save configuration
        save_config()

        try:
            chat = await client.get_entity(channel_id)
            chat_title = getattr(chat, 'title', f'Canal {channel_id}')
        except:
            chat_title = f'Canal {channel_id}'

        await event.respond(f"✅ **Canal de statistiques configuré**\n📋 {chat_title}\n\n✨ Le bot surveillera ce canal pour les prédictions - développé par Sossou Kouamé Appolinaire\n💾 Configuration sauvegardée automatiquement")
        print(f"Canal de statistiques configuré: {channel_id}")

    except Exception as e:
        print(f"Erreur dans set_stat_channel: {e}")

@client.on(events.NewMessage(pattern=r'/set_display (-?\d+)'))
async def set_display_channel(event):
    """Set display channel (only admin in private)"""
    global detected_display_channel, confirmation_pending

    try:
        # Only allow in private chat with admin
        if event.is_group or event.is_channel:
            return

        if event.sender_id != ADMIN_ID:
            await event.respond("❌ Seul l'administrateur peut configurer les canaux")
            return

        # Extract channel ID from command
        match = event.pattern_match
        channel_id = int(match.group(1))

        # Check if channel is waiting for confirmation
        if channel_id not in confirmation_pending:
            await event.respond("❌ Ce canal n'est pas en attente de configuration")
            return

        detected_display_channel = channel_id
        confirmation_pending[channel_id] = 'configured_display'

        # Save configuration
        save_config()

        try:
            chat = await client.get_entity(channel_id)
            chat_title = getattr(chat, 'title', f'Canal {channel_id}')
        except:
            chat_title = f'Canal {channel_id}'

        await event.respond(f"✅ **Canal de diffusion configuré**\n📋 {chat_title}\n\n🚀 Le bot publiera les prédictions dans ce canal - développé par Sossou Kouamé Appolinaire\n💾 Configuration sauvegardée automatiquement")
        print(f"Canal de diffusion configuré: {channel_id}")

    except Exception as e:
        print(f"Erreur dans set_display_channel: {e}")

# --- COMMANDES DE BASE ---
@client.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    """Send welcome message when user starts the bot"""
    try:
        welcome_msg = """🎯 **Bot de Prédiction de Cartes - Bienvenue !**

🔹 **Développé par Sossou Kouamé Appolinaire**

**Fonctionnalités** :
• Prédictions automatiques anticipées (déclenchées sur 7, 8)
• Prédictions pour les prochains jeux se terminant par 0
• Vérification des résultats avec statuts détaillés
• Rapports automatiques toutes les 20 prédictions mises à jour

**Configuration** :
1. Ajoutez-moi dans vos canaux
2. Je vous enverrai automatiquement une invitation privée
3. Répondez avec `/set_stat [ID]` ou `/set_display [ID]`

**Commandes** :
• `/start` - Ce message
• `/status` - État du bot (admin)
• `/intervalle` - Configure le délai de prédiction (admin)
• `/report` - Compteur de bilan détaillé (admin)
• `/sta` - Statut des déclencheurs (admin)
• `/reset` - Réinitialiser (admin)
• `/deploy` - Pack de déploiement 3D (admin)

Le bot est prêt à analyser vos jeux ! 🚀"""

        await event.respond(welcome_msg)
        print(f"Message de bienvenue envoyé à l'utilisateur {event.sender_id}")

        # Test message private pour vérifier la connectivité
        if event.sender_id == ADMIN_ID:
            await asyncio.sleep(2)
            test_msg = "🔧 Test de connectivité : Je peux vous envoyer des messages privés !"
            await event.respond(test_msg)

    except Exception as e:
        print(f"Erreur dans start_command: {e}")

# --- COMMANDES ADMINISTRATIVES ---
@client.on(events.NewMessage(pattern='/status'))
async def show_status(event):
    """Show bot status (admin only)"""
    try:
        if event.sender_id != ADMIN_ID:
            return

        config_status = "✅ Sauvegardée" if os.path.exists(CONFIG_FILE) else "❌ Non sauvegardée"
        status_msg = f"""📊 **Statut du Bot**

Canal statistiques: {'✅ Configuré' if detected_stat_channel else '❌ Non configuré'} ({detected_stat_channel})
Canal diffusion: {'✅ Configuré' if detected_display_channel else '❌ Non configuré'} ({detected_display_channel})
⏱️ Intervalle de prédiction: {prediction_interval} minutes
Configuration persistante: {config_status}
Prédictions actives: {len(predictor.prediction_status)}
Dernières prédictions: {len(predictor.last_predictions)}
Messages traités: {len(predictor.processed_messages)}
"""
        await event.respond(status_msg)
    except Exception as e:
        print(f"Erreur dans show_status: {e}")

@client.on(events.NewMessage(pattern='/reset'))
async def reset_bot(event):
    """Reset bot configuration (admin only)"""
    global detected_stat_channel, detected_display_channel, confirmation_pending

    try:
        if event.sender_id != ADMIN_ID:
            return

        detected_stat_channel = None
        detected_display_channel = None
        confirmation_pending.clear()
        predictor.reset()

        # Save the reset configuration
        save_config()

        await event.respond("🔄 Bot réinitialisé avec succès\n💾 Configuration effacée et sauvegardée")
        print("Bot réinitialisé par l'administrateur")
    except Exception as e:
        print(f"Erreur dans reset_bot: {e}")

# Handler /deploy supprimé - remplacé par le handler 2D plus bas

@client.on(events.NewMessage(pattern='/test_invite'))
async def test_invite(event):
    """Test sending invitation (admin only)"""
    try:
        if event.sender_id != ADMIN_ID:
            return

        # Test invitation message
        test_msg = f"""🔔 **Test d'invitation**

📋 **Canal test** : Canal de test
🆔 **ID** : -1001234567890

**Choisissez le type de canal** :
• `/set_stat -1001234567890` - Canal de statistiques
• `/set_display -1001234567890` - Canal de diffusion

Ceci est un message de test pour vérifier les invitations."""

        await event.respond(test_msg)
        print(f"Message de test envoyé à l'admin")

    except Exception as e:
        print(f"Erreur dans test_invite: {e}")

@client.on(events.NewMessage(pattern='/sta'))
async def show_trigger_numbers(event):
    """Show current trigger numbers for automatic predictions"""
    try:
        if event.sender_id != ADMIN_ID:
            return

        trigger_nums = list(predictor.trigger_numbers)
        trigger_nums.sort()

        msg = f"""📊 **Statut des Déclencheurs Automatiques**

🎯 **Numéros de fin activant les prédictions**: {', '.join(map(str, trigger_nums))}

📋 **Fonctionnement**:
• Le bot surveille les jeux se terminant par {', '.join(map(str, trigger_nums))}
• Il prédit automatiquement le prochain jeu se terminant par 0
• Format: "🔵 {{numéro}} 📌 D🔵 statut :''⌛''"

📈 **Statistiques actuelles**:
• Prédictions actives: {len([s for s in predictor.prediction_status.values() if s == '⌛'])}
• Canal stats configuré: {'✅' if detected_stat_channel else '❌'}
• Canal affichage configuré: {'✅' if detected_display_channel else '❌'}

💡 **Canal détecté**: {detected_stat_channel if detected_stat_channel else 'Aucun'}"""

        await event.respond(msg)
        print(f"Statut des déclencheurs envoyé à l'admin")

    except Exception as e:
        print(f"Erreur dans show_trigger_numbers: {e}")
        await event.respond(f"❌ Erreur: {e}")

@client.on(events.NewMessage(pattern='/report'))
async def show_report_status(event):
    """Show report counter and remaining messages until next automatic report"""
    try:
        if event.sender_id != ADMIN_ID:
            return

        total_predictions = len(predictor.status_log)
        processed_messages = len(predictor.processed_messages)
        pending_predictions = len([s for s in predictor.prediction_status.values() if s == '⌛'])

        # Calculate remaining until next report (every 20 predictions)
        if total_predictions == 0:
            remaining_for_report = 20
            last_report_at = 0
        else:
            last_report_at = (total_predictions // 20) * 20
            remaining_for_report = 20 - (total_predictions % 20)
            if remaining_for_report == 20:
                remaining_for_report = 0

        # Calculate statistics for completed predictions
        wins = sum(1 for _, status in predictor.status_log if '✅' in status)
        losses = sum(1 for _, status in predictor.status_log if '❌' in status or '⭕' in status)
        win_rate = (wins / total_predictions * 100) if total_predictions > 0 else 0.0

        msg = f"""📊 **Compteur de Bilan et Statut des Prédictions**

🎯 **Messages Traités**:
• Total de jeux traités: {processed_messages}
• Total de prédictions générées: {total_predictions}
• Prédictions en attente: {pending_predictions}

📈 **Résultats des Prédictions**:
• Prédictions réussies: {wins} ✅
• Prédictions échouées: {losses} ❌
• Taux de réussite: {win_rate:.1f}%

📋 **Compteur de Rapport Automatique**:
• Dernier rapport généré après: {last_report_at} prédictions
• Prédictions depuis dernier rapport: {total_predictions - last_report_at}
• Restant avant prochain rapport: {remaining_for_report}

⏰ **Prochaine Génération**:
{'🔄 Le prochain rapport sera généré automatiquement' if remaining_for_report > 0 else '✅ Prêt pour la génération du prochain rapport'}

💡 **Note**: Les rapports automatiques sont générés toutes les 20 prédictions mises à jour avec un statut final."""

        await event.respond(msg)
        print(f"Rapport de compteur envoyé à l'admin")

    except Exception as e:
        print(f"Erreur dans show_report_status: {e}")
        await event.respond(f"❌ Erreur: {e}")

# Handler /deploy supprimé - remplacé par le handler 2D unique

@client.on(events.NewMessage(pattern='/scheduler'))
async def manage_scheduler(event):
    """Gestion du planificateur automatique (admin uniquement)"""
    global scheduler
    try:
        if event.sender_id != ADMIN_ID:
            return

        # Parse command arguments
        message_parts = event.message.message.split()
        if len(message_parts) < 2:
            await event.respond("""🤖 **Commandes du Planificateur Automatique**

**Usage**: `/scheduler [commande]`

**Commandes disponibles**:
• `start` - Démarre le planificateur automatique
• `stop` - Arrête le planificateur
• `status` - Affiche le statut actuel
• `generate` - Génère une nouvelle planification
• `config [source_id] [target_id]` - Configure les canaux

**Exemple**: `/scheduler config -1001234567890 -1001987654321`""")
            return

        command = message_parts[1].lower()

        if command == "start":
            if not scheduler:
                if detected_stat_channel and detected_display_channel:
                    scheduler = PredictionScheduler(
                        client, predictor,
                        detected_stat_channel, detected_display_channel
                    )
                    # Démarre le planificateur en arrière-plan
                    asyncio.create_task(scheduler.run_scheduler())
                    await event.respond("✅ **Planificateur démarré**\n\nLe système de prédictions automatiques est maintenant actif.")
                else:
                    await event.respond("❌ **Configuration manquante**\n\nVeuillez d'abord configurer les canaux source et cible avec `/set_stat` et `/set_display`.")
            else:
                await event.respond("⚠️ **Planificateur déjà actif**\n\nUtilisez `/scheduler stop` pour l'arrêter.")

        elif command == "stop":
            if sc
