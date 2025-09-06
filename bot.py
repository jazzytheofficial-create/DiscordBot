"""
TadzzyBot - Enhanced version with full shop, trading system, selling system and passive income
- Added comprehensive shop system with buying functionality
- Enhanced trading system with two-way trades
- Improved selling system with dynamic pricing
- Advanced passive income generation based on card rarity and price
- Cleaner help panels with organized sections
- Income tracking and reporting commands
"""

import discord
from discord.ext import commands, tasks
import json
import random
import asyncio
import os
import shutil
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
from dotenv import load_dotenv

# -----------------------------
# Config
# -----------------------------
DATA_FILE = "tadzzy_data.json"
DATA_BACKUP_DIR = "backups"
AUTOSAVE_INTERVAL_SECONDS = 60
STARTING_BALANCE = 50_000
MAX_COLLECTION_SLOTS = 15
LEVEL_XP_REWARD = 1
LEVEL_UP_XP_THRESHOLD = 50
LEVEL_REWARD_TADBUCKS = 5000
LEVEL_REWARD_TADZZY = 5
AUCTION_DEFAULT_DURATION_HOURS = 1

# -----------------------------
# Load token & set intents
# -----------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("ERROR: DISCORD_TOKEN not set in environment.")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# -----------------------------
# In-memory data structure (persisted to JSON)
# -----------------------------
data = {
    "tadbucks_balances": {},  # user_id: int
    "tadzzy_points": {},      # user_id: int
    "xp_levels": {},          # user_id: int
    "user_collections": {},   # user_id: [card dicts]
    "gamenights": [],         # list of links
    "auctions": {},           # player_name: auction dict
    "guess_db": {},           # we'll fill programmatically (clues)
    "trades": {},             # trade_id: trade dict
    "settings": {             # future expansions
        "starting_balance": STARTING_BALANCE
    }
}

# Initialize users dict for compatibility
users = {}

# -----------------------------
# Footballers & Cards (base)
# -----------------------------
footballers = [
    # Secret - Highest passive income generators
    {"name": "Tadstarman", "rarity": "Secret", "price": 100000000, "color": 0x000000, "income_rate": 5000},
    {"name": "Jeeves", "rarity": "Secret", "price": 95000000, "color": 0x000000, "income_rate": 4750},
    {"name": "Jazzy", "rarity": "Secret", "price": 90000000, "color": 0x000000, "income_rate": 4500},

    # Expensive
    {"name": "JustMatt", "rarity": "Expensive", "price": 5000000, "color": 0x00ff00, "income_rate": 2500},

    # Mythics
    {"name": "Leo", "rarity": "Mythic", "price": 3000000, "color": 0xff0000, "income_rate": 1500},
    {"name": "Gdigz", "rarity": "Mythic", "price": 2900000, "color": 0xff0000, "income_rate": 1450},
    {"name": "Pulse", "rarity": "Mythic", "price": 2800000, "color": 0xff0000, "income_rate": 1400},
    {"name": "Barou", "rarity": "Mythic", "price": 2750000, "color": 0xff0000, "income_rate": 1375},
    {"name": "Arving8", "rarity": "Mythic", "price": 2700000, "color": 0xff0000, "income_rate": 1350},

    # Legendary
    {"name": "deadp00l295", "rarity": "Legendary", "price": 2000067, "color": 0xffff00, "income_rate": 1000},
    {"name": "Messi", "rarity": "Legendary", "price": 1500000, "color": 0xffff00, "income_rate": 750},
    {"name": "Ronaldo", "rarity": "Legendary", "price": 1400000, "color": 0xffff00, "income_rate": 700},
    {"name": "Salah", "rarity": "Legendary", "price": 1300000, "color": 0xffff00, "income_rate": 650},
    {"name": "Son", "rarity": "Legendary", "price": 1200000, "color": 0xffff00, "income_rate": 600},
    {"name": "De Bruyne", "rarity": "Legendary", "price": 1100000, "color": 0xffff00, "income_rate": 550},
    {"name": "Modric", "rarity": "Legendary", "price": 1050000, "color": 0xffff00, "income_rate": 525},
    {"name": "Lewandowski", "rarity": "Legendary", "price": 1000000, "color": 0xffff00, "income_rate": 500},
    {"name": "Mbappe", "rarity": "Legendary", "price": 980000, "color": 0xffff00, "income_rate": 490},
    {"name": "Neymar", "rarity": "Legendary", "price": 960000, "color": 0xffff00, "income_rate": 480},

    # Epics
    {"name": "Haaland", "rarity": "Epic", "price": 850000, "color": 0x800080, "income_rate": 425},
    {"name": "Benzema", "rarity": "Epic", "price": 820000, "color": 0x800080, "income_rate": 410},
    {"name": "Vinicius Jr", "rarity": "Epic", "price": 800000, "color": 0x800080, "income_rate": 400},
    {"name": "Kane", "rarity": "Epic", "price": 780000, "color": 0x800080, "income_rate": 390},
    {"name": "Joy", "rarity": "Epic", "price": 750000, "color": 0x800080, "income_rate": 375},

    # Commons - Lower income generators
    {"name": "Rashford", "rarity": "Common", "price": 20000, "color": 0x0000ff, "income_rate": 10},
    {"name": "Sancho", "rarity": "Common", "price": 20000, "color": 0x0000ff, "income_rate": 10},
    {"name": "Pedri", "rarity": "Common", "price": 20000, "color": 0x0000ff, "income_rate": 10},
    {"name": "Gavi", "rarity": "Common", "price": 20000, "color": 0x0000ff, "income_rate": 10},
    {"name": "Musiala", "rarity": "Common", "price": 20000, "color": 0x0000ff, "income_rate": 10},
    {"name": "Kroos", "rarity": "Common", "price": 20000, "color": 0x0000ff, "income_rate": 10},
    {"name": "Joel", "rarity": "Common", "price": 20000, "color": 0x0000ff, "income_rate": 10},
    {"name": "Axel", "rarity": "Common", "price": 20000, "color": 0x0000ff, "income_rate": 10},
    {"name": "Dim", "rarity": "Common", "price": 17000, "color": 0x0000ff, "income_rate": 8},
    {"name": "Ex_xpo", "rarity": "Common", "price": 16000, "color": 0x0000ff, "income_rate": 8},
    {"name": "Yousef", "rarity": "Common", "price": 15000, "color": 0x0000ff, "income_rate": 7},
    {"name": "Mazzy", "rarity": "Common", "price": 14000, "color": 0x0000ff, "income_rate": 7},
    {"name": "lizardboyy", "rarity": "Common", "price": 13000, "color": 0x0000ff, "income_rate": 6},
    {"name": "NtanielGamer6", "rarity": "Common", "price": 12000, "color": 0x0000ff, "income_rate": 6},
    {"name": "kanye", "rarity": "Common", "price": 11000, "color": 0x0000ff, "income_rate": 5},
    {"name": "salvas", "rarity": "Common", "price": 10000, "color": 0x0000ff, "income_rate": 5},
    {"name": "Eggham", "rarity": "Common", "price": 9000, "color": 0x0000ff, "income_rate": 4},
    {"name": "Ducky", "rarity": "Common", "price": 8000, "color": 0x0000ff, "income_rate": 4},
    {"name": "Kaan", "rarity": "Common", "price": 7000, "color": 0x0000ff, "income_rate": 3},
    {"name": "Krosspy", "rarity": "Common", "price": 6000, "color": 0x0000ff, "income_rate": 3},
    {"name": "Tmerri", "rarity": "Common", "price": 5000, "color": 0x0000ff, "income_rate": 2},
    {"name": "Quixy", "rarity": "Common", "price": 4000, "color": 0x0000ff, "income_rate": 2},
    {"name": "Alexander Isak", "rarity": "Common", "price": 3000, "color": 0x0000ff, "income_rate": 1},
    {"name": "Itoshi Sae", "rarity": "Common", "price": 2000, "color": 0x0000ff, "income_rate": 1},
    {"name": "Bachira", "rarity": "Common", "price": 1000, "color": 0x0000ff, "income_rate": 1},
    {"name": "Mr.Incredible", "rarity": "Common", "price": 500, "color": 0x0000ff, "income_rate": 1},
]

