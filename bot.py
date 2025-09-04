import asyncio
from datetime import datetime, timedelta, timezone
import random
import os
import re

import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive

# -----------------------------
# Load token
# -----------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# -----------------------------
# Keep bot alive
# -----------------------------
keep_alive()

# -----------------------------
# Setup bot
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# -----------------------------
# Storage
# -----------------------------
gamenights: list[str] = []

# Expanded Guess the Player lists
guess_players = {
"easy": [
("He plays for PSG and is from Argentina", "messi"),
("He plays for Al-Nassr and is from Portugal", "ronaldo"),
("He plays for Inter Miami now, also Argentine", "messi"),
("Plays for Manchester United and Portugal", "ronaldo"),
("French superstar at PSG", "mbappe"),
("English midfielder at Manchester City", "de bruyne"),
("English striker at Arsenal", "saliba"),
],
"normal": [
("Egyptian King at Liverpool", "salah"),
("Plays for Spurs and is from South Korea", "son"),
("Belgian midfielder at Man City", "de bruyne"),
("Portuguese striker at Chelsea", "silva"),
("Spanish winger at Real Madrid", "vinicius"),
("German midfielder at Bayern", "gnabry"),
("English defender at Manchester City", "walker"),
],
"hard": [
("Won the Ballon d'Or in 2006, Italian", "cannavaro"),
("Former Brazilian striker, called 'The Phenomenon'", "ronaldo"),
("Dutch winger, retired in 2019, bald head", "robben"),
("Spanish goalkeeper, won the Champions League with Real Madrid", "casillas"),
("Argentine defender at PSG", "diamanti"),
("French midfielder, World Cup 2018 winner", "pogba"),
("Portuguese legend, retired in 2021", "ronaldo"),
],
"extreme": [
("Mexican goalkeeper famous for 2014 World Cup saves", "ochoa"),
("Japanese midfielder, Celtic legend", "nakamura"),
("Played for Wigan, scored FA Cup Final winner in 2013", "ben watson"),
("Italian defender, Juventus legend", "chiellini"),
("Dutch midfielder, World Cup 2010 finalist", "de jong"),
("Argentine goalkeeper, famous for penalty saves", "romero"),
("Brazilian midfielder, retired in 2020", "ronaldinho"),
],
}

active_guess_games: dict[str, tuple[str, str]] = {} # key: user, value: (difficulty, answer)
active_scramble_games: dict[str, tuple[str, str]] = {} # key: user, value: (word, scrambled)

# -----------------------------
# Events
# -----------------------------
@bot.event
async def on_ready():
print(f"✅ Bot is ready! Logged in as {bot.user} (ID: {bot.user.id})")
await bot.change_presence(activity=discord.Game(name="type !help"))

# -----------------------------
# Help
# -----------------------------
@bot.command()
async def help(ctx):
embed = discord.Embed(title="Bot Commands", description="Prefix: `!`", color=0x5865F2)
embed.add_field(name="Moderation", value=(
"`!kick @user [reason]`\n"
"`!ban @user [reason]`\n"
"`!unban user_id`\n"
"`!timeout @user <seconds> [reason]`\n"
"`!clear <count>`"
), inline=False)
embed.add_field(name="Fun & Games", value=(
"`!ping` `!rps <rock|paper|scissors>` `!guess`\n"
"`!guesstheplayereasy` `!guesstheplayer` `!guesstheplayerhard` `!guesstheplayerextreme`\n"
"`!gamenight` `!addgamenight <roblox link>`\n"
"`!giveawaycreate <time in seconds> <prize>`\n"
"`!say <message>`\n"
"`!coinflip` `!dice <sides>` `!8ball <question>` `!compliment <user>` `!joke`\n"
"`!wordscramble` (big game)"
), inline=False)
await ctx.send(embed=embed)

# -----------------------------
# Moderation Commands
# -----------------------------
@commands.has_permissions(kick_members=True)
@bot.command()
async def kick(ctx, member: discord.Member, *, reason=None):
await member.kick(reason=reason)
await ctx.reply(f"👢 Kicked {member.mention}. Reason: {reason or 'no reason provided'}")

@commands.has_permissions(ban_members=True)
@bot.command()
async def ban(ctx, member: discord.Member, *, reason=None):
await member.ban(reason=reason)
await ctx.reply(f"🔨 Boomed {member.mention}. Reason: {reason or 'no reason provided'}")

@commands.has_permissions(ban_members=True)
@bot.command()
async def unban(ctx, user_id: int):
user = await bot.fetch_user(user_id)
await ctx.guild.unban(user)
await ctx.reply(f"♻️ Unboomed {user.mention}")

@commands.has_permissions(moderate_members=True)
@bot.command()
async def timeout(ctx, member: discord.Member, seconds: int, *, reason=None):
until = datetime.now(timezone.utc) + timedelta(seconds=seconds)
await member.timeout(until, reason=reason)
await ctx.reply(f"⏳ Timed out {member.mention} for {seconds}s. Reason: {reason or 'no reason provided'}")

@commands.has_permissions(manage_messages=True)
@bot.command(aliases=["purge"])
async def clear(ctx, count: int):
if count < 1 or count > 200:
return await ctx.reply("Choose 1–200 messages.")
deleted = await ctx.channel.purge(limit=count + 1)
msg = await ctx.send(f"🧹 Deleted {len(deleted)-1} messages.")
await asyncio.sleep(2)
try: await msg.delete()
except: pass

# -----------------------------
# Fun Commands
# -----------------------------
@bot.command()
async def ping(ctx):
await ctx.reply(f"🏓 Pong! {round(bot.latency*1000)}ms")

