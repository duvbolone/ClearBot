import gc
import os
import re
import sqlite3
import sys
from datetime import datetime

import aiofiles
import aiosqlite
import discord
import requests
from exceptions import UserNotVA, UserVABanned
from discord.ext import commands
from discord.ext.pages import PaginatorButton
from bot import ClearBot, RulesView, VAStartView


bot = ClearBot(intents=discord.Intents.all())


async def get_airports(ctx: discord.AutocompleteContext):
    if ctx.value == "":
        return ["Start typing the name of an airport for results to appear (e.g. KJFK)"]

    value = ctx.value.lower().replace("‘", "'").replace("’", "'")

    return [airport for airport in bot.airports_ac if (value in airport.lower())]


roles = bot.roles

@bot.listen()
async def on_ready():
    os.makedirs("database", exist_ok=True)
    gc.collect()
    if bot.user:
        bot.bot_id = bot.user.id

    bot.add_view(RulesView(bot=bot))
    bot.add_view(VAStartView(bot=bot))

    print(
        """
\033[34m|-----------------------------------------\033[0m
\033[34m| \033[96m  ____ _                 ____        _   \033[0m
\033[34m| \033[96m / ___| | ___  __ _ _ __| __ )  ___ | |_ \033[0m
\033[34m| \033[96m| |   | |/ _ \/ _` | '__|  _ \ / _ \| __|\033[0m
\033[34m| \033[96m| |___| |  __/ (_| | |  | |_) | (_) | |_ \033[0m
\033[34m| \033[96m \____|_|\___|\__,_|_|  |____/ \___/ \__|\033[0m
\033[34m|-----------------------------------------\033[0m"""
    )
    if bot.dev_mode:
        print("| DEV MODE")


@bot.listen()
async def on_application_command_error(
    ctx: discord.ApplicationContext, error: discord.DiscordException
):
    notHandled = True
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(
            title="Take a break!",
            description=error,
            colour=bot.color(1),
        )
        await ctx.respond(embed=embed)
        notHandled = False
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="Missing required permissions",
            description="You're not authorised to use this command!",
            colour=bot.color(1),
        )
        await ctx.respond(embed=embed)
        notHandled = False
    if isinstance(error, UserVABanned):
        embed = discord.Embed(
            title="You're banned from the VA!",
            description="Sadly you were banned from the ClearFly VA. You can't use any VA related commmands.",
            colour=bot.color(1),
        )
        await ctx.respond(embed=embed)
        notHandled = False
    if isinstance(error, UserNotVA):
        embed = discord.Embed(
            title="You're not part of the VA!",
            description=f"Head to <#{bot.channels.get('va-overview')}> to sign-up!",
            colour=bot.color(1),
        )
        await ctx.respond(embed=embed)
        notHandled = False
    if isinstance(error, ValueError):
        embed = discord.Embed(
            title="Incorrect Values",
            description="You gave some values that are incorrect/invalid to me, try again with correct ones!",
            colour=bot.color(1),
        )
        await ctx.respond(embed=embed)
        notHandled = False
    if isinstance(error, commands.MissingRole):
        embed = discord.Embed(
            title="Missing required roles",
            description="You're not authorised to use this command!",
            colour=bot.color(1),
        )
        await ctx.respond(embed=embed)
        notHandled = False
    if isinstance(error, commands.NotOwner):
        embed = discord.Embed(
            title="Owner only command",
            description="This command is for the owner of the bot only, so not for you!",
            colour=bot.color(1),
        )
        await ctx.respond(embed=embed)
        notHandled = False
    if isinstance(error, commands.errors.NoPrivateMessage):
        embed = discord.Embed(
            title="This command cannot be used in DMs.",
            colour=bot.color(1),
        )
        await ctx.respond(embed=embed)
        notHandled = False
    if notHandled:
        bot_author = bot.get_user(bot.bot_author)
        alert_emb = discord.Embed(
            title="Hey there!",
            colour=bot.color(),
            description=f"""
{ctx.author.mention} experienced some issues with me, please fix them as soon as possible! Error is provided below, more info can be found in the terminal.
```py
{error}
```
            """,
        )
        if not bot_author:
            bot_author_id = 0
        else:
            bot_author_id = bot_author.id

        if bot_author_id != ctx.author.id and bot_author:
            await bot_author.send(embed=alert_emb)
            embed = discord.Embed(
                title="Something went wrong...",
                description=f"""
We're sorry for the inconvenience. The bot author has been notified about this issue.
```{error}```
                    """,
                colour=bot.color(1),
            )
        else:
            embed = discord.Embed(
                title="Something went wrong...",
                description=f"""
See the terminal for more information.
```{error}```
                    """,
                colour=bot.color(1),
            )
        await ctx.respond(embed=embed)
        raise error


cogs = os.listdir("cogs")
cogs = [x.split(".")[0] for x in cogs if x.endswith(".py")]

if bot.dev_mode:
    args = sys.argv
    for arg in args:
        if arg.endswith(".py"):
            args.remove(arg)

    for arg in args:
        bot.load_extension(arg)

    bot.run(os.getenv("DEV_TOKEN"))
else:
    for cog in cogs:
        bot.load_extension(f"cogs.{cog}")

    bot.run(os.getenv("TOKEN"))