# Auto-generate more commons to reach 50+ players
common_players = [f"Tadstarman Bot{i}" for i in range(1, 51 - len(footballers))]
for i, name in enumerate(common_players):
    footballers.append({"name": name, "rarity": "Common", "price": 150, "color": 0x0000ff, "income_rate": 1})

# Normalizing helper
def normalize_name(n: str) -> str:
    return n.strip().lower()

# find player card by name (case-insensitive)
def find_player_card_by_name(name: str) -> Optional[dict]:
    name_norm = normalize_name(name)
    for p in footballers:
        if normalize_name(p["name"]) == name_norm:
            return p
    return None

# -----------------------------
# Guess-the-player DB
# -----------------------------
def build_guess_db():
    g = {
        "easy": [
            ("Plays as an Argentine forward for PSG", "Messi"),
            ("Portuguese superstar, now at Al-Nassr", "Ronaldo"),
            ("Egyptian winger who plays for Liverpool", "Salah"),
            ("Polish striker known for lethal finishing", "Lewandowski"),
            ("French speedster who plays for PSG", "Mbappe"),
            ("Brazilian flair, now an epic name", "Neymar"),
        ],
        "normal": [
            ("Belgian creative mid at Manchester City", "De Bruyne"),
            ("Korean attacker at Spurs", "Son"),
            ("Former Barca & Bayern striker, Polish", "Lewandowski"),
            ("Portuguese-Brazilian flair (epic)", "Neymar"),
        ],
        "hard": [
            ("Italian Ballon d'Or winner in 2006, defender", "Cannavaro"),
            ("Dutch winger, retired in 2019, trickster", "Robben"),
            ("Mexican keeper famous at the 2014 World Cup", "Ochoa"),
            ("Japanese midfield legend at Celtic", "Nakamura"),
        ],
        "extreme": [
            ("Historic attacker nicknamed 'Tadstarman' (Secret)", "Tadstarman"),
            ("A secret legend whose card is Jeeves", "Jeeves"),
            ("Expensive player JustMatt — expensive rarity", "JustMatt"),
        ]
    }

    # Add programmatic clues for other footballers
    for p in footballers:
        name = p["name"]
        rarity = p["rarity"]
        if name.lower() in ["messi", "ronaldo", "salah", "mbappe", "neymar", "lewandowski"]:
            continue
        clue_easy = f"A {rarity} player named {name[0]}..."
        clue_normal = f"Player {name} is a {rarity} card."
        g.setdefault("easy", []).append((clue_easy, name))
        g.setdefault("normal", []).append((clue_normal, name))
        if rarity.lower() in ("mythic", "secret"):
            g.setdefault("hard", []).append((f"Special {rarity} card: {name}", name))
            g.setdefault("extreme", []).append((f"Rare: {name} (collector's item)", name))

    return g

data["guess_db"] = build_guess_db()

# -----------------------------
# Persistence: save & load to JSON
# -----------------------------
def load_data():
    global data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                file_data = json.load(f)
            for k in ["tadbucks_balances", "tadzzy_points", "xp_levels", "user_collections", "gamenights", "auctions", "trades", "settings"]:
                if k in file_data:
                    data[k] = file_data[k]
            print("✅ Loaded data from", DATA_FILE)
        except Exception as e:
            print("Failed to load data:", e)
    else:
        print("No data file found, starting fresh.")

def save_data():
    try:
        to_save = {
            k: data[k] for k in ["tadbucks_balances", "tadzzy_points", "xp_levels", "user_collections", "gamenights", "auctions", "trades", "settings"]
        }
        tmp = DATA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(to_save, f, ensure_ascii=False, indent=2)
        os.replace(tmp, DATA_FILE)
        return True
    except Exception as e:
        print("Failed to save data:", e)
        return False

def backup_data():
    os.makedirs(DATA_BACKUP_DIR, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(DATA_BACKUP_DIR, f"tadzzy_data_backup_{timestamp}.json")
    try:
        if os.path.exists(DATA_FILE):
            shutil.copy2(DATA_FILE, dest)
        return dest
    except Exception as e:
        print("Backup failed:", e)
        return None

# -----------------------------
# Utility functions
# -----------------------------
def ensure_user_exists(user_id: int):
    uid = str(user_id)
    if uid not in data["tadbucks_balances"]:
        data["tadbucks_balances"][uid] = data["settings"].get("starting_balance", STARTING_BALANCE)
    if uid not in data["tadzzy_points"]:
        data["tadzzy_points"][uid] = 0
    if uid not in data["xp_levels"]:
        data["xp_levels"][uid] = 0
    if uid not in data["user_collections"]:
        data["user_collections"][uid] = []

def get_balance(user_id: int) -> int:
    uid = str(user_id)
    return int(data["tadbucks_balances"].get(uid, data["settings"].get("starting_balance", STARTING_BALANCE)))

def set_balance(user_id: int, amount: int):
    uid = str(user_id)
    data["tadbucks_balances"][uid] = int(amount)

def add_to_collection(user_id: int, card: dict) -> bool:
    uid = str(user_id)
    ensure_user_exists(user_id)
    if len(data["user_collections"][uid]) >= MAX_COLLECTION_SLOTS:
        return False
    data["user_collections"][uid].append(card)
    return True

# Global variables for tracking
last_income_report = {}
total_income_tracker = {}
gamble_cooldowns: Dict[str, str] = {}
active_guess_games: Dict[str, dict] = {}
two_way_trades = {}
pending_trades = {}

# -----------------------------
# Background tasks
# -----------------------------
@tasks.loop(seconds=AUTOSAVE_INTERVAL_SECONDS)
async def autosave_task():
    saved = save_data()
    if saved:
        print(f"[{datetime.utcnow().isoformat()}] Autosaved data.")
    else:
        print(f"[{datetime.utcnow().isoformat()}] Autosave failed.")

@tasks.loop(minutes=30)
async def passive_income():
    for uid, coll in data["user_collections"].items():
        total_income = 0
        for card in coll:
            # Use the new income_rate field for more accurate passive income
            income = card.get("income_rate", 1)
            
            # Add bonus based on rarity for extra scaling
            rarity = card.get("rarity", "Common")
            if rarity == "Secret":
                income = int(income * 1.5)  # 50% bonus
            elif rarity == "Mythic":
                income = int(income * 1.3)  # 30% bonus
            elif rarity == "Legendary":
                income = int(income * 1.2)  # 20% bonus
            elif rarity == "Epic":
                income = int(income * 1.1)  # 10% bonus
            
            total_income += income

        if total_income > 0:
            data["tadbucks_balances"][uid] = data["tadbucks_balances"].get(uid, STARTING_BALANCE) + total_income
            last_income_report[uid] = total_income
            total_income_tracker[uid] = total_income_tracker.get(uid, 0) + total_income
            print(f"[Passive Income] User {uid} earned {total_income} Tadbucks.")

    save_data()

@passive_income.before_loop
async def before_passive_income():
    await bot.wait_until_ready()
    print("[Passive Income] System started.")

# -----------------------------
# Bot events
# -----------------------------
@bot.event
async def on_ready():
    print(f"✅ Bot ready as {bot.user} (ID: {bot.user.id})")
    load_data()
    if not autosave_task.is_running():
        autosave_task.start()
    if not passive_income.is_running():
        passive_income.start()
    await bot.change_presence(activity=discord.Game(name="type !help"))

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    
    # XP system per message
    uid = message.author.id
    ensure_user_exists(uid)
    data["xp_levels"][str(uid)] = int(data["xp_levels"].get(str(uid), 0)) + LEVEL_XP_REWARD
    
    # Level check
    current_xp = data["xp_levels"][str(uid)]
    if current_xp % LEVEL_UP_XP_THRESHOLD == 0:
        data["tadbucks_balances"][str(uid)] = int(data["tadbucks_balances"].get(str(uid), data["settings"].get("starting_balance", STARTING_BALANCE))) + LEVEL_REWARD_TADBUCKS
        data["tadzzy_points"][str(uid)] = int(data["tadzzy_points"].get(str(uid), 0)) + LEVEL_REWARD_TADZZY
        try:
            await message.channel.send(
                f"🎉 {message.author.mention} leveled up! You received {LEVEL_REWARD_TADZZY} Tadzzy Points and ${LEVEL_REWARD_TADBUCKS} Tadbucks."
            )
        except Exception:
            pass

    # Guess game listener
    key = str(message.author.id)
    if key in active_guess_games:
        answer = active_guess_games[key]["answer"]
        if message.content.lower().strip() == answer.lower():
            await message.channel.send(f"🎉 Correct {message.author.mention}! The player was **{answer}**.")
            del active_guess_games[key]

    # Random auction spawn
    if random.random() < 0.01:  # 1% chance per message
        rarity_weights = {
            "Common": 0.6,
            "Epic": 0.25,
            "Legendary": 0.1,
            "Mythic": 0.04,
            "Secret": 0.01
        }
        rarities = list(rarity_weights.keys())
        weights = list(rarity_weights.values())
        chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]

        available_cards = [f for f in footballers if f["rarity"] == chosen_rarity]
        if available_cards:
            card = random.choice(available_cards)
            await message.channel.send(
                f"🏆 A wild **{card['rarity']} {card['name']}** has appeared for auction!\n"
                f"Starting bid: 💰 {card['price']} coins\n"
                f"Use `!bid {card['name']} <amount>` to join the auction!"
            )

    await bot.process_commands(message)