@bot.command()
async def rps(ctx, choice: str):
choice = choice.lower()
options = ["rock", "paper", "scissors"]
if choice not in options:
return await ctx.reply("Choose rock, paper, or scissors.")
bot_choice = random.choice(options)
outcome = (
"Tie!" if bot_choice == choice else
"You win!" if (choice, bot_choice) in [("rock","scissors"),("paper","rock"),("scissors","paper")] else
"I win!"
)
await ctx.reply(f"You: **{choice}** | Me: **{bot_choice}** → {outcome}")

# -----------------------------
# Game Night System
# -----------------------------
@commands.has_permissions(manage_guild=True)
@bot.command()
async def addgamenight(ctx, link: str):
if not re.match(r"^https:\/\/www\.roblox\.com\/games\/\d+\/.+", link):
return await ctx.reply("❌ Invalid link. Please provide a valid Roblox game link.")
gamenights.append(link)
await ctx.reply(f"✅ Added gamenight: {link}")

@bot.command()
async def gamenight(ctx):
if not gamenights:
return await ctx.reply("No gamenights have been added yet.")
embed = discord.Embed(title="Upcoming Game Nights", color=0x2ecc71)
for i, g in enumerate(gamenights, 1):
embed.add_field(name=f"Game {i}", value=g, inline=False)
await ctx.send(embed=embed)

# -----------------------------
# Guess The Player
# -----------------------------
async def start_guess(ctx, difficulty):
question, answer = random.choice(guess_players[difficulty])
active_guess_games[str(ctx.author.id)] = (difficulty, answer)
await ctx.reply(f"⚽ Guess the player! Clue: {question}")

@bot.command()
async def guesstheplayereasy(ctx): await start_guess(ctx, "easy")
@bot.command(name="guesstheplayer") async def guesstheplayer_normal(ctx): await start_guess(ctx, "normal")
@bot.command() async def guesstheplayerhard(ctx): await start_guess(ctx, "hard")
@bot.command() async def guesstheplayerextreme(ctx): await start_guess(ctx, "extreme")

@bot.listen("on_message")
async def guess_listener(msg):
if msg.author.bot: return
key = str(msg.author.id)
if key in active_guess_games:
difficulty, answer = active_guess_games[key]
if msg.content.lower().strip() == answer.lower():
await msg.channel.send(f"🎉 Correct {msg.author.mention}! The player was **{answer}**.")
del active_guess_games[key]

# -----------------------------
# Giveaway
# -----------------------------
@commands.has_permissions(manage_guild=True)
@bot.command()
async def giveawaycreate(ctx, time: int, *, prize: str):
embed = discord.Embed(title="🎉 Giveaway! 🎉", description=f"Prize: **{prize}**\nReact with 🎉 to enter!", color=0xf1c40f)
msg = await ctx.send(embed=embed)
await msg.add_reaction("🎉")

await asyncio.sleep(time)
msg = await ctx.channel.fetch_message(msg.id)
users = [u for u in await msg.reactions[0].users().flatten() if not u.bot]

if not users:
return await ctx.send("❌ Nobody entered the giveaway.")
winner = random.choice(users)
await ctx.send(f"🎊 Congratulations {winner.mention}, you won **{prize}**!")

# -----------------------------
# Say Command
# -----------------------------
@commands.has_permissions(manage_messages=True)
@bot.command()
async def say(ctx, *, message: str):
await ctx.message.delete()
await ctx.send(message)

# -----------------------------
# New Fun Commands
# -----------------------------
@bot.command()
async def coinflip(ctx):
await ctx.reply(f"🪙 {'Heads' if random.choice([True, False]) else 'Tails'}!")

@bot.command()
async def dice(ctx, sides: int = 6):
if sides < 2: return await ctx.reply("⚠️ Dice must have at least 2 sides.")
await ctx.reply(f"🎲 You rolled a {random.randint(1, sides)} on a {sides}-sided dice.")

@bot.command()
async def _8ball(ctx, *, question: str):
responses = [
"It is certain.", "Very doubtful.", "Ask again later.",
"Definitely yes!", "I have no idea.", "Probably not.",
"Absolutely!", "Maybe.", "Without a doubt."
]
await ctx.reply(f"🎱 Question: {question}\nAnswer: {random.choice(responses)}")

@bot.command()
async def compliment(ctx, member: discord.Member):
compliments = [
"You're awesome!", "You have a great sense of humor!", "You're amazing!",
"You're a legend!", "You light up the server!"
]
await ctx.reply(f"💖 {member.mention}, {random.choice(compliments)}")

@bot.command()
async def joke(ctx):
jokes = [
"Why did the soccer player bring string to the game? To tie the score!",
"Why did the stadium get hot after the game? All the fans left!",
"I told my computer I needed a break, now it won’t stop running!"
]
await ctx.reply(f"😂 {random.choice(jokes)}")

# -----------------------------
# Big Game: Word Scramble
# -----------------------------
WORDS = ["chelsea", "manchester", "barcelona", "liverpool", "psg", "ronaldo", "messi", "pogba", "neymar"]

@bot.command()
async def wordscramble(ctx):
word = random.choice(WORDS)
scrambled = "".join(random.sample(word, len(word)))
active_scramble_games[str(ctx.author.id)] = (word, scrambled)
await ctx.reply(f"🔤 Unscramble this word: **{scrambled}**")

@bot.listen("on_message")
async def scramble_listener(msg):
if msg.author.bot: return
key = str(msg.author.id)
if key in active_scramble_games:
word, scrambled = active_scramble_games[key]
if msg.content.lower().strip() == word.lower():
await msg.channel.send(f"🎉 Correct {msg.author.mention}! The word was **{word}**.")
del active_scramble_games[key]

# -----------------------------
# Run bot
# -----------------------------
if __name__ == "__main__":
bot.run(TOKEN)
