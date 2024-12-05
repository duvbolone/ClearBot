import io
import os
import discord
import re
import aiosqlite
from pilmoji import Pilmoji
from numerize import numerize as n
from PIL import Image, ImageDraw, ImageFont
from discord import option
from discord.ext import commands

from bot import ClearBot, DB


class LevelingCommands(discord.Cog):
    def __init__(self, bot: ClearBot):
        self.bot = bot

    def userlevel_color(self, c: int = 0) -> tuple[int, int, int]:
        colors = {
            0: {0: (9, 57, 97), 1: (38, 129, 180)},
            1: {0: (253, 133, 45), 1: (254, 179, 45)},
            2: {0: (119, 0, 18), 1: (0, 166, 40)},
        }

        return colors[self.bot.theme][c]
    

    async def generate_image(self, user: discord.User | discord.Member) -> tuple[int, discord.File | None]:
        fail = (False, None)
        async with aiosqlite.connect(DB["main"]) as db:
            usrdata = await db.execute(
                "SELECT * FROM leveling WHERE author_id=?", (str(user.id),)
            )
            usrdata = await usrdata.fetchone()
            if not usrdata:
                return fail
            
            if len(usrdata) < 2:
                return fail

        x1, y1 = 860, 547
        x2, y2 = 2740, 710
        img = Image.open(os.path.join("ui", "images", "userlevel", str(self.bot.theme), "userlevel.png"))
        avatar = Image.open(io.BytesIO(await user.display_avatar.read())).resize((1024, 1024))
        lvlnom = usrdata[3]
        lvl = usrdata[2]
        lvldenom = usrdata[4]
        h, w = avatar.size
        avmask = Image.new("L", (h, w), 0)
        clear = Image.new("RGBA", (h, w), 1)
        draw = ImageDraw.Draw(avmask)
        draw.ellipse((0, 0, h, w), fill=255)
        masked = Image.composite(avatar, clear, mask=avmask)
        font = ImageFont.truetype(
            os.path.join("ui", "fonts", "Inter-Regular.ttf"),
            size=100,
            layout_engine=ImageFont.Layout.BASIC,
        )
        fontbig = ImageFont.truetype(
            os.path.join("ui", "fonts", "Inter-Regular.ttf"),
            size=150,
            layout_engine=ImageFont.Layout.BASIC,
        )
        img.paste(
            masked.resize((612, 612)), (49, 82), mask=masked.resize((612, 612))
        )
        with Pilmoji(img) as pilmoji:
            pilmoji.text(
                (860, 120), str(user.name), fill=(255, 255, 255), font=fontbig
            )
            pilmoji.text(
                (900, 380),
                f"LVL: {n.numerize(int(lvl))}",
                fill=(255, 255, 255),
                font=font,
                emoji_position_offset=(0, 10),
            )
            x3, y3 = x1, y1
            x4, y4 = x1 + ((x2 - x1) * (int(lvlnom) / int(lvldenom))), y2
            pilmoji.text(
                (2000, 380),
                f"XP: {n.numerize(int(lvlnom))} / {n.numerize(int(lvldenom))}",
                fill=(255, 255, 255),
                font=font,
                emoji_position_offset=(0, 10),
            )
        bar = Image.new("RGBA", img.size, 1)
        draw = ImageDraw.ImageDraw(bar)
        draw.ellipse(
            (x1 - ((y2 - y1) / 2), y1, x1 + ((y2 - y1) / 2), y2),
            fill=self.userlevel_color(0),
        )
        draw.ellipse(
            (x2 - ((y2 - y1) / 2), y1, x2 + ((y2 - y1) / 2), y2),
            fill=self.userlevel_color(0),
        )
        draw.rectangle((x1, y1, x2, y2), fill=self.userlevel_color(0))
        draw.rectangle((x3, y3, x4, y4), fill=self.userlevel_color(1))
        draw.ellipse(
            (x1 - ((y2 - y1) / 2), y1, x1 + ((y2 - y1) / 2), y2),
            fill=self.userlevel_color(1),
        )
        draw.ellipse(
            (x4 - ((y2 - y1) / 2), y1, x4 + ((y2 - y1) / 2), y4),
            fill=self.userlevel_color(1),
        )
        img.paste(bar, mask=bar)
        with io.BytesIO() as output:
            img.save(output, format="PNG")
            output.seek(0)
            file = discord.File(output, filename="userlevel.png")
        
            return (True, file)
        
    leveling = discord.SlashCommandGroup(
        name="level", description="🏆 Commands related to the leveling system."
    )

    @commands.Cog.listener()
    async def on_ready(self):
        print(
            "\033[34m|\033[0m \033[96;1mLevel\033[0;36m cog loaded sucessfully\033[0m"
        )

    @leveling.command(name="userlevel", description="🥇 Gets the provided user's level.")
    @option(
        "user", description="The user you want level information about.", required=False
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def userlevel(
        self, ctx: discord.ApplicationContext, user: discord.Member | discord.User
    ):
        await ctx.defer()
        if not user:
            user = ctx.author

        result = await self.generate_image(user)

        if not result[0]:
            if user.bot == True:
                embed = discord.Embed(
                    title="No data found",
                    description="I didn't found any data of leveling, because the provided user is a bot. They don't get to use this amazing leveling system!",
                    color=self.bot.color(1),
                )
                await ctx.respond(embed=embed)
            else:
                if user == None:
                    embed = discord.Embed(
                        title="No data found",
                        description=f"This most probably means that you never sent a message in this server.",
                        color=self.bot.color(1),
                    )
                else:
                    embed = discord.Embed(
                        title="No data found",
                        description=f"This most probably means that {user.mention} never sent a message in this server.",
                        color=self.bot.color(1),
                    )
                await ctx.respond(embed=embed)  
            return

        embed = discord.Embed(color=self.bot.color())
        embed.set_image(url=f"attachment://userlevel.png")
        await ctx.respond(embed=embed, file=result[1])

    @discord.user_command(
        name="User Level", description="🥇 Gets the provided user's level."
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def userlevel_app(
        self, ctx: discord.ApplicationContext, user: discord.Member
    ):
        await ctx.defer()

        result = await self.generate_image(user)

        if not result[0]:
            if user.bot == True:
                embed = discord.Embed(
                    title="No data found",
                    description="I didn't found any data of leveling, because the provided user is a bot. They don't get to use this amazing leveling system!",
                    color=self.bot.color(1),
                )
                await ctx.respond(embed=embed)
            else:
                if user == None:
                    embed = discord.Embed(
                        title="No data found",
                        description=f"This most probably means that you never sent a message in this server.",
                        color=self.bot.color(1),
                    )
                else:
                    embed = discord.Embed(
                        title="No data found",
                        description=f"This most probably means that {user.mention} never sent a message in this server.",
                        color=self.bot.color(1),
                    )
                await ctx.respond(embed=embed)  
            return

        embed = discord.Embed(color=self.bot.color())
        embed.set_image(url=f"attachment://userlevel.png")
        await ctx.respond(embed=embed, file=result[1])

    @leveling.command(
        name="leaderboard", description="📊 See the leaderboard of the whole server."
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def lb(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        output = []
        nameoutput = []
        img = Image.open(f"ui/images/leaderboard/{self.bot.theme}/lb.png")
        async with aiosqlite.connect(DB["main"]) as db:
            sel = await db.execute("SELECT * FROM leveling")
            fetsel = await sel.fetchall()
            for usr in fetsel:
                lvl = usr[2]
                lvlnom = usr[3]
                lvldenom = usr[4]
                user = await self.bot.fetch_user(int(usr[1]))
                line = f"""
        {lvlnom+lvldenom*lvl} LVL: {lvl} XP: {lvlnom}/{n.numerize(lvldenom)}\n
            """
                output.append(line)
                line2 = f"""
            {lvlnom+lvldenom*lvl} {user.name}\n
        """
                nameoutput.append(line2)

            def atoi(text):
                return int(text) if text.isdigit() else text

            def natural_keys(text):
                return [atoi(c) for c in re.split(r"(\d+)", text)]

            output.sort(key=natural_keys, reverse=True)
            nameoutput.sort(key=natural_keys, reverse=True)

            def delstr(lst):
                return [f"{' '.join(elem.split()[1:]).rstrip()}" for elem in lst]

            output = delstr(output)
            nameoutput = delstr(nameoutput)

            nameoutput = [f"{index}       {i}" for index, i in enumerate(nameoutput, 1)]
            output = [direction + "\n\n" for direction in output]
            nameoutput = [direction + "\n\n" for direction in nameoutput]
            embed = discord.Embed(
                title="ClearFly Level Leaderboard",
                description=f"""
Chat to earn xp!
                """,
                color=self.bot.color(),
            )
            font = ImageFont.truetype(
                "ui/fonts/Inter-Regular.ttf",
                size=43,
                layout_engine=ImageFont.Layout.BASIC,
            )
            with Pilmoji(img) as pilmoji:
                pilmoji.text(
                    (800, 30),
                    "".join(output[:10]),
                    fill=(255, 255, 255),
                    font=font,
                    emoji_position_offset=(0, 20),
                )
                pilmoji.text(
                    (27, 30),
                    "".join(nameoutput[:10]),
                    fill=(255, 255, 255),
                    font=font,
                    emoji_position_offset=(0, 20),
                )
            with io.BytesIO() as output:
                img.save(output, format="PNG")
                output.seek(0)
                file = discord.File(output, filename="lb.png")
            embed.set_image(url=f"attachment://lb.png")
            await ctx.respond(embed=embed, file=file)


def setup(bot):
    bot.add_cog(LevelingCommands(bot))