# -----------------------------
# Enhanced Help Commands with Clean Sections
# -----------------------------
@bot.command(name="help")
async def help_command(ctx: commands.Context):
    embed = discord.Embed(
        title="🤖 Tadzzy Bot — Command Center", 
        description="Your ultimate Discord bot companion! Use `!` prefix for all commands.",
        color=0x5865F2
    )
    
    # Economy & Shop Section
    embed.add_field(
        name="💰 **Economy & Shop**",
        value=(
            "`!shop` - Browse the player shop\n"
            "`!buy <player>` - Purchase a player card\n"
            "`!sell <player>` - Sell your player card\n"
            "`!checkbalance` - View your Tadbucks\n"
            "`!collection` - View your cards\n"
            "`!leaderboard` - Top Tadbucks players"
        ),
        inline=False
    )
    
    # Trading & Auctions Section  
    embed.add_field(
        name="🔄 **Trading & Auctions**",
        value=(
            "`!trade @user <card_index>` - Trade with another player\n"
            "`!accepttrade <trade_id>` - Accept a trade offer\n"
            "`!spawnauction <player>` - Start an auction\n"
            "`!bid <player> <amount>` - Bid on auctions\n"
            "`!closeauction <player>` - Close auction (admin)"
        ),
        inline=False
    )
    
    # Income & Progress Section
    embed.add_field(
        name="📈 **Income & Progress**",
        value=(
            "`!passiveincome` - Check last income payout\n"
            "`!income total` - View total earnings\n"
            "`!messagesleft` - XP needed for next level\n"
            "`!points_leaderboard` - Top Tadzzy Points"
        ),
        inline=False
    )
    
    # Games & Fun Section
    embed.add_field(
        name="🎮 **Games & Fun**",
        value=(
            "`!gamble <amount>` - Risk it all! (24h cooldown)\n"
            "`!fairgamble <amount>` - 50/50 bet (level 50+)\n"
            "`!guesstheplayer[easy/hard/extreme]` - Trivia games\n"
            "`!rps <choice>` - Rock Paper Scissors\n"
            "`!coinflip` - Flip a coin"
        ),
        inline=False
    )
    
    # Utility Section
    embed.add_field(
        name="🛠️ **Utility & Info**",
        value=(
            "`!ping` - Check bot latency\n"
            "`!allplayers` - Browse all available players\n"
            "`!gamenight` - View game night links\n"
            "`!adminhelp` - Admin commands (admins only)"
        ),
        inline=False
    )
    
    embed.set_footer(
        text="💡 Tip: Cards generate passive income every 30 minutes! Rarer cards = more money!",
        icon_url=bot.user.avatar.url if bot.user.avatar else None
    )
    
    await ctx.send(embed=embed)

# -----------------------------
# Enhanced Admin Help
# -----------------------------
@commands.has_permissions(administrator=True)
@bot.command()
async def adminhelp(ctx: commands.Context):
    embed = discord.Embed(
        title="🛡️ Admin Command Center", 
        description="Powerful tools for server administrators",
        color=0xff0000
    )
    
    # Moderation Section
    embed.add_field(
        name="🔨 **Moderation**",
        value=(
            "`!kick @user [reason]` - Kick a member\n"
            "`!ban @user [reason]` - Ban a member\n"
            "`!timeout @user <seconds>` - Timeout user\n"
            "`!clear <count>` - Delete messages\n"
            "`!mute @user <minutes>` - Mute member\n"
            "`!warn @user <reason>` - Warn a user"
        ),
        inline=False
    )
    
    # Economy Management
    embed.add_field(
        name="💎 **Economy Management**",
        value=(
            "`!givetadbucks @user <amount>` - Give Tadbucks\n"
            "`!removetadbucks @user <amount>` - Remove Tadbucks\n"
            "`!givetadzzypoints @user <amount>` - Give points\n"
            "`!giveplayer @user <player>` - Give player card\n"
            "`!resetbalance @user` - Reset user balance"
        ),
        inline=False
    )
    
    # System Administration  
    embed.add_field(
        name="⚙️ **System Administration**",
        value=(
            "`!save` - Manually save data\n"
            "`!load` - Reload data from disk\n"
            "`!backup` - Create data backup\n"
            "`!broadcast <message>` - Send to all members\n"
            "`!say <message>` - Make bot speak"
        ),
        inline=False
    )
    
    embed.set_footer(text="⚠️ Use admin commands responsibly!")
    await ctx.send(embed=embed)

# -----------------------------
# Enhanced Shop System
# -----------------------------
@bot.command()
async def shop(ctx: commands.Context, rarity: str = None):
    """Browse the player shop with optional rarity filter"""
    if rarity:
        rarity = rarity.title()
        available_cards = [f for f in footballers if f["rarity"] == rarity]
        if not available_cards:
            return await ctx.send(f"No players found with rarity '{rarity}'. Available rarities: Common, Epic, Legendary, Mythic, Expensive, Secret")
    else:
        available_cards = footballers
    
    # Sort by price for better organization
    available_cards.sort(key=lambda x: x["price"], reverse=True)
    
    pages = []
    per_page = 8
    
    for i in range(0, len(available_cards), per_page):
        embed = discord.Embed(
            title=f"🏪 Tadzzy Card Shop{f' - {rarity} Cards' if rarity else ''}",
            description="Use `!buy <player>` to purchase a card!",
            color=0x00ff00
        )
        
        for card in available_cards[i:i+per_page]:
            income_info = f"💰 {card.get('income_rate', 1)}/30min"
            embed.add_field(
                name=f"{card['name']} ({card['rarity']})",
                value=f"Price: ${card['price']:,}\nIncome: {income_info}",
                inline=True
            )
        
        embed.set_footer(text=f"Page {i//per_page + 1}/{(len(available_cards)-1)//per_page + 1} | Tip: Higher rarity = more income!")
        pages.append(embed)
    
    await paged_embed_navigation(ctx, pages)

