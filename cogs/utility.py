import json
import os
import platform
import pytz
import discord
import psutil
import urllib.parse
import datetime
import math
from discord import option
from discord.ext import commands
import aiosqlite
from bot import ClearBot, DB

timezones = pytz.all_timezones


class PollTypeYesNo(discord.ui.Modal):
    def __init__(self, bot: ClearBot, *args, **kwargs) -> None:
        self.bot = bot
        super().__init__(*args, **kwargs)

        self.add_item(
            discord.ui.InputText(
                label="Question",
                placeholder="Are you interested in planes?",
                style=discord.InputTextStyle.short,
            )
        )

    async def callback(self, interaction: discord.Interaction):
        conf_embed = discord.Embed(
            title="Successfully created poll", colour=self.bot.color()
        )
        conf_embed.add_field(name="Question", value=str(self.children[0].value))
        conf_embed.add_field(name="Type", value="Yes/No")
        await interaction.response.send_message(embed=conf_embed, ephemeral=True)
        embed = discord.Embed(title="Creating poll...", colour=self.bot.color())
        channel = self.bot.sendable_channel(interaction.channel)
        if channel and interaction.user:
            message = await channel.send(embed=embed)
            poll_id = message.id
        else:
            raise Exception("Unable to send poll message.")

        new_poll = {
            "poll_id": str(poll_id),
            "author": str(interaction.user.id),
            "question": self.children[0].value,
            "type": "yn",
        }
        async with aiosqlite.connect(DB["main"]) as db:
            cur = await db.cursor()
            await cur.execute(
                "INSERT INTO poll (poll_id, author, question, type) VALUES (:poll_id, :author, :question, :type)",
                new_poll,
            )
            await db.commit()
        embed = discord.Embed(
            title=self.children[0].value,
            description="""
1️⃣ Yes

2️⃣ No
        """,
            colour=self.bot.color(),
        )
        embed.set_author(
            name="Asked by " + interaction.user.name,
            icon_url=interaction.user.display_avatar,
        )
        embed.set_footer(text=f"Poll ID: {poll_id}")
        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")
        await message.edit(embed=embed)


class PollTypeMChoice(discord.ui.Modal):
    def __init__(self, bot, choices: int, *args, **kwargs) -> None:
        self.bot = bot
        self.choices = choices
        super().__init__(*args, **kwargs)

        self.add_item(
            discord.ui.InputText(
                label="Question",
                placeholder="Are you interested in planes?",
                style=discord.InputTextStyle.short,
            )
        )
        for choice in range(choices):
            self.add_item(
                discord.ui.InputText(
                    label=f"Choice {choice + 1}",
                    placeholder=f"Choice {choice + 1} content",
                    style=discord.InputTextStyle.short,
                )
            )

    async def callback(self, interaction: discord.Interaction):
        conf_embed = discord.Embed(
            title="Successfully created poll", colour=self.bot.color()
        )
        conf_embed.add_field(name="Question", value=str(self.children[0].value))
        conf_embed.add_field(name="Type", value=f"{self.choices} choices")
        await interaction.response.send_message(embed=conf_embed, ephemeral=True)
        embed = discord.Embed(title="Creating poll...", colour=self.bot.color())
        channel = self.bot.sendable_channel(interaction.channel)
        if channel and interaction.user:
            message = await channel.send(embed=embed)
            poll_id = message.id
        else:
            raise Exception("Unable to send poll message.")

        new_poll = {
            "poll_id": str(poll_id),
            "author": str(interaction.user.id),
            "question": self.children[0].value,
            "type": str(self.choices),
        }
        async with aiosqlite.connect(DB["main"]) as db:
            cur = await db.cursor()
            await cur.execute(
                "INSERT INTO poll (poll_id, author, question, type) VALUES (:poll_id, :author, :question, :type)",
                new_poll,
            )
            await db.commit()

        def int_to_emoji(num):
            return chr(0x0030 + num) + chr(0x20E3)

        choices = []
        for choice in range(self.choices):
            choices.append(
                f"{int_to_emoji(choice + 1)} {self.children[choice + 1].value}\n\n"
            )
            await message.add_reaction(int_to_emoji(choice + 1))
        embed = discord.Embed(
            title=self.children[0].value,
            description=f"""
{''.join(choices)}
        """,
            colour=self.bot.color(),
        )
        embed.set_author(
            name="Asked by " + interaction.user.name,
            icon_url=interaction.user.display_avatar,
        )
        embed.set_footer(text=f"Poll ID: {poll_id}")
        await message.edit(embed=embed)


