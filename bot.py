import discord
from discord.ext import commands
from flask import Flask, request, jsonify
from threading import Thread
from datetime import datetime, timedelta
import random, string
import json
import os

# ----------------- Config -----------------
DISCORD_TOKEN = os.environ.get("Discord_Codes")  # Railway Secret
PORT = int(os.environ.get("PORT", 5000))        # Railway sets PORT automatically
bot_prefix = "/"

# ----------------- Flask App -----------------
app = Flask(__name__)

# ----------------- API Key Storage -----------------
if os.path.exists("apikeys.json"):
    with open("apikeys.json", "r") as f:
        apikeys = json.load(f)
else:
    apikeys = {}

def save_keys():
    with open("apikeys.json", "w") as f:
        json.dump(apikeys, f)

# ----------------- Helper Functions -----------------
def generate_apikey():
    return "ZYYRO_" + ''.join(random.choices(string.ascii_letters + string.digits, k=16))

def verify_apikey(key):
    expire = apikeys.get(key)
    if expire:
        expire_dt = datetime.fromisoformat(expire)
        return expire_dt > datetime.utcnow()
    return False

# ----------------- Discord Bot -----------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix=bot_prefix, intents=intents)

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")

@bot.command()
async def createapikey(ctx, amount: int, unit: str):
    if ctx.author.guild_permissions.administrator:
        key = generate_apikey()
        now = datetime.utcnow()
        if "day" in unit.lower():
            expire = now + timedelta(days=amount)
        elif "hour" in unit.lower():
            expire = now + timedelta(hours=amount)
        elif "minute" in unit.lower():
            expire = now + timedelta(minutes=amount)
        else:
            await ctx.send("❌ Invalid unit! Use day/hour/minute")
            return
        apikeys[key] = expire.isoformat()
        save_keys()
        await ctx.send(f"✅ Created API Key: `{key}` (expires {expire} UTC)")
    else:
        await ctx.send("❌ Only admins can create API keys.")

@bot.command()
async def checkapikey(ctx, key: str):
    if verify_apikey(key):
        await ctx.send(f"✅ API Key `{key}` is valid.")
    else:
        await ctx.send(f"❌ API Key `{key}` invalid or expired.")

# ----------------- Flask HTTP API -----------------
@app.route("/api", methods=["POST"])
def api():
    data = request.get_json()
    player = data.get("player")
    key = data.get("apikey", "")
    action = data.get("action", "")
    target = data.get("target", "")
    duration = data.get("duration", "")
    msg = data.get("message", "")

    if action == "login":
        if verify_apikey(key):
            print(f"{player} logged in with valid key: {key}")
            return jsonify({"status": "valid"})
        else:
            print(f"{player} tried invalid key: {key}")
            return jsonify({"status": "invalid"})
    elif action == "fly":
        print(f"{player} activated Fly")
        return jsonify({"status": "ok"})
    elif action == "teleport":
        print(f"{player} teleport to {target}")
        return jsonify({"status": "ok"})
    elif action == "banned":
        print(f"{player} banned {target} for {duration}")
        return jsonify({"status": "ok"})
    elif action == "sendall":
        print(f"{player} send message to all: {msg}")
        return jsonify({"status": "ok"})
    elif action == "support":
        print(f"{player} support message: {msg}")
        return jsonify({"status": "ok"})
    return jsonify({"status": "unknown action"})

# ----------------- Ping Endpoint -----------------
@app.route("/")
def home():
    return "ZYYRO PANEL Bot Running on Railway!"

# ----------------- Run Flask in Thread -----------------
def run_flask():
    app.run(host="0.0.0.0", port=PORT)

Thread(target=run_flask).start()
bot.run(DISCORD_TOKEN)