@bot.command()
async def buy(ctx: commands.Context, *, player_name: str):
    """Purchase a player card from the shop"""
    ensure_user_exists(ctx.author.id)
    
    card = find_player_card_by_name(player_name)
    if not card:
        return await ctx.send("❌ Player not found in shop. Use `!shop` to browse available players.")
    
    user_balance = get_balance(ctx.author.id)
    card_price = card["price"]
    
    if user_balance < card_price:
        return await ctx.send(f"❌ Insufficient funds! You have ${user_balance:,} but {card['name']} costs ${card_price:,}")
    
    # Check if user already owns this card
    uid = str(ctx.author.id)
    user_collection = data["user_collections"].get(uid, [])
    if any(c["name"] == card["name"] for c in user_collection):
        return await ctx.send(f"❌ You already own **{card['name']}**!")
    
    # Check collection space
    if len(user_collection) >= MAX_COLLECTION_SLOTS:
        return await ctx.send(f"❌ Your collection is full! ({MAX_COLLECTION_SLOTS}/{MAX_COLLECTION_SLOTS})")
    
    # Process purchase
    set_balance(ctx.author.id, user_balance - card_price)
    data["user_collections"][uid].append(card.copy())
    
    embed = discord.Embed(
        title="🎉 Purchase Successful!",
        description=f"You bought **{card['name']}** for ${card_price:,}!",
        color=card["color"]
    )
    embed.add_field(name="Remaining Balance", value=f"${get_balance(ctx.author.id):,}", inline=True)
    embed.add_field(name="Passive Income", value=f"💰 {card.get('income_rate', 1)} every 30 minutes", inline=True)
    embed.add_field(name="Collection", value=f"{len(user_collection)+1}/{MAX_COLLECTION_SLOTS}", inline=True)
    
    await ctx.send(embed=embed)

# -----------------------------
# Enhanced Trading System
# -----------------------------
@bot.command()
async def trade(ctx: commands.Context, target: discord.Member, card_index: int):
    """Initiate a trade with another player"""
    if ctx.author.id == target.id:
        await ctx.send("❌ You cannot trade with yourself!")
        return

    ensure_user_exists(ctx.author.id)
    ensure_user_exists(target.id)
    
    sender_coll = data["user_collections"].get(str(ctx.author.id), [])
    target_coll = data["user_collections"].get(str(target.id), [])

    if card_index < 1 or card_index > len(sender_coll):
        await ctx.send(f"❌ Invalid card number. You have {len(sender_coll)} cards. Use `!collection` to see them.")
        return

    item_to_trade = sender_coll[card_index - 1]
    trade_id = f"{ctx.author.id}_{target.id}_{int(datetime.utcnow().timestamp())}"
    
    # Store trade info
    pending_trades[trade_id] = {
        "sender": ctx.author.id,
        "recipient": target.id,
        "card": item_to_trade,
        "card_index": card_index - 1,
        "status": "pending",
        "timestamp": datetime.utcnow().isoformat()
    }

    embed = discord.Embed(
        title="🔄 Trade Offer",
        description=f"{target.mention}, {ctx.author.mention} wants to trade with you!",
        color=0xff9900
    )
    embed.add_field(
        name="Offered Card",
        value=f"**{item_to_trade['name']}** ({item_to_trade['rarity']})\nValue: ${item_to_trade['price']:,}\nIncome: 💰{item_to_trade.get('income_rate', 1)}/30min",
        inline=False
    )
    embed.add_field(
        name="How to Respond",
        value=f"`!accepttrade {trade_id}` - Accept the trade\n`!declinetrade {trade_id}` - Decline the trade",
        inline=False
    )
    embed.set_footer(text=f"Trade ID: {trade_id} | Expires in 5 minutes")

    await ctx.send(embed=embed)
    
    # Auto-expire trade after 5 minutes
    await asyncio.sleep(300)  # 5 minutes
    if trade_id in pending_trades and pending_trades[trade_id]["status"] == "pending":
        del pending_trades[trade_id]

@bot.command()
async def accepttrade(ctx: commands.Context, trade_id: str):
    """Accept a trade offer"""
    if trade_id not in pending_trades:
        return await ctx.send("❌ Trade not found or expired.")
    
    trade = pending_trades[trade_id]
    if trade["recipient"] != ctx.author.id:
        return await ctx.send("❌ This trade is not for you.")
    
    if trade["status"] != "pending":
        return await ctx.send("❌ This trade is no longer available.")
    
    sender_id = str(trade["sender"])
    recipient_id = str(trade["recipient"])
    
    sender_coll = data["user_collections"].get(sender_id, [])
    recipient_coll = data["user_collections"].get(recipient_id, [])
    
    # Check if recipient has space
    if len(recipient_coll) >= MAX_COLLECTION_SLOTS:
        await ctx.send("❌ Your collection is full! Cannot accept trade.")
        del pending_trades[trade_id]
        return
    
    # Check if sender still has the card
    if trade["card_index"] >= len(sender_coll) or sender_coll[trade["card_index"]]["name"] != trade["card"]["name"]:
        await ctx.send("❌ The sender no longer has this card.")
        del pending_trades[trade_id]
        return
    
    # Execute trade
    card = sender_coll.pop(trade["card_index"])
    recipient_coll.append(card)
    
    trade["status"] = "completed"
    
    embed = discord.Embed(
        title="✅ Trade Completed!",
        description=f"Trade between <@{sender_id}> and <@{recipient_id}> successful!",
        color=0x00ff00
    )
    embed.add_field(
        name="Traded Card",
        value=f"**{card['name']}** ({card['rarity']})\nValue: ${card['price']:,}",
        inline=False
    )
    
    await ctx.send(embed=embed)
    del pending_trades[trade_id]

@bot.command()
async def declinetrade(ctx: commands.Context, trade_id: str):
    """Decline a trade offer"""
    if trade_id not in pending_trades:
        return await ctx.send("❌ Trade not found.")
    
    trade = pending_trades[trade_id]
    if trade["recipient"] != ctx.author.id:
        return await ctx.send("❌ This trade is not for you.")
    
    await ctx.send(f"❌ <@{ctx.author.id}> declined the trade offer.")
    del pending_trades[trade_id]

# -----------------------------
# Enhanced Selling System  
# -----------------------------
@bot.command()
async def sell(ctx: commands.Context, *, player_name: str):
    """Sell a player card with dynamic pricing"""
    uid = str(ctx.author.id)
    ensure_user_exists(ctx.author.id)
    coll = data["user_collections"].get(uid, [])
    
    # Find the card (case-insensitive)
    card = next((c for c in coll if normalize_name(c["name"]) == normalize_name(player_name)), None)
    if not card:
        return await ctx.send("❌ You don't own this card. Use `!collection` to see your cards.")
    
    # Dynamic pricing based on rarity
    base_price = card["price"]
    rarity_multipliers = {
        "Secret": 0.8,      # 80% of original price
        "Mythic": 0.7,      # 70% of original price  
        "Legendary": 0.6,   # 60% of original price
        "Epic": 0.55,       # 55% of original price
        "Expensive": 0.75,  # 75% of original price
        "Common": 0.4       # 40% of original price
    }
    
    multiplier = rarity_multipliers.get(card["rarity"], 0.5)
    sell_price = int(base_price * multiplier)
    
    # Confirmation embed
    embed = discord.Embed(
        title="💸 Sell Confirmation",
        description=f"Are you sure you want to sell **{card['name']}**?",
        color=0xff9900
    )
    embed.add_field(name="Original Price", value=f"${base_price:,}", inline=True)
    embed.add_field(name="Sell Price", value=f"${sell_price:,}", inline=True)
    embed.add_field(name="Lost Income", value=f"💰{card.get('income_rate', 1)}/30min", inline=True)
    embed.set_footer(text="React with ✅ to confirm or ❌ to cancel")
    
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    
    def check(reaction, user):
        return user == ctx.author and reaction.message.id == msg.id and str(reaction.emoji) in ["✅", "❌"]
    
    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check)
        
        if str(reaction.emoji) == "✅":
            # Process sale
            coll.remove(card)
            current_balance = get_balance(ctx.author.id)
            set_balance(ctx.author.id, current_balance + sell_price)
            
            success_embed = discord.Embed(
                title="✅ Sale Completed!",
                description=f"You sold **{card['name']}** for ${sell_price:,}!",
                color=0x00ff00
            )
            success_embed.add_field(name="New Balance", value=f"${get_balance(ctx.author.id):,}", inline=True)
            success_embed.add_field(name="Cards Remaining", value=f"{len(coll)}/{MAX_COLLECTION_SLOTS}", inline=True)
            
            await msg.edit(embed=success_embed)
            await msg.clear_reactions()
            
        else:
            await msg.edit(content="❌ Sale cancelled.", embed=None)
            await msg.clear_reactions()
            
    except asyncio.TimeoutError:
        await msg.edit(content="⏰ Sale timed out.", embed=None)
        await msg.clear_reactions()