class UtilityCommands(discord.Cog):
    def __init__(self, bot: ClearBot):
        self.bot = bot

    utility = discord.SlashCommandGroup(
        name="utility", description="🛠️ Commands that are supposed to be useful."
    )
    math = utility.create_subgroup(name="math", description="Commands related to math")
    poll = utility.create_subgroup(name="poll", description="Commands related to polls")
    stats = utility.create_subgroup(
        name="stats", description="Commands related to statistics"
    )  # type: ignore

    @commands.Cog.listener()
    async def on_ready(self):
        print(
            "\033[34m|\033[0m \033[96;1mUtility\033[0;36m cog loaded sucessfully\033[0m"
        )

    @discord.command(
        name="report",
        description="⛑️ Someone is misbehaving? Use this command to contact the admins!",
    )
    @option(
        "subject",
        description="What is your report about?",
        choices=["Misbehaving User", "Spam", "Hacked/Compromised Account", "Raid"],
    )
    @option(
        "priority",
        description="The priority level of the report",
        choices=["low", "medium", "high"],
    )
    @option(
        "user",
        description="The user involved (if more than one mention in comments unless raid)",
        required=False,
    )
    @option(
        "comments", description="Anything else to say about the report?", required=False
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def report(
        self,
        ctx: discord.ApplicationContext,
        subject: str,
        priority: str,
        user: discord.Member,
        comments: str,
    ):
        await ctx.defer(ephemeral=True)
        channel = self.bot.sendable_channel(
            self.bot.get_channel(self.bot.channels.get("dev-chat", 0))
        )
        embed = discord.Embed(
            title=f"{ctx.author} submitted a report!", color=self.bot.color()
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        confirmembed = discord.Embed(
            title="Report send!",
            description="The team will come to help you as soon as possible.",
            color=self.bot.color(),
        )
        if priority == "low":
            embed.add_field(name="Subject:", value=subject)
            embed.add_field(
                name="Involved User:",
                value=f"{user.mention if user else '*None was given*'}",
            )
            embed.add_field(
                name="Comments *if any*:",
                value=f"""
```
{comments}
```
            """,
                inline=False,
            )
            await ctx.respond(embed=confirmembed)
            if channel:
                await channel.send("Low priority report", embed=embed)
        if priority == "medium":
            embed.add_field(name="Subject:", value=subject)
            embed.add_field(
                name="Involved User:",
                value=f"{user.mention if user else '*None was given*'}",
            )
            embed.add_field(
                name="Comments *if any*:",
                value=f"""
```
{comments}
```
            """,
                inline=False,
            )
            await ctx.respond(embed=confirmembed)
            if channel:
                await channel.send(
                    "<@&965422406036488282> Medium priority report", embed=embed
                )
        if priority == "high":
            embed.add_field(name="Subject:", value=subject)
            embed.add_field(
                name="Involved User:",
                value=f"{user.mention if user else '*None was given*'}",
            )
            embed.add_field(
                name="Comments *if any*:",
                value=f"""
```
{comments}
```
            """,
                inline=False,
            )
            await ctx.respond(embed=confirmembed)
            if channel:
                await channel.send(
                    "<@&965422406036488282> ATTENTION ALL ADMINS", embed=embed
                )
                await channel.send(
                    "<@&965422406036488282> ^ THIS IS A HIGH PRIORITY REPORT"
                )

    async def get_commands(self, ctx: discord.AutocompleteContext):
        cmds = []
        for cmd in self.bot.walk_application_commands():
            if isinstance(cmd, discord.commands.SlashCommand):
                cmds.append(str(cmd))
        return [cmd for cmd in cmds if ctx.value in cmd]

    @discord.command(name="help", description="❓ Need help? This is the right command!")
    @option(
        "command",
        description="Get information for a specific command by inputting this option.",
        autocomplete=get_commands,
        required=False,
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def help(self, ctx: discord.ApplicationContext, command: str):
        if command:
            cmd_list = []
            for cmd in self.bot.walk_application_commands():
                if isinstance(cmd, discord.commands.SlashCommand):
                    cmd_list.append(str(cmd))
            if command in cmd_list:
                cmd = self.bot.get_application_command(command)
                if not cmd:
                    raise Exception("Couldn't find command.")

                if cmd.options == []:  # type: ignore
                    opts = ["`No options`"]
                else:
                    opts = []
                    for opt in cmd.options:  # type: ignore
                        opts.append(
                            f"`{opt.name}`(required: {opt.required}): {opt.description}"
                        )
                    opts = "\n".join(opts)
                if cmd.cooldown == None:
                    cd = "`No cooldown`"
                else:
                    cd = f"`{cmd.cooldown.rate}` run(s) every `{round(cmd.cooldown.per)}s`"
                cmd_m, cmd_d = cmd.mention, cmd.description  # type: ignore
                embed = discord.Embed(
                    title=f"`/{command}` info",
                    description=f"""
**Name**: {cmd_m}
**Description**: {cmd_d}
**Cooldown**: {cd}
**Options**: 
{opts}
                """,
                    colour=self.bot.color(),
                )
                await ctx.respond(embed=embed)
            else:
                embed = discord.Embed(
                    title="Command not found",
                    description=f"I didn't found the command `{command}`.",
                    colour=self.bot.color(1),
                )
                await ctx.respond(embed=embed)
        else:
            groups = []
            group_names = []
            for cmd in self.bot.walk_application_commands():
                if isinstance(cmd, discord.commands.SlashCommandGroup):
                    if cmd.parent is None:
                        group_names.append(cmd.name)
                        groups.append(cmd)

            cmds: dict = {"other": []}
            for cmd in self.bot.walk_application_commands():
                if isinstance(cmd, discord.commands.SlashCommand):
                    if str(cmd).split(" ")[0] in group_names:
                        cmds.setdefault(str(cmd).split(" ")[0], []).append(cmd)
                    else:
                        cmds["other"].append(cmd)

            select_groups = []
            for group in groups:
                select_groups.append(
                    discord.SelectOption(
                        label=group.name.title(), description=group.description
                    )
                )
            select_groups.append(
                discord.SelectOption(
                    label="Other", description="❓ Commands not in a group."
                )
            )

            class HelpView(discord.ui.View):
                def __init__(self, bot):
                    self.bot = bot
                    super().__init__(timeout=120, disable_on_timeout=True)

                @discord.ui.select(
                    placeholder="Select command group...",
                    min_values=1,
                    max_values=1,
                    options=select_groups,
                )
                async def select_callback(
                    self, select: discord.ui.Select, interaction: discord.Interaction
                ):
                    await interaction.response.defer()
                    listed_cmds = []
                    for cmd in cmds[str(select.values[0]).lower()]:
                        if cmd.options == []:
                            opts = ["`No options`"]
                        else:
                            opts = []
                            for opt in cmd.options:
                                opts.append(f"`{opt.name}`")
                        listed_cmds.append(
                            f"{cmd.mention}({', '.join(opts)}) - {cmd.description}"
                        )
                    embed = discord.Embed(
                        title=f"{select.values[0]} Commands",
                        description="\n".join(listed_cmds),
                        colour=self.bot.color(),
                    )
                    await interaction.edit_original_response(embed=embed)

            embed = discord.Embed(
                title="Help!",
                description="Select a command group below to view all the available commands inside it.",
                colour=self.bot.color(),
            )
            await ctx.respond(embed=embed, view=HelpView(self.bot))

    @utility.command(name="the-team", description="👏 Shows The ClearFly Team!")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def team(self, ctx: discord.ApplicationContext):
        with open("dev/team.json", "r") as f:
            data = json.load(f)
        embed = discord.Embed(title="The ClearFly Team", color=self.bot.color())
        logo = data["icon"]
        for member in data["members"]:
            embed.add_field(
                name=member, value=f"> {data['members'][member]['role']}", inline=False
            )
        embed.set_thumbnail(url=logo)
        await ctx.respond(embed=embed)

    @utility.command(name="avatar", description="🌌 Shows your avatar.")
    @option("user", description="The user you want the avatar of.", required=False)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def avatar(
        self, ctx: discord.ApplicationContext, user: discord.Member | discord.User
    ):
        await ctx.defer()
        if not user:
            user = ctx.author
            embed = discord.Embed(
                title="Your avatar",
                url=user.display_avatar.url,
                colour=self.bot.color(),
            )
        else:
            embed = discord.Embed(
                title=f"{user.name}'s avatar",
                url=user.display_avatar.url,
                colour=self.bot.color(),
            )

        embed.set_image(url=user.display_avatar.url)
        await ctx.respond(embed=embed)

    @discord.user_command(
        name="User Avatar", description="Get's the avatar from the user"
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def avatar_app(self, ctx, user: discord.Member):
        await ctx.defer()
        embed = discord.Embed(
            title=f"{user.name}'s avatar",
            url=user.display_avatar.url,
            colour=self.bot.color(),
        )
        embed.set_image(url=user.display_avatar.url)
        await ctx.respond(embed=embed)

    @utility.command(name="who-is", description="📰 Fetches a user profile.")
    @option(
        "user", description="The user you want the user profile of.", required=False
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def whois(
        self, ctx: discord.ApplicationContext, user: discord.Member | discord.User
    ):
        await ctx.defer()
        if not user:
            user = ctx.author
        roles = []
        status = str(user.status) if isinstance(user, discord.Member) else "N/A"
        if status == "dnd":
            status = "Do Not Disturb"

        if isinstance(user, discord.Member):
            for role in user.roles:
                roles.append(f"<@&{role.id}>")
        roles = "\n".join(reversed(roles))
        if isinstance(user, discord.Member):
            if user.is_on_mobile():
                device = "Mobile"
            else:
                if status == "offline":
                    device = "User is offline"
                else:
                    device = "Desktop/Web"
        else:
            device = "N/A"

        created_at = discord.utils.format_dt(user.created_at)  # type: ignore
        joined_at = discord.utils.format_dt(user.joined_at) if isinstance(user, discord.Member) else "N/A"  # type: ignore
        embed = discord.Embed(
            title=f"**{user}'s profile:**",
            color=self.bot.color(),
            description=f"""
{user.mention}
**Created on:** {created_at}
**Status:** `{status.title()}`
**Activity:** {user.activity if isinstance(user, discord.Member) else "N/A"}
**Device:** `{device}`

**Joined ClearFly:** {joined_at}
**Nickname:** {user.nick if isinstance(user, discord.Member) else "N/A"}
**Roles:** 
{roles}
        """,
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        await ctx.respond(embed=embed)

    @discord.user_command(name="User Profile")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def whois_app(
        self, ctx: discord.ApplicationContext, user: discord.Member | discord.User
    ):
        await ctx.defer()
        roles = []
        status = str(user.status) if isinstance(user, discord.Member) else "N/A"
        if status == "dnd":
            status = "Do Not Disturb"

        if isinstance(user, discord.Member):
            for role in user.roles:
                roles.append(f"<@&{role.id}>")

        roles = "\n".join(reversed(roles))
        if isinstance(user, discord.Member):
            if user.is_on_mobile():
                device = "Mobile"
            else:
                if status == "offline":
                    device = "User is offline"
                else:
                    device = "Desktop/Web"
        else:
            device = "N/A"

        created_at = discord.utils.format_dt(user.created_at)  # type: ignore
        joined_at = discord.utils.format_dt(user.joined_at) if isinstance(user, discord.Member) else "N/A"  # type: ignore
        embed = discord.Embed(
            title=f"**{user}'s profile:**",
            color=self.bot.color(),
            description=f"""
{user.mention}
**Created on:** {created_at}
**Status:** `{status.title()}`
**Activity:** {user.activity if isinstance(user, discord.Member) else "N/A"}
**Device:** `{device}`

**Joined ClearFly:** {joined_at}
**Nickname:** {user.nick if isinstance(user, discord.Member) else "N/A"}
**Roles:** 
{roles}
        """,
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        await ctx.respond(embed=embed)

    @utility.command(
        name="github", description="🗄️ Shows ClearFly's GitHub repositories."
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def github(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(
            title="ClearFly GitHub:",
            description="- [ClearFly](https://github.com/ClearFly-Official/)\n- [ClearBot](https://github.com/ClearFly-Official/ClearBot)\n- [ClearFly-Branding](https://github.com/ClearFly-Official/ClearFly-Branding)",
            color=self.bot.color(),
        )
        await ctx.respond(embed=embed)

    @math.command(name="basic", description="🧮 Do some basic math.")
    @option(
        "type",
        description="The type of basic math you want to do.",
        choices=["Addition", "Subtraction", "Multiplication", "Division"],
    )
    @option("input1", description="The first number.")
    @option("input2", description="The second number.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def basic(
        self, ctx: discord.ApplicationContext, type, input1: int, input2: int
    ):
        await ctx.defer()
        if type == "Addition":
            embed = discord.Embed(
                description=f"{input1} + {input2} = **{input1+input2}**",
                color=self.bot.color(),
            )
            await ctx.respond(embed=embed)
        if type == "Subtraction":
            embed = discord.Embed(
                description=f"{input1} - {input2} = **{input1-input2}**",
                color=self.bot.color(),
            )
            await ctx.respond(embed=embed)
        if type == "Multiplication":
            embed = discord.Embed(
                description=f"{input1} x {input2} = **{input1*input2}**",
                color=self.bot.color(),
            )
            await ctx.respond(embed=embed)
        if type == "Division":
            if input2 == 0:
                await ctx.respond("You can't divide by 0!")
            else:
                embed = discord.Embed(
                    description=f"{input1} : {input2} = **{input1/input2}**",
                    color=self.bot.color(),
                )
                await ctx.respond(embed=embed)

    @math.command(name="advanced", description="♾️ Do some more advanced math.")
    @option(
        "type",
        description="The type of advanced math you want to do.",
        choices=["Square root", "Power"],
    )
    @option("input", description="The first number")
    @option("power", description="The exponent (not needed for sqrt)", required=False)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def advanced(
        self,
        ctx: discord.ApplicationContext,
        type: str,
        input: int,
        exponent: int | None = None,
    ):
        await ctx.defer()
        if type == "Square root":
            embed = discord.Embed(
                title=f"The square root of {input} is",
                description=f"**{math.sqrt(input)}**",
                color=self.bot.color(),
            )
            await ctx.respond(embed=embed)
        if type == "Power" and exponent == None:
            await ctx.respond("You need to give a exponent...")
            return
        if type == "Power" and isinstance(exponent, int):
            if exponent > 2000:
                embed = discord.Embed(
                    title="Exponent too large!", colour=self.bot.color(1)
                )
                await ctx.respond(embed=embed)
                return
            result = input**exponent
            if int(math.log10(result)) + 1 < 4299:
                embed = discord.Embed(
                    title=f"{input} to the power of {exponent} is",
                    description=f"**{result}**",
                    color=self.bot.color(),
                )
                await ctx.respond(embed=embed)
            else:
                embed = discord.Embed(
                    title="Number too large!", colour=self.bot.color(1)
                )
                await ctx.respond(embed=embed)

    @utility.command(description="🔎 Search the web!")
    @option("query", description="The content you want to search for.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def search(self, ctx: discord.ApplicationContext, query: str):
        convquery = urllib.parse.quote_plus(query)
        view = discord.ui.View()
        google = discord.ui.Button(
            label="Google", url=f"https://google.com/search?q={convquery}"
        )
        bing = discord.ui.Button(
            label="Microsoft Bing", url=f"https://bing.com/search?q={convquery}"
        )
        duckduckgo = discord.ui.Button(
            label="DuckDuckGo", url=f"https://duckduckgo.com/?q={convquery}"
        )
        ecosia = discord.ui.Button(
            label="Ecosia", url=f"https://ecosia.org/search?q={convquery}"
        )
        yahoo = discord.ui.Button(
            label="Yahoo! Search", url=f"https://search.yahoo.com/search?p={convquery}"
        )
        view.add_item(google)
        view.add_item(bing)
        view.add_item(duckduckgo)
        view.add_item(ecosia)
        view.add_item(yahoo)
        embed = discord.Embed(
            title=f"Click the links below to view the results of your search: '**{query}**'.",
            colour=self.bot.color(),
        )
        embed.set_author(
            name=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url,
        )
        await ctx.respond(view=view, embed=embed)

    @poll.command(name="new", description="📜 Post a new poll.")
    @discord.option(
        "poll_type",
        description="You're desired type of poll.",
        choices=["Yes/No", "2 choices", "3 choices", "4 choices"],
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def new_poll(self, ctx: discord.ApplicationContext, poll_type: str):
        if poll_type == "Yes/No":
            await ctx.send_modal(
                PollTypeYesNo(title=f"Setup your {poll_type} poll", bot=self.bot)
            )
        else:
            await ctx.send_modal(
                PollTypeMChoice(
                    title=f"Setup your {poll_type} poll",
                    bot=self.bot,
                    choices=int(poll_type[:1]),
                )
            )

    @poll.command(name="end", description="❌ End a poll and see its results.")
    @discord.option("poll_id", description="ID of the poll you want to end.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def end_poll(self, ctx: discord.ApplicationContext, poll_id_str: str):
        await ctx.defer(ephemeral=True)

        def progress_bar(percent: int) -> str:
            bar = "⬛️" * 10
            bar = bar.replace("⬛", "🟦", round(max(min(percent, 100), 0) / 10))
            return bar

        try:
            poll_id = int(poll_id_str)
            channel = self.bot.sendable_channel(ctx.channel)
            if channel:
                poll_msg = await channel.fetch_message(poll_id)
            else:
                raise Exception("Message not found")

        except discord.NotFound:
            embed = discord.Embed(
                title="Not a valid poll id!",
                description="Please give an actual poll id, where you are the author of. You can find the poll id at the bottom of the poll itself.",
                colour=self.bot.color(1),
            )
            await ctx.respond(embed=embed)
        else:
            async with aiosqlite.connect(DB["main"]) as db:
                curs = await db.cursor()
                poll = await curs.execute(
                    "SELECT * FROM poll WHERE poll_id=?", (poll_id,)
                )
                poll = await poll.fetchone()
            if poll == None:
                embed = discord.Embed(
                    title="It looks like this poll already ended...",
                    colour=self.bot.color(),
                )
                await ctx.respond(embed=embed)
            elif poll[2] == str(ctx.author.id):
                author = ctx.author
                react_types = []
                for reaction in poll_msg.reactions:
                    react_types.append(reaction)
                total_count = 0 - len(react_types)
                reactions = []
                for reaction in react_types:
                    total_count = total_count + reaction.count
                    reactions.append(reaction.count)
                out = []
                for reaction in react_types:
                    if total_count == 0:
                        p_count = 1
                    else:
                        p_count = total_count
                    percent = (reaction.count - 1) / p_count * 100
                    out.append(
                        f"{reaction.emoji}: **{reaction.count - 1}**/**{total_count}**(**{percent}**% of the total votes)\n{progress_bar(percent)}\n\n"
                    )
                embed = discord.Embed(
                    title=f"'{poll[3]}': results",
                    description=f"""
Total votes: **{total_count}**

{''.join(out)}
                """,
                    colour=self.bot.color(),
                ).set_author(
                    icon_url=author.display_avatar, name=f"Poll by {author.name}"
                )
                await poll_msg.edit(embed=embed)
                async with aiosqlite.connect(DB["main"]) as db:
                    cursor = await db.cursor()
                    await cursor.execute("DELETE FROM poll WHERE poll_id=?", (poll_id,))
                    await db.commit()
                embed = discord.Embed(
                    title="Successfully closed poll!", colour=self.bot.color()
                )
                await ctx.respond(embed=embed)
            else:
                embed = discord.Embed(
                    title="You're not the author of this poll!",
                    description="Try again with a poll you own.",
                    colour=self.bot.color(1),
                )
                await ctx.respond(embed=embed)

    @utility.command(description="⏰ Convert time to timestamp.")
    @discord.option(
        name="style",
        choices=[
            f"Short Time (e.g. 14:10)",
            f"Long Time (e.g. 14:10:36)",
            f"Short Date (e.g. 23/7/2023)",
            f"Long Date (e.g. 23 July 2023)",
            f"Short Date Time (e.g. 23 July 2023 14:10)",
            f"Long Date Time (e.g. Sunday, 23 July 2023 14:10)",
            f"Relative Time (e.g. in 8 hours)",
        ],
        description="The style to use for the timestamp",
    )
    @discord.option(
        name="timezone",
        description="The timezone to use (e.g. UTC, CET, EST).",
        # Pylance doesn't seem to find the basic_autocomplete function, but it does in discord.utils.utils, which doesn't even exist.
        # If you find a fix for this, please make a PR on the repository.
        autocomplete=discord.utils.basic_autocomplete(timezones),  # type: ignore
    )
    @discord.option(name="year", description="Years.")
    @discord.option(name="month", description="Months.")
    @discord.option(name="day", description="Days.")
    @discord.option(name="hour", description="Hours.")
    @discord.option(name="minute", description="Minutes.")
    @discord.option(name="second", description="Seconds.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def time2stamp(
        self,
        ctx: discord.ApplicationContext,
        style: str,
        timezone: str,
        year: int = 0,
        month: str = "Default",
        day: int = 0,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
    ):
        try:
            time_zone = pytz.timezone(timezone)
        except pytz.UnknownTimeZoneError:
            embed = discord.Embed(
                title="Incorrect Timezone",
                description="You gave me a non-existent time zone. Please input correct time zones(e.g. UTC, CET, EST, etc.)",
                colour=0xFF0000,
            )
            await ctx.respond(embed=embed)
            return
        o_style = style
        match style.split("(")[0].strip():
            case "Short Time":
                style = "t"
            case "Long Time":
                style = "T"
            case "Short Date":
                style = "d"
            case "Long Date":
                style = "D"
            case "Short Date Time":
                style = "f"
            case "Long Date Time":
                style = "F"
            case "Relative Time":
                style = "R"
            case _:
                style = "R"

        match month.capitalize():
            case "January":
                conv_month = 1
            case "February":
                conv_month = 2
            case "March":
                conv_month = 3
            case "April":
                conv_month = 4
            case "May":
                conv_month = 5
            case "June":
                conv_month = 6
            case "July":
                conv_month = 7
            case "August":
                conv_month = 8
            case "September":
                conv_month = 9
            case "October":
                conv_month = 10
            case "November":
                conv_month = 11
            case "December":
                conv_month = 12
            case _:
                conv_month = datetime.datetime.utcnow().month

        now = datetime.datetime.now(tz=time_zone)
        if second == 0:
            second = now.second
        if not second <= 59 >= 0:
            embed = discord.Embed(
                title="Invalid seconds input",
                description="Seconds parameter must be greater or equal to 0 and smaller than 60",
                colour=0xFF0000,
            )
            await ctx.respond(embed=embed)
            return
        if minute == 0:
            minute = now.minute
        if hour == 0:
            hour = now.hour
        if not hour <= 59 >= 0:
            embed = discord.Embed(
                title="Invalid hour input",
                description="Hour parameter must be greater or equal to 0 and smaller than 60",
                colour=0xFF0000,
            )
            await ctx.respond(embed=embed)
            return
        if day == 0:
            day = now.day
        if conv_month == 2:
            if not day <= 28 > 0:
                embed = discord.Embed(
                    title="Invalid day input",
                    description="Day parameter must be greater than 0 and smaller than 29 if in February",
                    colour=0xFF0000,
                )
                await ctx.respond(embed=embed)
                return
        else:
            if not day <= 31 > 0:
                embed = discord.Embed(
                    title="Invalid day input",
                    description="Day parameter must be greater than 0 and smaller or equal to 31",
                    colour=0xFF0000,
                )
                await ctx.respond(embed=embed)
                return
        if conv_month == 0:
            conv_month = now.month
        if not conv_month <= 12 > 0:
            embed = discord.Embed(
                title="Invalid month input",
                colour=0xFF0000,
            )
            await ctx.respond(embed=embed)
            return
        if year == 0:
            year = now.year
        if not year <= 9999 >= 0:
            embed = discord.Embed(
                title="Invalid year input",
                description="Year parameter must be greater or equal to 0 and smaller than 10000",
                colour=self.bot.color(),
            )
            await ctx.respond(embed=embed)
            return

        naive_datetime = datetime.datetime(
            year=year,
            month=conv_month,
            day=day,
            hour=hour,
            minute=minute,
            second=second,
        )
        time_2_conv = time_zone.localize(naive_datetime)

        # Pylance doesn't seem to find the format_dt function, but it does in discord.utils.utils, which doesn't even exist.
        # If you find a fix for this, please make a PR on the repository.
        conv_time = discord.utils.format_dt(time_2_conv, style=style)  # type: ignore
        embed = discord.Embed(
            title="Here's your converted time!",
            colour=self.bot.color(),
        )
        embed.add_field(name="Display", value=conv_time)
        embed.add_field(name="Raw", value=f"`{conv_time}`")
        embed.add_field(
            name="Parameters",
            value=f"""
Style: **{o_style.split('(')[0]}**
Timezone: **{str(timezone)}**
Year: **{year}**
Month: **{conv_month}**
Day: **{day}**
Hour: **{hour}**
Minute: **{minute}**
Second: **{second}**
        """,
            inline=False,
        )
        await ctx.respond(embed=embed)

    @stats.command(name="server", description="🛜 Show the server statistics.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def server_stats(self, ctx: discord.ApplicationContext):
        join_stats = None
        async with aiosqlite.connect(DB["main"]) as db:
            cur = await db.execute("SELECT * FROM stats WHERE name='join'")
            join_stats = await cur.fetchone()
            if not join_stats:
                raise Exception("Couldn't fetch join_stats from database.")

        if int(join_stats[2]) == 0:
            join_pphrase = ""
        else:
            join_perc = abs(
                round(
                    ((int(join_stats[3]) - int(join_stats[2])) / int(join_stats[2]))
                    * 100,
                    2,
                )
            )
            if int(join_stats[2]) < int(join_stats[3]):
                join_pphrase = f"There was a {join_perc}% increase in joins!"
            else:
                join_pphrase = f"There was a {join_perc}% decrease in joins..."

        guild = ctx.guild
        if not guild:
            raise Exception("Couldn't fetch guild.")

        created_at, created_at_rel = discord.utils.format_dt(guild.created_at), discord.utils.format_dt(guild.created_at, style="R")  # type: ignore

        embed = discord.Embed(
            title="Server Stats", colour=self.bot.color()
        ).set_thumbnail(
            url=guild.icon.url
            if guild.icon
            else "https://matt3o0.is-a.dev/r/img_not_found/"
        )
        embed.add_field(
            name="General",
            value=f"""
Owner: {guild.owner.mention if guild.owner else "N/A"}({guild.owner.name if guild.owner else "N/A"})
Created At: {created_at}({created_at_rel})
Channel Count: **{len(guild.channels)}**
Role Count: **{len(guild.roles)}**
        """,
        )
        embed.add_field(
            name="Members",
            value=f"""
Member Count: **{guild.member_count}**
Joins this week: **{join_stats[3]}**
Joins last week: **{join_stats[2]}**
{join_pphrase}
        """,
        )
        embed.add_field(
            name="Features",
            value="\n".join(
                ["• " + (f.title().replace("_", " ")) for f in guild.features]
            ),
            inline=False,
        )
        await ctx.respond(embed=embed)

    @stats.command(name="bot", description="📈 Show statistics about the bot.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def stats_cmd(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        loc = 0
        f = open("main.py", "r")
        loc += int(len(f.readlines()))
        f.close()
        f = open("bot.py", "r")
        loc += int(len(f.readlines()))
        f.close()
        for cog in self.bot.cog_list:
            f = open(os.path.join("cogs", f"{cog}.py"))
            loc += int(len(f.readlines()))
            f.close()
        if platform.system().lower() == "linux":
            temp = os.popen("vcgencmd measure_temp").readline()
            temp = temp.replace("temp=", "").replace("'", "°")
        else:
            temp = "N/A"
        cogs_list = "\n".join(self.bot.cog_list)
        delta_uptime = datetime.datetime.utcnow() - self.bot.start_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        embed = discord.Embed(
            title="**Bot Stats**",
            description=f"""
**Uptime:** {days}d {hours}h {minutes}m {seconds}s.
**Latency:** {round(self.bot.latency*1000)}ms
**CPU usage:** {psutil.cpu_percent()}%
**CPU temp:** {temp}
**RAM usage:** {psutil.virtual_memory()[2]}% (total {round(psutil.virtual_memory()[0]/1000000)}MB)
**Total lines of code:** {loc}

**Cogs loaded:**
```
{cogs_list}
```
        """,
            color=self.bot.color(),
        )
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(UtilityCommands(bot))
