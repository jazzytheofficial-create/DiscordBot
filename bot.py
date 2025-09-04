"""
Discord Moderation + Fun Commands Bot (All Commands Async)
Replit-ready: uses keep_alive.py and .env for token
"""

import asyncio
from datetime import datetime, timedelta, timezone
import random
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive

# -----------------------------
# Load token from .env
# -----------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# -----------------------------
# Keep bot alive
# -----------------------------
keep_alive()

# -----------------------------
# Discord Bot Setup
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# -----------------------------
# Events
# -----------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Game(name="type !help"))

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply("Missing argument. Try `!help`. ")
    elif isinstance(error, commands.BadArgument):
        await ctx.reply("Bad argument type. Try `!help`. ")
    else:
        await ctx.reply("Something went wrong. The dev console has details.")
        print("[Command Error]", repr(error))

# -----------------------------
# Help Command
# -----------------------------
@bot.command()
async def help(ctx: commands.Context):
    embed = discord.Embed(title="Bot Commands", description="Prefix: `!`", color=0x5865F2)
    embed.add_field(name="Moderation", value=(
        "`!kick @user [reason]`\n"
        "`!ban @user [reason]`\n"
        "`!unban user_id`\n"
        "`!timeout @user <seconds> [reason]`\n"
        "`!clear <count>`"
    ), inline=False)
    embed.add_field(name="Fun & Utility", value=(
        "`!ping`  `!rps <rock|paper|scissors>`  `!guess`"
    ), inline=False)
    await ctx.send(embed=embed)

# -----------------------------
# Moderation Commands
# -----------------------------
@commands.has_permissions(kick_members=True)
@bot.command()
async def kick(ctx: commands.Context, member: discord.Member, *, reason: str | None = None):
    await member.kick(reason=reason)
    await ctx.reply(f"👢 Kicked {member.mention}. Reason: {reason or 'no reason provided'}")

@commands.has_permissions(ban_members=True)
@bot.command()
async def ban(ctx: commands.Context, member: discord.Member, *, reason: str | None = None):
    await member.ban(reason=reason, delete_message_days=0)
    await ctx.reply(f"🔨 Boomed {member.mention}. Reason: {reason or 'no reason provided'}")

@commands.has_permissions(ban_members=True)
@bot.command()
async def unban(ctx: commands.Context, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)  # type: ignore
    await ctx.reply(f"♻️ Unboomed {user.mention}")

@commands.has_permissions(moderate_members=True)
@bot.command()
async def timeout(ctx: commands.Context, member: discord.Member, seconds: int, *, reason: str | None = None):
    until = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    await member.timeout(until, reason=reason)
    await ctx.reply(f"⏳ Timed out {member.mention} for {seconds}s. Reason: {reason or 'no reason provided'}")

@commands.has_permissions(manage_messages=True)
@bot.command(aliases=["purge"])
async def clear(ctx: commands.Context, count: int):
    if count < 1 or count > 200:
        return await ctx.reply("Choose 1–200 messages.")
    deleted = await ctx.channel.purge(limit=count + 1)
    msg = await ctx.send(f"🧹 Deleted {len(deleted)-1} messages.")
    await asyncio.sleep(2)
    try:
        await msg.delete()
    except Exception:
        pass

# -----------------------------
# Fun Commands / Minigames
# -----------------------------
@bot.command()
async def ping(ctx: commands.Context):
    await ctx.reply(f"🏓 Pong! {round(bot.latency*1000)}ms")

@bot.command()
async def rps(ctx: commands.Context, choice: str):
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

_guess_games: dict[str, int] = {}

@bot.command()
async def guess(ctx: commands.Context):
    key = f"{ctx.channel.id}:{ctx.author.id}"
    if key not in _guess_games:
        _guess_games[key] = random.randint(1, 100)
        await ctx.reply("I picked a number 1–100. Reply with `!try <n>`!")
    else:
        await ctx.reply("Game in progress. Use `!try <n>`. Use `!giveup` to reveal.")

@bot.command(name="try")
async def try_number(ctx: commands.Context, number: int):
    key = f"{ctx.channel.id}:{ctx.author.id}"
    target = _guess_games.get(key)
    if not target:
        return await ctx.reply("Start a game first with `!guess`.")
    if number == target:
        del _guess_games[key]
        await ctx.reply("🎉 Correct! You win.")
    else:
        await ctx.reply("Too low." if number < target else "Too high.")

@bot.command()
async def giveup(ctx: commands.Context):
    key = f"{ctx.channel.id}:{ctx.author.id}"
    target = _guess_games.pop(key, None)
    if target:
        await ctx.reply(f"The number was **{target}**. Play again with `!guess`!")
    else:
        await ctx.reply("No active game. Use `!guess` to start.")

# -----------------------------
# Run the bot
# -----------------------------
if __name__ == "__main__":
    bot.run(TOKEN)