# -----------------------------
# Moderation commands
# -----------------------------
@commands.has_permissions(kick_members=True)
@bot.command()
async def kick(ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None):
    try:
        await member.kick(reason=reason)
        await ctx.send(f"👢 Kicked {member.mention}. Reason: {reason or 'No reason specified'}")
    except Exception as e:
        await ctx.send(f"Failed to kick: {e}")

@commands.has_permissions(ban_members=True)
@bot.command()
async def ban(ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"🔨 Banned {member.mention}. Reason: {reason or 'No reason specified'}")
    except Exception as e:
        await ctx.send(f"Failed to ban: {e}")

@commands.has_permissions(moderate_members=True)
@bot.command()
async def timeout(ctx: commands.Context, member: discord.Member, seconds: int, *, reason: Optional[str] = None):
    try:
        until = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        await member.timeout(until, reason=reason)
        await ctx.send(f"⏳ Timed out {member.mention} for {seconds}s.")
    except Exception as e:
        await ctx.send(f"Failed to timeout: {e}")

@commands.has_permissions(manage_messages=True)
@bot.command(aliases=["purge"])
async def clear(ctx: commands.Context, count: int):
    try:
        deleted = await ctx.channel.purge(limit=count + 1)
        await ctx.send(f"🧹 Deleted {len(deleted)-1} messages.", delete_after=3.0)
    except Exception as e:
        await ctx.send(f"Failed to purge messages: {e}")

@commands.has_permissions(moderate_members=True)
@bot.command()
async def mute(ctx: commands.Context, member: discord.Member, minutes: int = 10):
    try:
        until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        await member.timeout(until, reason="Muted by command")
        await ctx.send(f"🔇 Muted {member.mention} for {minutes} minutes.")
    except Exception as e:
        await ctx.send(f"Failed to mute: {e}")

@commands.has_permissions(moderate_members=True)
@bot.command()
async def unmute(ctx: commands.Context, member: discord.Member):
    try:
        await member.timeout(None)
        await ctx.send(f"🔊 Unmuted {member.mention}.")
    except Exception as e:
        await ctx.send(f"Failed to unmute: {e}")

@commands.has_permissions(manage_messages=True)
@bot.command()
async def warn(ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None):
    await ctx.send(f"⚠️ {member.mention} was warned. Reason: {reason or 'No reason provided'}")

@commands.has_permissions(manage_guild=True)
@bot.command()
async def slowmode(ctx: commands.Context, seconds: int):
    try:
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"⏱️ Channel slowmode set to {seconds} seconds.")
    except Exception as e:
        await ctx.send(f"Failed to set slowmode: {e}")

@commands.has_permissions(manage_nicknames=True)
@bot.command()
async def nick(ctx: commands.Context, member: discord.Member, *, newname: str):
    try:
        await member.edit(nick=newname)
        await ctx.send(f"✏️ Changed nickname for {member.mention} to {newname}.")
    except Exception as e:
        await ctx.send(f"Failed to change nickname: {e}")

# -----------------------------
# Admin commands
# -----------------------------
@commands.has_permissions(administrator=True)
@bot.command()
async def givetadzzypoints(ctx: commands.Context, member: discord.Member, amount: int):
    ensure_user_exists(member.id)
    data["tadzzy_points"][str(member.id)] = int(data["tadzzy_points"].get(str(member.id), 0)) + amount
    await ctx.send(f"✅ Gave {amount} Tadzzy Points to {member.mention}.")

@commands.has_permissions(administrator=True)
@bot.command()
async def removetadzzypoints(ctx: commands.Context, member: discord.Member, amount: int):
    ensure_user_exists(member.id)
    data["tadzzy_points"][str(member.id)] = max(0, int(data["tadzzy_points"].get(str(member.id), 0)) - amount)
    await ctx.send(f"✅ Removed {amount} Tadzzy Points from {member.mention}.")

@commands.has_permissions(administrator=True)
@bot.command()
async def givetadbucks(ctx: commands.Context, member: discord.Member, amount: int):
    ensure_user_exists(member.id)
    data["tadbucks_balances"][str(member.id)] = int(data["tadbucks_balances"].get(str(member.id), STARTING_BALANCE)) + amount
    await ctx.send(f"✅ Gave ${amount} Tadbucks to {member.mention}.")

@commands.has_permissions(administrator=True)
@bot.command()
async def removetadbucks(ctx: commands.Context, member: discord.Member, amount: int):
    ensure_user_exists(member.id)
    data["tadbucks_balances"][str(member.id)] = max(0, int(data["tadbucks_balances"].get(str(member.id), STARTING_BALANCE)) - amount)
    await ctx.send(f"✅ Removed ${amount} Tadbucks from {member.mention}.")

@commands.has_permissions(administrator=True)
@bot.command()
async def giveplayer(ctx: commands.Context, member: discord.Member, *, player_name: str):
    ensure_user_exists(member.id)
    card = find_player_card_by_name(player_name)
    if not card:
        return await ctx.send("Player not found.")
    if len(data["user_collections"][str(member.id)]) >= MAX_COLLECTION_SLOTS:
        return await ctx.send("User's collection is full.")
    data["user_collections"][str(member.id)].append(card)
    await ctx.send(f"✅ Gave {member.mention} the player card **{card['name']}**.")

@commands.has_permissions(administrator=True)
@bot.command()
async def removeplayer(ctx: commands.Context, member: discord.Member, *, player_name: str):
    ensure_user_exists(member.id)
    coll = data["user_collections"].get(str(member.id), [])
    card = next((c for c in coll if normalize_name(c["name"]) == normalize_name(player_name)), None)
    if not card:
        return await ctx.send("User does not own that player.")
    coll.remove(card)
    await ctx.send(f"✅ Removed {card['name']} from {member.mention}'s collection.")

@commands.has_permissions(administrator=True)
@bot.command()
async def addlevel(ctx: commands.Context, member: discord.Member, amount: int):
    ensure_user_exists(member.id)
    data["xp_levels"][str(member.id)] = int(data["xp_levels"].get(str(member.id), 0)) + amount
    await ctx.send(f"✅ Added {amount} XP to {member.mention}.")

@commands.has_permissions(administrator=True)
@bot.command()
async def removelevel(ctx: commands.Context, member: discord.Member, amount: int):
    ensure_user_exists(member.id)
    data["xp_levels"][str(member.id)] = max(0, int(data["xp_levels"].get(str(member.id), 0)) - amount)
    await ctx.send(f"✅ Removed {amount} XP from {member.mention}.")

@commands.has_permissions(administrator=True)
@bot.command()
async def resetbalance(ctx: commands.Context, member: discord.Member):
    data["tadbucks_balances"][str(member.id)] = data["settings"].get("starting_balance", STARTING_BALANCE)
    await ctx.send(f"✅ Reset {member.mention}'s balance to ${data['tadbucks_balances'][str(member.id)]}.")

@commands.has_permissions(administrator=True)
@bot.command()
async def forcecloseauction(ctx: commands.Context, *, player_name: str):
    card = find_player_card_by_name(player_name)
    if not card:
        return await ctx.send("Player not found.")
    pname = card["name"]
    if pname not in data["auctions"] or not data["auctions"][pname].get("active", False):
        return await ctx.send("No active auction for that player.")
    auction = data["auctions"][pname]
    highest_bidder = auction.get("highest_bidder")
    highest_bid = int(auction.get("highest_bid", 0))
    auction["active"] = False
    if highest_bidder:
        ensure_user_exists(int(highest_bidder))
        if int(data["tadbucks_balances"].get(str(highest_bidder), STARTING_BALANCE)) >= highest_bid:
            data["tadbucks_balances"][str(highest_bidder)] -= highest_bid
            data["user_collections"].setdefault(str(highest_bidder), [])
            if len(data["user_collections"][str(highest_bidder)]) < MAX_COLLECTION_SLOTS:
                data["user_collections"][str(highest_bidder)].append(card)
                await ctx.send(f"🎉 Auction force-closed. <@{highest_bidder}> wins {pname} for ${highest_bid}.")
                return
    await ctx.send("Auction force-closed. No valid winner or failed to deliver card.")

