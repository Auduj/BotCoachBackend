from twitchio.ext import commands
from flask import Flask, jsonify
from dotenv import load_dotenv
from flask_cors import CORS
import requests
import threading
import time
import os

# --- Charger les variables d'environnement ---
load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
CHANNEL = os.getenv("CHANNEL")
TOKEN_URL = "https://id.twitch.tv/oauth2/token"

# --- Flask Setup ---
app = Flask(__name__)
CORS(app, origins=["https://auduj.github.io"])
participants = {}

@app.route('/')
def home():
    return jsonify({"status": "BotCoachTwitch API is running"})

@app.route('/participants')
def get_participants():
    return jsonify(participants)

@app.route('/participants', methods=['DELETE'])
def reset_participants():
    participants.clear()
    return jsonify({"message": "Liste des participants réinitialisée"}), 200

# --- Token Manager ---
token_expiry = time.time() + 3600

def refresh_access_token():
    global ACCESS_TOKEN, REFRESH_TOKEN, token_expiry
    print("🔁 Rafraîchissement du token...")

    params = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID
    }

    response = requests.post(TOKEN_URL, params=params)
    data = response.json()

    if "access_token" in data:
        ACCESS_TOKEN = f"oauth:{data['access_token']}"
        REFRESH_TOKEN = data["refresh_token"]
        token_expiry = time.time() + data["expires_in"]
        print("✅ Nouveau token rafraîchi.")
    else:
        print("❌ Erreur lors du rafraîchissement :", data)

def get_valid_token():
    if time.time() >= token_expiry:
        refresh_access_token()
    return ACCESS_TOKEN

# --- Twitch Bot ---
class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=get_valid_token(),
            prefix='!',
            initial_channels=[CHANNEL]
        )

    async def event_ready(self):
        print(f"✅ Bot connecté en tant que {self.nick}")

    async def event_message(self, message):
        if message.echo:
            return
        await self.handle_commands(message)

    @commands.command(name='coachme')
    async def coachme(self, ctx):
        parts = ctx.message.content.strip().split()
        user = ctx.author.name

        if user in participants:
            game_id = participants[user]
            await ctx.send(f"{user}, tu es déjà inscrit avec l'ID : {game_id} 🛡️")
            return

        if len(parts) == 2:
            game_id = parts[1]
            participants[user] = game_id
            await ctx.send(f"{user} a été ajouté avec l'ID de game : {game_id}")
        else:
            await ctx.send("❗ Utilisation correcte : !coachme ID_DE_GAME")


# --- Démarrage Flask + Bot ---
def start_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    threading.Thread(target=start_flask).start()
    bot = Bot()
    bot.run()
