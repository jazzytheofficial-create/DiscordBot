import asyncio
from datetime import datetime, timedelta, timezone
import random
import os
import re

import discord
from discord.ext import commands
from dotenv import load_dotenv

# -----------------------------
# Load token
# -----------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

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

guess_players = {
    "easy": [
        ("He plays for PSG and is from Argentina", "messi"),
        ("He plays for Al-Nassr and is from Portugal", "ronaldo"),
        ("He plays for Inter Miami now, also Argentine", "messi"),
        ("French midfielder at Real Madrid", "camavinga"),
        ("Norwegian striker at Manchester City", "haaland"),
    ],
    "normal": [
        ("Egyptian King at Liverpool", "salah"),
        ("Plays for Spurs and is from South Korea", "son"),
        ("Belgian midfielder at Man City", "de bruyne"),
        ("English winger at Arsenal", "saka"),
        ("Italian goalkeeper at Juventus", "donnarumma"),
    ],
    "hard": [
        ("Won the Ballon d'Or in 2006, Italian", "cannavaro"),
        ("Former Brazilian striker, called 'The Phenomenon'", "ronaldo"),
        ("Dutch winger, retired in 2019, bald head", "robben"),
        ("Spanish midfielder, played for Barcelona, nickname Xavi", "xavi"),
        ("Argentine striker, played for Napoli", "higuain"),
    ],
    "extreme": [
        ("Mexican goalkeeper famous for 2014 World Cup saves", "ochoa"),
        ("Japanese midfielder, Celtic legend", "nakamura"),
        ("Played for Wigan, scored FA Cup Final winner in 2013", "ben watson"),
        ("Cameroonian striker, retired 2009, played in France", "samuel eto'o"),
        ("German midfielder, won 2014 World Cup", "khedira"),
    ],
}

active_guess_games: dict[str, tuple[str, str]] = {}  # key: user, value: (difficulty, answer)

# -----------------------------
# Events
# -----------------------------
@bot.event
async def on_ready():
    print(f"✅ Bot is ready! Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Game(name="type !help"))

# -----------------------------
# Help Command
# -----------------------------
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Bot Commands", description="Prefix: `!`", color=0x5865F2)
    embed.add_field(name="Moderation", value=(
        "`!kick @user [reason]`\n"
        "`!ban @user [reason]`\n"
        "`!unboomed user_id`\n"
        "`!timeout @user <seconds> [reason]`\n"
        "`!clear <count>`"
    ), inline=False)
    embed.add_field(name="Fun & Games", value=(
        "`!ping`  `!rps <rock|paper|scissors>`  `!guess`\n"
        "`!guesstheplayereasy` `!guesstheplayer` `!guesstheplayerhard` `!guesstheplayerextreme`\n"
        "`!gamenight` `!addgamenight <roblox link>`\n"
        "`!giveawaycreate <time in seconds> <prize>`\n"
        "`!say <message>`"
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
    await ctx.reply(f"🔨 Unbanned {member.mention}. Reason: {reason or 'no reason provided'}")

@commands.has_permissions(ban_members=True)
@bot.command()
async def unboomed(ctx, user_id: int):
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
# Game Night Commands
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
@bot.command(name="guesstheplayer")
async def guesstheplayer_normal(ctx): await start_guess(ctx, "normal")
@bot.command()
async def guesstheplayerhard(ctx): await start_guess(ctx, "hard")
@bot.command()
async def guesstheplayerextreme(ctx): await start_guess(ctx, "extreme")

@bot.listen("on_message")
async def guess_listener(msg):
    if msg.author.bot: return
    key = str(msg.author.id)
    if key not in active_guess_games: return
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
# Run bot
# -----------------------------
if __name__ == "__main__":
    bot.run(TOKEN)