@commands.has_permissions(administrator=True)
@bot.command()
async def broadcast(ctx: commands.Context, *, message: str):
    sent = 0
    failed = 0
    for member in ctx.guild.members:
        if member.bot:
            continue
        try:
            await member.send(f"[Broadcast from {ctx.guild.name}] {message}")
            sent += 1
        except Exception:
            failed += 1
    await ctx.send(f"Broadcast sent to {sent} members, failed for {failed} members.")

@commands.has_permissions(administrator=True)
@bot.command()
async def save(ctx: commands.Context):
    ok = save_data()
    await ctx.send("Saved data." if ok else "Save failed.")

@commands.has_permissions(administrator=True)
@bot.command()
async def load(ctx: commands.Context):
    load_data()
    await ctx.send("Loaded data (from disk).")

@commands.has_permissions(administrator=True)
@bot.command()
async def backup(ctx: commands.Context):
    if not os.path.exists(DATA_FILE):
        return await ctx.send("No data file to backup.")
    dest = backup_data()
    if dest:
        await ctx.send(f"Backup created: `{dest}`")
    else:
        await ctx.send("Backup failed.")

@commands.has_permissions(administrator=True)
@bot.command()
async def say(ctx: commands.Context, *, message: str):
    await ctx.send(message)

# -----------------------------
# Fun Commands
# -----------------------------
@bot.command()
async def ping(ctx: commands.Context):
    await ctx.send(f"🏓 Pong! {round(bot.latency*1000)}ms")

@bot.command()
async def rps(ctx: commands.Context, choice: str):
    choice = choice.lower()
    options = ["rock", "paper", "scissors"]
    if choice not in options:
        return await ctx.send("Choose rock, paper, or scissors.")
    bot_choice = random.choice(options)
    outcome = "Tie!" if bot_choice == choice else "You win!" if (choice, bot_choice) in [
        ("rock", "scissors"), ("paper", "rock"), ("scissors", "paper")
    ] else "I win!"
    await ctx.send(f"You: {choice} | Bot: {bot_choice} → {outcome}")

@bot.command()
async def coinflip(ctx: commands.Context):
    await ctx.send(f"🪙 {'Heads' if random.random() < 0.5 else 'Tails'}")

@bot.command()
async def dice(ctx: commands.Context, sides: int = 6):
    if sides < 2 or sides > 1000:
        return await ctx.send("Sides must be between 2 and 1000.")
    await ctx.send(f"🎲 You rolled a {random.randint(1, sides)} (1-{sides})")

@bot.command()
async def meme(ctx: commands.Context):
    memes = [
        "https://i.imgur.com/w3duR07.png",
        "https://i.imgur.com/2JX6KQm.jpg",
        "https://i.imgur.com/5fXbG4Z.jpg"
    ]
    await ctx.send(random.choice(memes))

@bot.command()
async def compliment(ctx: commands.Context, member: Optional[discord.Member] = None):
    member = member or ctx.author
    compliments = [
        "You're an awesome friend!",
        "Your positivity is infectious.",
        "You light up the room!"
    ]
    await ctx.send(f"{member.mention}, {random.choice(compliments)}")

@bot.command()
async def trivia(ctx: commands.Context):
    questions = [
        ("What is the capital of France?", "paris"),
        ("Which planet is known as the Red Planet?", "mars"),
        ("What programming language is this bot written in?", "python")
    ]
    q, a = random.choice(questions)
    await ctx.send(q)

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        reply = await bot.wait_for("message", check=check, timeout=20.0)
        if reply.content.lower().strip() == a:
            await ctx.send("✅ Correct!")
        else:
            await ctx.send(f"❌ Wrong — the answer was **{a}**.")
    except asyncio.TimeoutError:
        await ctx.send(f"⏳ Time's up! The answer was **{a}**.")

@bot.command()
async def dadjoke(ctx: commands.Context):
    jokes = [
        "I would tell you a construction pun, but I'm still working on it.",
        "Why don't skeletons fight each other? They don't have the guts.",
        "I used to play piano by ear, but now I use my hands."
    ]
    await ctx.send(random.choice(jokes))

@bot.command(name="8ball")
async def eight_ball(ctx: commands.Context, *, question: str):
    answers = [
        "It is certain.", "Without a doubt.", "Ask again later.", "My reply is no.",
        "Very doubtful.", "Signs point to yes.", "Better not tell you now."
    ]
    await ctx.send(f"🎱 {random.choice(answers)}")

@bot.command()
async def deadp00l295(ctx):
    if ctx.author.id != 724928981450752021:
        await ctx.send("❌ You're not authorized to use this command.")
        return

    responses = [
        "67676767676767",
        "URO THE GOAT IS HERE",
        "DEADPOOL HAS A BIG WOODINI"
    ]
    await ctx.send(random.choice(responses))

@bot.command()
async def var(ctx):
    punishments = [
        "Red card 🚩 – Off you go!",
        "Yellow card 🟨 – Behave yourself!",
        "Warning ⚠️ – You got lucky this time.",
        "VAR is broken, play on! 😂"
    ]
    weights = [0.3, 0.3, 0.3, 0.1]
    choice = random.choices(punishments, weights=weights, k=1)[0]
    await ctx.send(f"VAR Decision: {choice}")

# -----------------------------
# Game Night System
# -----------------------------
@commands.has_permissions(administrator=True)
@bot.command()
async def addgamenight(ctx: commands.Context, link: str):
    if not re.match(r"^https:\/\/www\.roblox\.com\/games\/\d+\/.+", link):
        return await ctx.send("❌ Invalid Roblox link.")
    data["gamenights"].append(link)
    await ctx.send(f"✅ Added gamenight: {link}")

@commands.has_permissions(administrator=True)
@bot.command()
async def gamenightremove(ctx: commands.Context, link: str):
    if link in data["gamenights"]:
        data["gamenights"].remove(link)
        await ctx.send(f"❌ Removed gamenight: {link}")
    else:
        await ctx.send("Link not found.")

@bot.command()
async def gamenight(ctx: commands.Context):
    if not data["gamenights"]:
        return await ctx.send("No gamenights added.")
    embed = discord.Embed(title="Game Nights", color=0x2ecc71)
    for i, g in enumerate(data["gamenights"], 1):
        embed.add_field(name=f"Game {i}", value=g, inline=False)
    await ctx.send(embed=embed)

# -----------------------------
# Guess The Player
# -----------------------------
async def start_guess(ctx: commands.Context, difficulty: str):
    db = data["guess_db"]
    if difficulty not in db or not db[difficulty]:
        return await ctx.send("No clues for that difficulty.")
    q, a = random.choice(db[difficulty])
    active_guess_games[str(ctx.author.id)] = {"difficulty": difficulty, "answer": a}
    await ctx.send(f"⚽ Guess the player! Clue: {q}")

@bot.command()
async def guesstheplayereasy(ctx: commands.Context):
    await start_guess(ctx, "easy")

@bot.command(name="guesstheplayer")
async def guesstheplayer_normal(ctx: commands.Context):
    await start_guess(ctx, "normal")

@bot.command()
async def guesstheplayerhard(ctx: commands.Context):
    await start_guess(ctx, "hard")

@bot.command()
async def guesstheplayerextreme(ctx: commands.Context):
    await start_guess(ctx, "extreme")

