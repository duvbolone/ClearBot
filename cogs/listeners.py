import asyncio
import re
import aiofiles
import aiohttp
import discord
import os
import random
import aiosqlite
import feedparser
import time
import datetime
from http.client import RemoteDisconnected
from discord.ext import commands, tasks
from bot import ClearBot, DB

class DeleteMsgView(discord.ui.View):
    def __init__(self, bot: ClearBot, auth):
        self.bot = bot
        self.auth = auth
        super().__init__(timeout=240.0, disable_on_timeout=True)

    @discord.ui.button(
        label="Delete Message",
        style=discord.ButtonStyle.danger,
    )
    async def button_callback(self, button, interaction: discord.Interaction):
        if not self.bot.is_interaction_owner(interaction, self.auth.id):
            msg = interaction.message
            if msg:
                await msg.delete()
            else:
                await interaction.response.send_message(
                    "Something went wrong while trying to delete the message.",
                    ephemeral=True,
                )
        else:
            await interaction.response.send_message(
                "You did not send the link, so you can't delete the snippet!",
                ephemeral=True,
            )


class Listeners(discord.Cog):
    def __init__(self, bot: ClearBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.presence.is_running():
            self.presence.start()
        # if not self.rssfeedtres1.is_running() and not self.bot.dev_mode:
        #     self.rssfeedtres1.start()
        # if not self.rssfeedtres2.is_running() and not self.bot.dev_mode:
        #     self.rssfeedtres2.start()
        # if not self.rssfeedtres3.is_running() and not self.bot.dev_mode:
        #     self.rssfeedtres3.start()
        if not self.check_theme.is_running() and not self.bot.dev_mode:
            self.check_theme.start()
        if not self.join_stats_loop.is_running() and not self.bot.dev_mode:
            self.join_stats_loop.start()

        #         channel = self.bot.get_channel(1001405648828891187)
        #         now = discord.utils.format_dt(datetime.datetime.now())
        #         if os.popen("hostname -s").readline() == "raspberrypi\n":
        #             embed = discord.Embed(
        #                 title="I started up!",
        #                 description=f"""
        # Started bot up on {now}

        # *Host is Raspberry Pi*
        #             """,
        #                 color=0x00FF00,
        #             )
        #             await channel.send(embed=embed)
        #         else:
        #             embed = discord.Embed(
        #                 title="I started up!",
        #                 description=f"""
        # Started bot up on {now}

        # *Host is on {platform.system()}*
        #             """,
        #                 color=0x00FF00,
        #             )
        #             await channel.send(embed=embed)
        print(
            "\033[34m|\033[0m \033[96;1mListeners\033[0;36m cog loaded sucessfully\033[0m"
        )

    @tasks.loop(minutes=1)
    async def presence(self):
        guild = self.bot.get_guild(self.bot.server_id)
        if not guild:
            print("\033[31mCould not fetch the ClearFly guild.\033[0m")
            return

        statements = [
            (discord.ActivityType.watching, "ClearFly"),
            (discord.ActivityType.watching, f"{guild.member_count} users"),
            (discord.ActivityType.listening, "ATC"),
            (discord.ActivityType.listening, "ATIS"),
            (discord.ActivityType.watching, "METAR via /aviation airport metar"),
            (
                discord.ActivityType.watching,
                "approach charts via /aviation airport charts",
            ),
            (discord.ActivityType.playing, "X-Plane 10"),
            (discord.ActivityType.playing, "X-Plane 11"),
            (discord.ActivityType.playing, "X-Plane 12"),
            (discord.ActivityType.playing, "Plane Maker"),
            (discord.ActivityType.playing, "Airfoil Maker"),
            (discord.ActivityType.playing, "tuning my radios"),
            (discord.ActivityType.watching, "the ClearFly VA"),
        ]

        statement = random.choice(statements)

        await self.bot.change_presence(
            activity=discord.Activity(type=statement[0], name=statement[1]),
            status=discord.Status.online,
        )

    @tasks.loop(minutes=5)
    async def rssfeedtres1(self):
        table = "RSS_thresholdx_news"
        try:
            channel = self.bot.sendable_channel(
                self.bot.get_channel(self.bot.channels.get("news", 0))
            )
            blog_feed = feedparser.parse("https://www.thresholdx.net/news/rss.xml")
            try:
                feed = dict(blog_feed.entries[0])
            except:
                return
            async with aiosqlite.connect(DB["main"]) as db:
                curs = await db.cursor()
                lastIDs = await curs.execute(f"SELECT lastID FROM {table}")
                lastIDs = await lastIDs.fetchall()
                if lastIDs:
                    lastIDs = [lastID[0] for lastID in lastIDs]
                else:
                    return
            if feed.get("id") in lastIDs:
                return
            else:
                async with aiosqlite.connect(DB["main"]) as db:
                    cursor = await db.cursor()
                    if lastIDs:
                        await cursor.execute(
                            f"UPDATE {table} SET lastID=? WHERE id=1",
                            (feed.get("id"),),
                        )
                        await cursor.execute(
                            f"UPDATE {table} SET lastID=? WHERE id=2",
                            (lastIDs[0],),
                        )
                        await cursor.execute(
                            f"UPDATE {table} SET lastID=? WHERE id=3",
                            (lastIDs[0],),
                        )
                    else:
                        await cursor.execute(
                            f"INSERT INTO {table} (lastID) VALUES (?)",
                            (feed.get("id"),),
                        )
                        await cursor.execute(
                            f"INSERT INTO {table} (lastID) VALUES (?)",
                            ("NULL",),
                        )
                        await cursor.execute(
                            f"INSERT INTO {table} (lastID) VALUES (?)",
                            ("NULL",),
                        )
                    await db.commit()

                if channel:
                    await channel.send(
                        f"""
# {feed.get('title')}

{feed.get('link')}
                    """
                    )
        except Exception as e:
            if isinstance(e, RemoteDisconnected):
                pass
            else:
                raise

    @tasks.loop(minutes=5)
    async def rssfeedtres2(self):
        table = "RSS_thresholdx_opinion"
        try:
            channel = self.bot.sendable_channel(
                self.bot.get_channel(self.bot.channels.get("news", 0))
            )
            blog_feed = feedparser.parse("https://www.thresholdx.net/opinion/rss.xml")
            try:
                feed = dict(blog_feed.entries[0])
            except:
                return
            async with aiosqlite.connect(DB["main"]) as db:
                curs = await db.cursor()
                lastIDs = await curs.execute(f"SELECT lastID FROM {table}")
                lastIDs = await lastIDs.fetchall()
                if lastIDs:
                    lastIDs = [lastID[0] for lastID in lastIDs]
                else:
                    return
            if feed.get("id") in lastIDs:
                return
            else:
                async with aiosqlite.connect(DB["main"]) as db:
                    cursor = await db.cursor()
                    if lastIDs:
                        await cursor.execute(
                            f"UPDATE {table} SET lastID=? WHERE id=1",
                            (feed.get("id"),),
                        )
                        await cursor.execute(
                            f"UPDATE {table} SET lastID=? WHERE id=2",
                            (lastIDs[0],),
                        )
                    else:
                        await cursor.execute(
                            f"INSERT INTO {table} (lastID) VALUES (?)",
                            (feed.get("id"),),
                        )
                        await cursor.execute(
                            f"INSERT INTO {table} (lastID) VALUES (?)",
                            ("NULL",),
                        )
                        await cursor.execute(
                            f"INSERT INTO {table} (lastID) VALUES (?)",
                            ("NULL",),
                        )
                    await db.commit()
                if channel:
                    await channel.send(
                        f"""
# {feed.get('title')}

{feed.get('link')}
                    """
                    )
        except Exception as e:
            if isinstance(e, RemoteDisconnected):
                pass
            else:
                raise

    @tasks.loop(minutes=5)
    async def rssfeedtres3(self):
        table = "RSS_thresholdx_article"
        try:
            channel = self.bot.sendable_channel(
                self.bot.get_channel(self.bot.channels.get("news", 0))
            )
            blog_feed = feedparser.parse("https://www.thresholdx.net/article/rss.xml")
            try:
                feed = dict(blog_feed.entries[0])
            except:
                return
            async with aiosqlite.connect(DB["main"]) as db:
                curs = await db.cursor()
                lastIDs = await curs.execute(f"SELECT lastID FROM {table}")
                lastIDs = await lastIDs.fetchall()
                if lastIDs:
                    lastIDs = [lastID[0] for lastID in lastIDs]
                else:
                    return
            if feed.get("id") in lastIDs:
                return
            else:
                async with aiosqlite.connect(DB["main"]) as db:
                    cursor = await db.cursor()
                    if lastIDs:
                        await cursor.execute(
                            f"UPDATE {table} SET lastID=? WHERE id=1",
                            (feed.get("id"),),
                        )
                        await cursor.execute(
                            f"UPDATE {table} SET lastID=? WHERE id=2",
                            (lastIDs[0],),
                        )
                        await cursor.execute(
                            f"UPDATE {table} SET lastID=? WHERE id=3",
                            (lastIDs[1],),
                        )
                    else:
                        await cursor.execute(
                            f"INSERT INTO {table} (lastID) VALUES (?)",
                            (feed.get("id"),),
                        )
                        await cursor.execute(
                            f"INSERT INTO {table} (lastID) VALUES (?)",
                            ("NULL",),
                        )
                        await cursor.execute(
                            f"INSERT INTO {table} (lastID) VALUES (?)",
                            ("NULL",),
                        )
                    await db.commit()
                if channel:
                    await channel.send(
                        f"""
# {feed.get('title')}

{feed.get('link')}
                    """
                    )
        except Exception as e:
            if isinstance(e, RemoteDisconnected):
                pass
            else:
                raise

    @tasks.loop(hours=12)
    async def check_theme(self):
        now = datetime.datetime.utcnow()

        if now.month == 10 and self.bot.theme != 1:
            result = await self.bot.set_theme("auto-theme", 1)

            failed = ", ".join(result.get("failed_roles", ["N/A"]))  # type: ignore

            embed = discord.Embed(
                title=f"Automatically set theme to **{self.bot.theme_name}**",
                description=f"Failed roles: {failed}",
                color=self.bot.color(),
            )
            channel = self.bot.sendable_channel(
                self.bot.get_channel(self.bot.channels.get("logs", 0))
            )

            if channel:
                await channel.send(embed=embed)
        elif now.month == 12 and self.bot.theme != 2:
            result = await self.bot.set_theme("auto-theme", 2)

            failed = ", ".join(result.get("failed_roles", ["N/A"]))  # type: ignore

            embed = discord.Embed(
                title=f"Automatically set theme to **{self.bot.theme_name}**",
                description=f"Failed roles: {failed}",
                color=self.bot.color(),
            )
            channel = self.bot.sendable_channel(
                self.bot.get_channel(self.bot.channels.get("logs", 0))
            )

            if channel:
                await channel.send(embed=embed)
        elif self.bot.theme != 0 and now.month != 10 and now.month != 12:
            result = await self.bot.set_theme("auto-theme", 0)

            failed = ", ".join(result.get("failed_roles", ["N/A"]))  # type: ignore

            embed = discord.Embed(
                title=f"Automatically set theme to **{self.bot.theme_name}**",
                description=f"Failed roles: {failed}",
                color=self.bot.color(),
            )
            channel = self.bot.sendable_channel(
                self.bot.get_channel(self.bot.channels.get("logs", 0))
            )

            if channel:
                await channel.send(embed=embed)

    @commands.Cog.listener("on_message")
    async def levellisten(self, message):
        if isinstance(message.author, discord.User):
            return
        nowlvlnom = 0
        if message.channel.id == 966077223260004402:
            return
        if message.channel.id == 965600413376200726:
            return
        if message.author.bot:
            return
        else:
            async with aiosqlite.connect(DB["main"]) as db:
                sel = await db.execute("SELECT author_id FROM leveling")
                rows = await sel.fetchall()
                usrs = [row[0] for row in rows]
            if str(message.author.id) in usrs:
                usrdata = None
                async with aiosqlite.connect(DB["main"]) as db:
                    curs = await db.cursor()
                    usrdata = await curs.execute(
                        "SELECT * FROM leveling WHERE author_id=?",
                        (str(message.author.id),),
                    )
                    usrdata = await usrdata.fetchone()
                    if not usrdata:
                        raise ValueError("Couldn't fetch data from database.")

                belvlnom = usrdata[3]
                last = usrdata[5]
                now = round(time.time())
                if (now - int(last)) < 5:
                    return
                else:
                    async with aiosqlite.connect(DB["main"]) as db:
                        cursor = await db.cursor()
                        await cursor.execute(
                            "UPDATE leveling SET last_msg=? WHERE author_id=?",
                            (now, str(message.author.id)),
                        )
                        await db.commit()
                if len(message.content) == 0:
                    nowlvlnom = int(belvlnom) + 1
                if len(message.content) > 0:
                    nowlvlnom = int(belvlnom) + 1
                if len(message.content) > 10:
                    nowlvlnom = int(belvlnom) + 2
                if len(message.content) > 25:
                    nowlvlnom = int(belvlnom) + 5
                if len(message.content) > 50:
                    nowlvlnom = int(belvlnom) + 7
                if len(message.content) > 75:
                    nowlvlnom = int(belvlnom) + 10
                lvl = usrdata[2]
                denom = usrdata[4]
                async with aiosqlite.connect(DB["main"]) as db:
                    cursor = await db.cursor()
                    await cursor.execute(
                        "UPDATE leveling SET nom=? WHERE author_id=?",
                        (nowlvlnom, str(message.author.id)),
                    )
                    await db.commit()
                if int(nowlvlnom) >= int(denom):
                    async with aiosqlite.connect(DB["main"]) as db:
                        cursor = await db.cursor()
                        await cursor.execute(
                            "UPDATE leveling SET nom=0, level=?, denom=? WHERE author_id=?",
                            (
                                lvl + 1,
                                int(denom) + (int(lvl) * 20),
                                str(message.author.id),
                            ),
                        )
                        await db.commit()
                    if int(lvl) == 0:
                        lvl = 1
                    async with aiosqlite.connect(DB["main"]) as db:
                        curs = await db.cursor()
                        usrdata = await curs.execute(
                            "SELECT * FROM leveling WHERE author_id=?",
                            (str(message.author.id),),
                        )
                        usrdata = await usrdata.fetchone()
                        if not usrdata:
                            raise ValueError("Couldn't fetch data from database.")

                    lvlp = usrdata[2]
                    await message.channel.send(
                        f"{message.author.mention} :partying_face: You reached level {lvlp}!"
                    )
            else:
                new_user = {
                    "author_id": str(message.author.id),
                    "level": 0,
                    "nom": 1,
                    "denom": 25,
                    "last_msg": round(time.time()),
                }
                async with aiosqlite.connect(DB["main"]) as db:
                    cur = await db.cursor()
                    await cur.execute(
                        "INSERT INTO leveling (author_id, level, nom, denom, last_msg) VALUES (:author_id, :level, :nom, :denom, :last_msg)",
                        new_user,
                    )
                    await db.commit()

    @tasks.loop(time=datetime.time(hour=19, minute=0))
    async def join_stats_loop(self):
        if (datetime.datetime.now().weekday() == 6) and ():
            async with aiosqlite.connect(DB["main"]) as db:
                await db.execute(
                    "CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY, name TEXT, last INTEGER, now INTEGER)"
                )
                cur = await db.execute("SELECT * FROM stats WHERE name='join'")
                join_stats = await cur.fetchone()
                if not join_stats:
                    raise ValueError("Couldn't fetch data from database.")

                if int(join_stats[2]) == 0:
                    join_pphrase = ""
                else:
                    ma = max(int(join_stats[3]), int(join_stats[2]))
                    mi = min(int(join_stats[3]), int(join_stats[2]))

                    join_perc = abs(round(mi / ma * 100, 2))

                    if int(join_stats[2]) < int(join_stats[3]):
                        join_pphrase = (
                            f"There was a **{join_perc}**% increase in joins!"
                        )
                    elif join_perc == 100:
                        join_pphrase = ""
                    else:
                        join_pphrase = (
                            f"There was a **{join_perc}**% decrease in joins..."
                        )

                embed = discord.Embed(
                    title="Weekly ClearFly Join Report",
                    colour=self.bot.color(),
                    description=f"""
Joins this week: **{join_stats[3]}**
Joins last week: **{join_stats[2]}**
{join_pphrase}
                """,
                )
                channel = self.bot.sendable_channel(
                    self.bot.get_channel(self.bot.channels.get("logs", 0))
                )

                if channel:
                    await channel.send(embed=embed)
                await db.execute(
                    "UPDATE stats SET last = now, now = 0 WHERE name = 'join'"
                )
                await db.commit()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = self.bot.sendable_channel(
            self.bot.get_channel(self.bot.channels.get("arrivals", 0))
        )
        logchannel = self.bot.sendable_channel(
            self.bot.get_channel(self.bot.channels.get("logs", 0))
        )

        emb = discord.Embed(
            title=f"Welcome to ClearFly!",
            description=f"Hey there, {member.mention}! Be sure to read the <#{self.bot.channels.get('info')}> to become a member and gain full access to the server! Thanks for joining!",
            color=self.bot.color(),
        )
        if channel:
            await channel.send(member.mention, embed=emb)
        guild_count = str(member.guild.member_count)
        guild_c_suffix = "th"
        if (
            (guild_count == "12")
            or (guild_count == "13")
            or (guild_count == "14")
            or (guild_count == "15")
            or (guild_count == "16")
            or (guild_count == "17")
            or (guild_count == "18")
            or (guild_count == "19")
        ):
            guild_c_suffix = "th"
        elif guild_count.endswith("1"):
            guild_c_suffix = "st"
        elif guild_count.endswith("2"):
            guild_c_suffix = "nd"
        elif guild_count.endswith("3"):
            guild_c_suffix = "rd"
        else:
            guild_c_suffix = "th"

        emb = discord.Embed(
            title=f"**{member.name}** joined",
            description=f"{member.mention} is the **{guild_count}**{guild_c_suffix} member!",
            color=self.bot.color(),
        ).set_thumbnail(url=member.display_avatar.url)
        async with aiosqlite.connect(DB["main"]) as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY, name TEXT, last INTEGER, now INTEGER)"
            )
            await db.execute(
                "INSERT OR IGNORE INTO stats (name, last, now) VALUES (?, ?, ?)",
                ("join", 0, 0),
            )
            await db.execute("UPDATE stats SET now = now + 1 WHERE name = 'join'")
            await db.commit()

        if logchannel:
            await logchannel.send(embed=emb)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = self.bot.sendable_channel(
            self.bot.get_channel(self.bot.channels.get("logs", 0))
        )
        emb = discord.Embed(
            title=f"{member} left.",
            color=self.bot.color(),
            description=f"Joined on {discord.utils.format_dt(member.joined_at)}",  # type: ignore
        )
        pfp = member.display_avatar.url
        emb.set_thumbnail(url=pfp)
        if channel:
            await channel.send(embed=emb)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if isinstance(message.author, discord.User):
            return

        class ViewRawMessage(discord.ui.View):
            def __init__(self, bot):
                self.bot = bot
                super().__init__(timeout=None)

            @discord.ui.button(
                label="View Raw Contents", style=discord.ButtonStyle.primary
            )
            async def viewRawButtonCallback(self, button, interaction):
                if message.content == "":
                    message.content = "None"
                message.content = message.content.replace("```", "`` `")
                await interaction.response.send_message(
                    f"""
Message Content:
```md
{message.content}
```
                """,
                    ephemeral=True,
                )

        if message.author.bot == False:
            channel = self.bot.sendable_channel(
                self.bot.get_channel(self.bot.channels.get("logs", 0))
            )
            msgcontent = message.clean_content
            if msgcontent == "":
                msgcontent = "None"
            msgatr = message.author.mention
            msgcnl = self.bot.sendable_channel(message.channel)
            if msgcnl:
                msgcnl = msgcnl.mention
            else:
                return
            embs = []
            if message.attachments != []:
                for attach in message.attachments:
                    if not attach.content_type:
                        continue

                    if attach.content_type[:5] == "image":
                        embs.append(
                            discord.Embed(
                                title="Attachment deleted",
                                url=attach.url,
                                colour=self.bot.color(),
                            )
                            .set_image(url=attach.url)
                            .set_footer(
                                text="If the image doesn't load, try opening it in your browser by clicking the title."
                            )
                        )
                    else:
                        embs.append(
                            discord.Embed(
                                title="Attachment deleted",
                                url=attach.url,
                                description="*Attachment is* ***not*** *image*",
                                colour=self.bot.color(),
                            ).set_footer(
                                text="If the image doesn't load, try opening it in your browser by clicking the title."
                            )
                        )
            pfp = message.author.display_avatar.url
            embed = discord.Embed(title="Message Deleted", color=self.bot.color())
            embed.add_field(name="Content", value=f"{msgcontent[:1024]}", inline=False)
            embed.add_field(name="Author", value=f"{msgatr}", inline=True)
            embed.add_field(name="Channel", value=f"{msgcnl}", inline=True)
            embed.add_field(
                name="Other Information",
                value=f"""
Pinned: **{message.pinned}**
Type: **{message.type}**
ID: **{message.id}**
                """,
            )
            embed.set_thumbnail(url=pfp)
            embs.append(embed)
            if channel:
                await channel.send(embeds=embs, view=ViewRawMessage(self.bot))

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if isinstance(before.author, discord.User):
            return

        class ViewRawMessage(discord.ui.View):
            def __init__(self, bot):
                self.bot = bot
                super().__init__(timeout=None)

            @discord.ui.button(
                label="View Raw Contents", style=discord.ButtonStyle.primary
            )
            async def viewRawButtonCallback(self, button, interaction):
                if before.content == "":
                    before.content = "None"
                if after.content == "":
                    after.content = "None"
                before.content, after.content = before.content.replace(
                    "```", "` ` `"
                ), after.content.replace("```", "`` `")
                await interaction.response.send_message(
                    f"""
Before:
```md
{before.content}
```
After:
```md
{after.content}
```
                """,
                    ephemeral=True,
                )

        if before.author.bot == False:
            if before.content == after.content:
                pass
            else:
                channel = self.bot.sendable_channel(
                    self.bot.get_channel(self.bot.channels.get("logs", 0))
                )
                msgeditb = before.clean_content
                msgedita = after.clean_content
                msgatr = before.author.mention
                msgcnl = before.channel.mention
                pfp = before.author.display_avatar.url
                emb = discord.Embed(
                    title="Message Edited",
                    color=self.bot.color(),
                    url=f"https://discord.com/channels/965419296937365514/{after.channel.id}/{after.id}",
                )
                emb.add_field(
                    name="Content before", value=f"{msgeditb[:1024]}", inline=False
                )
                emb.add_field(
                    name="Content after", value=f"{msgedita[:1024]}", inline=False
                )
                emb.add_field(name="Author", value=f"{msgatr}", inline=True)
                emb.add_field(name="Channel", value=f"{msgcnl}", inline=True)
                emb.add_field(
                    name="Other Information",
                    value=f"""
Pinned: **{after.pinned}**
Type: **{after.type}**
ID: **{after.id}**
                """,
                )
                emb.set_thumbnail(url=pfp)
                if channel:
                    await channel.send(embed=emb, view=ViewRawMessage(self.bot))

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self, before: discord.TextChannel, after: discord.TextChannel
    ):
        channel = self.bot.sendable_channel(
            self.bot.get_channel(self.bot.channels.get("logs", 0))
        )
        embed = discord.Embed(title=f"Channel Updated", colour=self.bot.color())
        embed.add_field(name="", value=after.mention, inline=False)
        if before.name != after.name:
            embed.add_field(
                name="Name",
                value=f"""
Before: **{before.name}**
After: **{after.name}**
            """,
                inline=False,
            )
        if (str(before.type) or str(after.type)) == "text":
            if before.topic != after.topic:
                embed.add_field(
                    name="Topic",
                    value=f"""
Before:
> {before.topic}
After:
> {after.topic}
            """,
                    inline=False,
                )
            if before.slowmode_delay != after.slowmode_delay:
                embed.add_field(
                    name="Slowmode",
                    value=f"""
Before: **{before.slowmode_delay}**s
After: **{after.slowmode_delay}**s
                """,
                    inline=False,
                )
        if before.permissions_synced != after.permissions_synced:
            embed.add_field(
                name="Synced Permissions",
                value=f"""
Before: **{before.permissions_synced}**
After: **{after.permissions_synced}**
            """,
                inline=False,
            )
        if before.category != after.category:
            embed.add_field(
                name="Category",
                value=f"""
Before: **{before.category}**
After: **{after.category}**
            """,
                inline=False,
            )
        if before.overwrites != after.overwrites:
            permoverwritesB = {}
            permoverwritesA = {}
            out = []
            for key, val in before.overwrites.items():
                itobj = iter(before.overwrites[key])
                for perm in before.overwrites[key]:
                    it = next(itobj)
                    if it[1] == None:
                        continue
                    else:
                        permoverwritesB.setdefault(key.id, []).append(it)
            for key, val in after.overwrites.items():
                itobj = iter(after.overwrites[key])
                for perm in after.overwrites[key]:
                    it = next(itobj)
                    if it[1] == None:
                        continue
                    else:
                        permoverwritesA.setdefault(key.id, []).append(it)
            permoverwrites = {}
            for id in permoverwritesA:
                diffA = set(permoverwritesA[id]) - set(permoverwritesB[id])
                diffB = set(permoverwritesB[id]) - set(permoverwritesA[id])
                permoverwrites.setdefault(id, []).append(diffA)
                if (list(diffA) == []) and (list(diffB) == []):
                    continue
                else:
                    perms = []
                    if self.bot.get_user(id):
                        mention = f"<@{id}>"
                    else:
                        mention = f"<@&{id}>"
                    for perm in list(permoverwrites[id])[0]:
                        if list(diffB) == []:
                            diffB = {(perm, "None")}
                        if list(diffA) == []:
                            diffA = {(perm, "None")}
                        perms.append(
                            str(perm[0])
                            + " : "
                            + str(list(diffB)[0][1])
                            + " -> "
                            + str(perm[1])
                        )
                    fperm = (
                        "\n".join(perms)
                        .replace("True", "✅")
                        .replace("False", "❌")
                        .replace("None", "◻️")
                    )
                    out.append(
                        f"""
{mention}
{fperm}
                        """
                    )
            embed.add_field(name="Permissions", value="\n".join(out), inline=False)
        if channel:
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        logs = self.bot.sendable_channel(
            self.bot.get_channel(self.bot.channels.get("logs", 0))
        )
        if before.bot == False:
            if before.name != after.name:
                embed = discord.Embed(
                    title=f"{before} changed their name to `{after.name}`.",
                    colour=self.bot.color(),
                )
                embed.set_thumbnail(url=after.display_avatar.url)
                if logs:
                    await logs.send(embed=embed)
            if before.display_name != after.display_name:
                embed = discord.Embed(
                    title=f"{before} changed their nickname to `{after.display_name}`.",
                    colour=self.bot.color(),
                )
                embed.set_thumbnail(url=after.display_avatar.url)
                if logs:
                    await logs.send(embed=embed)
            if before.discriminator != after.discriminator:
                embed = discord.Embed(
                    title=f"{before} changed their discriminator to `{after.discriminator}`.",
                    colour=self.bot.color(),
                )
                embed.set_thumbnail(url=after.display_avatar.url)
                if logs:
                    await logs.send(embed=embed)
            if before.roles != after.roles:
                embed = discord.Embed(
                    title=f"{before} got their roles changed.", colour=self.bot.color()
                )
                brole = [str(role.id) for role in before.roles]
                brole = ["<@&" + str(role) for role in brole]
                brole = [str(role) + ">" for role in brole]
                arole = [str(role.id) for role in after.roles]
                arole = ["<@&" + str(role) for role in arole]
                arole = [str(role) + ">" for role in arole]
                difr = set(brole) - set(arole)
                difa = set(arole) - set(brole)
                if difr == set():
                    difr = None
                else:
                    difr = "\n".join(list(difr))
                if difa == set():
                    difa = None
                else:
                    difa = "\n".join(list(difa))
                embed.add_field(name="Roles removed:", value=str(difr))
                embed.add_field(name="Roles added:", value=str(difa))
                embed.set_thumbnail(url=after.display_avatar.url)
                if logs:
                    await logs.send(embed=embed)
            if before.display_avatar != after.display_avatar:
                embed = discord.Embed(
                    title=f"{before} changed their avatar to the following image.",
                    colour=self.bot.color(),
                )
                embed.set_image(url=after.display_avatar.url)
                if logs:
                    await logs.send(embed=embed)
        else:
            pass

    @commands.Cog.listener("on_message")
    async def scamcheck(self, message: discord.Message):
        if isinstance(message.author, discord.User):
            return

        class BanView(discord.ui.View):
            def __init__(self, bot):
                self.bot = bot
                super().__init__(timeout=None)

            @discord.ui.button(
                label=f"Ban {message.author}", style=discord.ButtonStyle.danger
            )
            async def button_callback(self, button, interaction):
                try:
                    if isinstance(message.author, discord.User):
                        return

                    await message.author.ban(
                        reason=f"{message.author} sent a scam, confirmed by {interaction.user}"
                    )
                    embed = discord.Embed(
                        title=f"Successfully banned `{message.author}`", colour=0x00FF00
                    )
                    await interaction.response.send_message(embed=embed)
                except Exception as error:
                    embed = discord.Embed(
                        title=f"While trying to ban `{message.author}`, I got the following error:",
                        description=f"\n```{error}\n```",
                        colour=self.bot.color(1),
                    )
                    await interaction.response.send_message(embed=embed)

        def scamChecker(string):
            change = 0
            blacklist = ["@everyone", "@here", "porn", "nudes", "crypto", "free nitro"]
            for i in blacklist:
                if blacklist[change] in string:
                    return True
                change += 1

        guild = self.bot.get_guild(self.bot.server_id)
        if guild:
            role = guild.get_role(self.bot.roles.get("admin", 0))
            if not role:
                return
        else:
            return
        members = [member.id for member in role.members]
        logs = self.bot.sendable_channel(
            self.bot.get_channel(self.bot.channels.get("logs", 0))
        )
        if message.author.id not in members:
            if scamChecker(message.clean_content):
                await message.reply(
                    content="Your message included blacklisted words, and has been deleted."
                )
                embed = discord.Embed(
                    title=f"`{message.author}` might have sent a scam",
                    description=message.content,
                    colour=self.bot.color(1),
                )
                await message.delete(reason=f"{message.author} might have sent a scam.")
                if logs:
                    await logs.send(embed=embed, view=BanView(bot=self.bot))
            else:
                pass
        else:
            pass

    @commands.Cog.listener("on_message")
    async def github_snippet(self, message):
        if not message.author.bot:
            match = re.search(
                r"https?://github\.com/[\w-]+/[\w-]+/[\w./-]+#L(\d+)-L(\d+)",
                message.content,
            )
            if match:
                random.seed(message.content)
                snip_id = random.randint(0, 100)
                url = match.group()
                start_line = match.group(1)
                end_line = match.group(2)
                if (int(end_line) - int(start_line)) > 25:
                    return
                raw_url = url.replace(
                    "github.com", "raw.githubusercontent.com"
                ).replace("/blob", "")
                async with aiohttp.ClientSession() as cs:
                    async with cs.get(raw_url) as r:
                        async with aiofiles.open(f"snip{snip_id}.txt", "wb") as f:
                            await f.write(await r.content.read())
                async with aiofiles.open(f"snip{snip_id}.txt", "r") as f:
                    snip = await f.readlines()

                file_name = url.split("/")[len(url.split("/")) - 1].split("#")[0]
                syntaxh = file_name.split(".")[1]
                out_snip = "".join(snip[int(start_line) - 1 : int(end_line)])
                await message.reply(
                    f"""
`{url.split("/")[3]}/{url.split("/")[4]}`: `{file_name}` line **{start_line}**-**{end_line}**
```{syntaxh}
{out_snip}
```
                """,
                    view=DeleteMsgView(bot=self.bot, auth=message.author),
                )
                os.remove(f"snip{snip_id}.txt")


def setup(bot):
    bot.add_cog(Listeners(bot=bot))