# -----------------------------
# Giveaway
# -----------------------------
@commands.has_permissions(administrator=True)
@bot.command()
async def giveawaycreate(ctx: commands.Context, time: int, *, prize: str):
    embed = discord.Embed(title="🎉 Giveaway! 🎉", description=f"Prize: **{prize}**\nReact with 🎉 to enter!", color=0xf1c40f)
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("🎉")
    await asyncio.sleep(time)
    msg = await ctx.channel.fetch_message(msg.id)
    entries = []
    for reaction in msg.reactions:
        if str(reaction.emoji) == "🎉":
            async for u in reaction.users():
                if not u.bot:
                    entries.append(u)
            break
    if not entries:
        return await ctx.send("❌ Nobody entered.")
    winner = random.choice(entries)
    await ctx.send(f"🎊 Congratulations {winner.mention}, you won **{prize}**!")

# -----------------------------
# Economy Commands
# -----------------------------
@bot.command()
async def checkbalance(ctx: commands.Context):
    ensure_user_exists(ctx.author.id)
    bal = get_balance(ctx.author.id)
    await ctx.send(f"💰 {ctx.author.mention}, your balance is **${bal:,} Tadbucks**")

@bot.command(name="Tadbucks")
async def tadbucks_help(ctx: commands.Context):
    embed = discord.Embed(title="💵 Tadbucks System", description="Your guide to the Tadbucks economy!", color=0xf1c40f)
    embed.add_field(name="💰 Earning", value=(
        "• Message XP: Gain XP and level up rewards\n"
        "• Passive Income: Cards generate money every 30min\n"
        "• Gambling: Risk your Tadbucks for potential gains\n"
        "• Trading: Exchange cards with other players"
    ), inline=False)
    embed.add_field(name="🛒 Spending", value=(
        "• `!shop` - Buy player cards from the shop\n"
        "• `!gamble <amount>` - Gamble your Tadbucks\n"
        "• `!bid <player> <amount>` - Bid in auctions"
    ), inline=False)
    embed.add_field(name="📊 Tracking", value=(
        "• `!checkbalance` - View your current balance\n"
        "• `!collection` - See your owned cards\n"
        "• `!leaderboard` - Top Tadbucks players"
    ), inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def gamble(ctx: commands.Context, amount: int):
    uid = str(ctx.author.id)
    ensure_user_exists(ctx.author.id)
    if amount <= 0:
        return await ctx.send("Bet amount must be positive.")
    balance = get_balance(ctx.author.id)
    if amount > balance:
        return await ctx.send("You don't have enough Tadbucks.")
    last = gamble_cooldowns.get(uid)
    now = datetime.utcnow()
    if last:
        last_dt = datetime.fromisoformat(last)
        if now - last_dt < timedelta(hours=24):
            remaining = timedelta(hours=24) - (now - last_dt)
            return await ctx.send(f"You can gamble again in {str(remaining).split('.')[0]}.")
    gamble_cooldowns[uid] = now.isoformat()
    if random.random() < 0.3:
        set_balance(ctx.author.id, balance + amount)
        await ctx.send(f"🎉 You won! You gained ${amount:,}. New balance: ${get_balance(ctx.author.id):,}")
    else:
        set_balance(ctx.author.id, balance - amount)
        await ctx.send(f"💸 You lost ${amount:,}. New balance: ${get_balance(ctx.author.id):,}")

@bot.command()
async def fairgamble(ctx: commands.Context, amount: int):
    uid = str(ctx.author.id)
    ensure_user_exists(ctx.author.id)
    if amount <= 0:
        return await ctx.send("Bet amount must be positive.")
    balance = get_balance(ctx.author.id)
    if amount > balance:
        return await ctx.send("You don't have enough Tadbucks.")
    level = int(data["xp_levels"].get(uid, 0))
    if level < 50:
        return await ctx.send("You need to be at least level 50 for fair gamble.")
    if random.random() < 0.5:
        set_balance(ctx.author.id, balance + amount)
        await ctx.send(f"🎉 50/50! You won ${amount:,}. New balance: ${get_balance(ctx.author.id):,}")
    else:
        set_balance(ctx.author.id, balance - amount)
        await ctx.send(f"💸 50/50! You lost ${amount:,}. New balance: ${get_balance(ctx.author.id):,}")

@bot.command()
async def spawnauction(ctx: commands.Context, *, player_name: str):
    ensure_user_exists(ctx.author.id)
    card = find_player_card_by_name(player_name)
    if not card:
        return await ctx.send("Player does not exist.")
    name = card["name"]
    if name in data["auctions"] and data["auctions"][name].get("active", False):
        return await ctx.send("Auction already active for this player.")
    ends_at = (datetime.utcnow() + timedelta(hours=AUCTION_DEFAULT_DURATION_HOURS)).isoformat()
    data["auctions"][name] = {
        "highest_bid": 0,
        "highest_bidder": None,
        "active": True,
        "created_by": str(ctx.author.id),
        "ends_at": ends_at
    }
    await ctx.send(f"🏆 Auction started for **{name}**! Place bids with `!bid {name} <amount>`.")

@bot.command()
async def bid(ctx: commands.Context, player_name: str, amount: int):
    ensure_user_exists(ctx.author.id)
    card = find_player_card_by_name(player_name)
    if not card:
        return await ctx.send("Player not found.")
    name = card["name"]
    auction = data["auctions"].get(name)
    if not auction or not auction.get("active", False):
        return await ctx.send("No active auction for this player.")
    ends_at = datetime.fromisoformat(auction["ends_at"])
    if datetime.utcnow() > ends_at:
        auction["active"] = False
        return await ctx.send("This auction has already ended.")
    current = int(auction.get("highest_bid", 0))
    if amount <= current:
        return await ctx.send("Bid must be higher than current highest.")
    balance = get_balance(ctx.author.id)
    if amount > balance:
        return await ctx.send("You don't have enough Tadbucks.")
    auction["highest_bid"] = int(amount)
    auction["highest_bidder"] = str(ctx.author.id)
    new_end = max(ends_at, datetime.utcnow() + timedelta(minutes=5))
    auction["ends_at"] = new_end.isoformat()
    await ctx.send(f"{ctx.author.mention} is now the highest bidder for {name} with ${amount:,}!")

@commands.has_permissions(administrator=True)
@bot.command()
async def closeauction(ctx: commands.Context, *, player_name: str):
    card = find_player_card_by_name(player_name)
    if not card:
        return await ctx.send("Player not found.")
    name = card["name"]
    auction = data["auctions"].get(name)
    if not auction or not auction.get("active", False):
        return await ctx.send("No active auction for this player.")
    if auction.get("highest_bidder") is None:
        auction["active"] = False
        return await ctx.send(f"No bids placed for {name}. Auction closed.")
    winner_id = int(auction["highest_bidder"])
    amount = int(auction["highest_bid"])
    ensure_user_exists(winner_id)
    if get_balance(winner_id) < amount:
        auction["active"] = False
        return await ctx.send("Winner doesn't have enough balance anymore. Auction cancelled.")
    set_balance(winner_id, get_balance(winner_id) - amount)
    user_coll = data["user_collections"].setdefault(str(winner_id), [])
    if len(user_coll) >= MAX_COLLECTION_SLOTS:
        auction["active"] = False
        return await ctx.send("Winner has full collection, cannot add player.")
    user_coll.append(card)
    auction["active"] = False
    await ctx.send(f"🎉 <@{winner_id}> won the auction for {name} with ${amount:,}!")

# -----------------------------
# Collection & Allplayers with paging
# -----------------------------
async def paged_embed_navigation(ctx, pages: List[discord.Embed], timeout: int = 60):
    if not pages:
        return
    cur = 0
    message = await ctx.send(embed=pages[cur])
    if len(pages) == 1:
        return
    await message.add_reaction("◀️")
    await message.add_reaction("⏹️")
    await message.add_reaction("▶️")

    def check(reaction, user):
        return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in ["◀️", "▶️", "⏹️"]

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=timeout, check=check)
            emoji = str(reaction.emoji)
            try:
                await message.remove_reaction(reaction, user)
            except Exception:
                pass
            if emoji == "◀️":
                cur = (cur - 1) % len(pages)
                await message.edit(embed=pages[cur])
            elif emoji == "▶️":
                cur = (cur + 1) % len(pages)
                await message.edit(embed=pages[cur])
            elif emoji == "⏹️":
                await message.clear_reactions()
                break
        except asyncio.TimeoutError:
            try:
                await message.clear_reactions()
            except Exception:
                pass
            break

@bot.command()
async def collection(ctx: commands.Context):
    uid = str(ctx.author.id)
    ensure_user_exists(ctx.author.id)
    coll = data["user_collections"].get(uid, [])
    if not coll:
        return await ctx.send("Your collection is empty. Use `!shop` to buy some cards!")
    
    # Sort by rarity and price for better display
    rarity_order = {"Secret": 0, "Expensive": 1, "Mythic": 2, "Legendary": 3, "Epic": 4, "Common": 5}
    coll.sort(key=lambda x: (rarity_order.get(x["rarity"], 6), -x["price"]))
    
    pages = []
    per_page = 6
    for i in range(0, len(coll), per_page):
        embed = discord.Embed(
            title=f"🎴 {ctx.author.display_name}'s Collection", 
            description=f"Total Cards: {len(coll)}/{MAX_COLLECTION_SLOTS}",
            color=0x5865F2
        )
        for idx, card in enumerate(coll[i:i+per_page], i+1):
            embed.add_field(
                name=f"{idx}. {card['name']} ({card['rarity']})",
                value=f"💰 Value: ${card['price']:,}\n📈 Income: {card.get('income_rate', 1)}/30min",
                inline=True
            )
        embed.set_footer(text=f"Page {i//per_page + 1}/{(len(coll)-1)//per_page + 1} | Use card numbers for trading!")
        pages.append(embed)
    await paged_embed_navigation(ctx, pages)

@bot.command()
async def allplayers(ctx: commands.Context):
    pages = []
    per_page = 8
    
    # Sort players by rarity and price
    sorted_players = sorted(footballers, key=lambda x: (x["price"]), reverse=True)
    
    for i in range(0, len(sorted_players), per_page):
        embed = discord.Embed(title="🏪 All Available Players", color=0x5865F2)
        for card in sorted_players[i:i+per_page]:
            embed.add_field(
                name=f"{card['name']} ({card['rarity']})",
                value=f"💰 Price: ${card['price']:,}\n📈 Income: {card.get('income_rate', 1)}/30min",
                inline=True
            )
        embed.set_footer(text=f"Page {i//per_page + 1}/{(len(sorted_players)-1)//per_page + 1} | Use !shop to buy!")
        pages.append(embed)
    await paged_embed_navigation(ctx, pages)

# -----------------------------
# Leaderboards
# -----------------------------
@bot.command()
async def leaderboard(ctx: commands.Context):
    items = sorted(data["tadbucks_balances"].items(), key=lambda x: int(x[1]), reverse=True)[:10]
    embed = discord.Embed(title="💰 Tadbucks Leaderboard", description="Top 10 richest players", color=0xf1c40f)
    for i, (uid, bal) in enumerate(items, 1):
        try:
            user = await bot.fetch_user(int(uid))
            name = user.name if user else f"User {uid}"
        except Exception:
            name = f"User {uid}"
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        embed.add_field(
            name=f"{medal} {name}",
            value=f"${int(bal):,}",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command()
async def points_leaderboard(ctx: commands.Context):
    items = sorted(data["tadzzy_points"].items(), key=lambda x: int(x[1]), reverse=True)[:10]
    embed = discord.Embed(title="🏆 Tadzzy Points Leaderboard", description="Top 10 point holders", color=0x00ff00)
    for i, (uid, pts) in enumerate(items, 1):
        try:
            user = await bot.fetch_user(int(uid))
            name = user.name if user else f"User {uid}"
        except Exception:
            name = f"User {uid}"
            
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        embed.add_field(
            name=f"{medal} {name}",
            value=f"{int(pts):,} pts",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command()
async def collection_status(ctx: commands.Context, member: Optional[discord.Member] = None):
    member = member or ctx.author
    coll = data["user_collections"].get(str(member.id), [])
    await ctx.send(f"📊 {member.display_name} has **{len(coll)}/{MAX_COLLECTION_SLOTS}** cards.")

# -----------------------------
# Enhanced Passive Income Commands
# -----------------------------
@bot.command()
async def passiveincome(ctx):
    user_id = str(ctx.author.id)
    if user_id not in last_income_report:
        await ctx.send(f"💸 {ctx.author.mention}, you haven't received a passive income payout yet!\nCards generate income every **30 minutes** based on their rarity and value.")
    else:
        payout = last_income_report[user_id]
        embed = discord.Embed(
            title="💰 Latest Passive Income Report", 
            color=0x00ff00
        )
        embed.add_field(
            name="Last Payout", 
            value=f"**${payout:,} Tadbucks** 💸", 
            inline=True
        )
        embed.add_field(
            name="Next Payout", 
            value="⏰ Within 30 minutes", 
            inline=True
        )
        embed.set_footer(text="💡 Tip: Rarer cards generate more income!")
        await ctx.send(embed=embed)

@bot.command()
async def income(ctx, arg: str = None):
    user_id = str(ctx.author.id)
    if arg and arg.lower() == "total":
        total = total_income_tracker.get(user_id, 0)
        
        embed = discord.Embed(
            title="📊 Total Income Report",
            description=f"{ctx.author.mention}'s lifetime earnings",
            color=0xf1c40f
        )
        embed.add_field(
            name="Total Passive Income Earned",
            value=f"**${total:,} Tadbucks** 💰",
            inline=False
        )
        
        # Calculate potential income from current collection
        coll = data["user_collections"].get(user_id, [])
        potential_income = sum(card.get("income_rate", 1) for card in coll)
        
        embed.add_field(
            name="Current Collection Income Rate",
            value=f"**${potential_income:,}** every 30 minutes",
            inline=True
        )
        embed.add_field(
            name="Cards Owned",
            value=f"{len(coll)}/{MAX_COLLECTION_SLOTS}",
            inline=True
        )
        
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"📈 {ctx.author.mention}, use `!income total` to see your total lifetime earnings from passive income!")

@bot.command()
async def messagesleft(ctx):
    user_id = str(ctx.author.id)
    ensure_user_exists(ctx.author.id)
    current_xp = data["xp_levels"].get(user_id, 0)
    current_level = current_xp // LEVEL_UP_XP_THRESHOLD
    xp_in_current_level = current_xp % LEVEL_UP_XP_THRESHOLD
    xp_remaining = LEVEL_UP_XP_THRESHOLD - xp_in_current_level
    
    embed = discord.Embed(
        title="📊 Level Progress", 
        color=0x9932cc
    )
    embed.add_field(
        name="Current Level", 
        value=f"**{current_level}**", 
        inline=True
    )
    embed.add_field(
        name="XP to Next Level", 
        value=f"**{xp_remaining}** messages", 
        inline=True
    )
    embed.add_field(
        name="Level Up Rewards", 
        value=f"💰 ${LEVEL_REWARD_TADBUCKS:,}\n🏆 {LEVEL_REWARD_TADZZY} Points", 
        inline=True
    )
    
    await ctx.send(embed=embed)

# -----------------------------
# Error handling
# -----------------------------
@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingPermissions):
        return await ctx.send("❌ You don't have the required permissions to run this command.")
    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send("❌ Missing required argument. Check the command usage.")
    if isinstance(error, commands.BadArgument):
        return await ctx.send("❌ Bad argument. Please check your inputs.")
    print("Unhandled command error:", error)
    await ctx.send(f"An error occurred: {error}")

# -----------------------------
# Graceful shutdown
# -----------------------------
async def close_and_save():
    print("Saving data before shutdown...")
    save_data()
    print("Saved.")

# -----------------------------
# Run bot
# -----------------------------
if __name__ == "__main__":
    try:
        if TOKEN:
            bot.run(TOKEN)
        else:
            print("No token provided. Set DISCORD_TOKEN in your .env file.")
    except KeyboardInterrupt:
        asyncio.get_event_loop().run_until_complete(close_and_save())
        
