import discord
import aiosqlite
import time
from discord import option
from discord.ext import commands
from discord.ext.pages import Page, Paginator

from bot import ClearBot, DB


class TagCommands(discord.Cog):
    def __init__(self, bot: ClearBot):
        self.bot = bot

    tags = discord.SlashCommandGroup(
        name="tag", description="🏷️ Commands related to the tag system."
    )

    @commands.Cog.listener()
    async def on_ready(self):
        print("\033[34m|\033[0m \033[96;1mTags\033[0;36m cog loaded sucessfully\033[0m")

    async def get_tags(self, ctx: discord.AutocompleteContext):
        async with aiosqlite.connect(DB["main"]) as db:
            cursor = await db.execute("SELECT name FROM tags")
            rows = await cursor.fetchall()
            tags = [row[0] for row in rows]
        return [tag for tag in tags if ctx.value in tag]

    @tags.command(description="🔎 View a tag.")
    @option("tag", description="The tag you want to view.", autocomplete=get_tags)
    @option(
        "raw",
        description="Toggles if you want to view the tag raw, for copying/editing.",
        required=False,
    )
    @option(
        "info",
        description="Toggles if you want to view information about the tag.",
        required=False,
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def view(
        self, ctx: discord.ApplicationContext, tag: str, raw: bool, info: bool
    ):
        tags = []
        await ctx.defer()
        async with aiosqlite.connect(DB["main"]) as db:
            cursor = await db.execute("SELECT name FROM tags")
            rows = await cursor.fetchall()
            tags = [row[0] for row in rows]
        if tag in tags:
            async with aiosqlite.connect(DB["main"]) as db:
                curs = await db.cursor()
                output = await curs.execute("SELECT * FROM tags WHERE name=?", (tag,))
                output = await output.fetchone()
                if not output:
                    raise ValueError("Couldn't fetch the tag from the database")
            if raw:
                await ctx.respond(
                    f"```\n{output[2]}\n```",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            elif info:
                embed = discord.Embed(title="Tag information", colour=self.bot.color())
                tagAuthor = await self.bot.fetch_user(int(output[3]))
                embed.add_field(name="Name", value=output[1], inline=False)
                embed.add_field(name="Value", value=output[2], inline=False)
                embed.add_field(name="Author", value=tagAuthor.mention, inline=False)
                embed.add_field(
                    name="Created At",
                    value=f"<t:{round(float(output[5]))}:f>(<t:{round(float(output[5]))}:R>)",
                )
                embed.add_field(
                    name="Edited At",
                    value=f"<t:{round(float(output[4]))}:f>(<t:{round(float(output[4]))}:R>)",
                )
                embed.set_thumbnail(url=tagAuthor.display_avatar.url)
                await ctx.respond(embed=embed)
            else:
                await ctx.respond(
                    f"{output[2]}",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
        else:
            embed = discord.Embed(
                title="Tag not found",
                description=f"""
Didn't found {tag}. 
            """,
                colour=self.bot.color(1),
            )
            await ctx.respond(embed=embed)

    @tags.command(name="list", description="📂 List all the tags.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def listtags(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        tags = []
        async with aiosqlite.connect(DB["main"]) as db:
            cursor = await db.execute("SELECT name FROM tags")
            rows = await cursor.fetchall()
            tags = [row[0] for row in rows]
        var = 0
        var2 = 1
        for i in tags:
            tags[var] = f"{var2}: " + f"`{tags[var]}`"
            var += 1
            var2 += 1

        chunks = [tags[i : i + 25] for i in range(0, len(tags), 25)]

        pages = [
            Page(
                embeds=[
                    discord.Embed(
                        title=f"Tags {i+1}-{i+len(chunk)}",
                        description="\n".join(chunk),
                        colour=self.bot.color(),
                    ).set_footer(text=f"Showing 25/page, total of {len(tags)} tags")
                ]
            )
            for i, chunk in enumerate(chunks)
        ]
        paginator = Paginator(
            pages, use_default_buttons=False, custom_buttons=self.bot.paginator_buttons
        )
        await paginator.respond(ctx.interaction)

    @tags.command(description="➕ Add a new tag.")
    @option("name", description="The name of the new tag.")
    @option("value", description="The value of the new tag.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def add(self, ctx: discord.ApplicationContext):
        class AddTagModal(discord.ui.Modal):
            def __init__(self, bot: ClearBot, *args, **kwargs) -> None:
                self.bot = bot
                super().__init__(*args, **kwargs)

                self.add_item(
                    discord.ui.InputText(label="Name of tag", placeholder="foo")
                )
                self.add_item(
                    discord.ui.InputText(
                        label="Value of tag",
                        style=discord.InputTextStyle.long,
                        placeholder="A very interesting value.",
                    )
                )

            async def callback(self, interaction: discord.Interaction):
                new_tag = {
                    "name": self.children[0].value,
                    "value": self.children[1].value,
                    "author": str(ctx.author.id),
                    "created_at": str(time.time()),
                    "edited_at": str(time.time()),
                }
                async with aiosqlite.connect(DB["main"]) as db:
                    cur = await db.cursor()
                    await cur.execute(
                        "INSERT INTO tags (name, value, author, edited_at, created_at) VALUES (:name, :value, :author, :edited_at, :created_at)",
                        new_tag,
                    )
                    await db.commit()
                embed = discord.Embed(
                    title=f"Tag created with following data:",
                    description=f"\n\n**Name:** {self.children[0].value}\n\n**Value:** {self.children[1].value}",
                    colour=self.bot.color(),
                )
                await interaction.response.send_message(embed=embed)

        modal = AddTagModal(bot=self.bot, title="Create a new tag.")
        await ctx.send_modal(modal)

    @tags.command(description="✍️ Edit a tag.")
    @option("edit", description="The tag you want to edit.", autocomplete=get_tags)
    @option("name", description="The name of the edited tag.")
    @option("value", description="The value of the edited tag.")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def edit(self, ctx: discord.ApplicationContext, edit: str):
        class EditTagModal(discord.ui.Modal):
            def __init__(self, bot: ClearBot, *args, **kwargs) -> None:
                self.bot = bot
                super().__init__(*args, **kwargs)

                self.add_item(
                    discord.ui.InputText(label="Name of tag", placeholder="foo")
                )
                self.add_item(
                    discord.ui.InputText(
                        label="Value of tag",
                        style=discord.InputTextStyle.long,
                        placeholder=f"A value that's very, very interesting and useful.",
                    )
                )

            async def callback(self, interaction: discord.Interaction):
                tags = []
                async with aiosqlite.connect(DB["main"]) as db:
                    cursor = await db.execute("SELECT name FROM tags")
                    rows = await cursor.fetchall()
                    tags = [row[0] for row in rows]
                if edit in tags:
                    new_tag = {
                        "name": self.children[0].value,
                        "value": self.children[1].value,
                        "edited_at": str(time.time()),
                        "old_name": edit,
                    }
                    async with aiosqlite.connect(DB["main"]) as db:
                        cursor = await db.cursor()
                        await cursor.execute(
                            "UPDATE tags SET name=:name, value=:value, edited_at=:edited_at WHERE name=:old_name",
                            new_tag,
                        )
                        await db.commit()
                    embed = discord.Embed(
                        title=f"Tag edited with following data:",
                        description=f"\n\n**Name:** {self.children[0].value}\n\n**Value:** {self.children[1].value}",
                        colour=self.bot.color(),
                    )
                    await interaction.response.send_message(embed=embed)
                else:
                    embed = discord.Embed(
                        title="Tag not found",
                        description=f"""
Didn't found {edit}. 
                        """,
                        colour=self.bot.color(1),
                    )
                    await interaction.response.send_message(embed=embed)

        async with aiosqlite.connect(DB["main"]) as db:
            curs = await db.cursor()
            edit_tag = await curs.execute("SELECT * FROM tags WHERE name=?", (edit,))
            edit_tag = await edit_tag.fetchone()
            if not edit_tag:
                raise ValueError("Couldn't fetch tag from database.")

        if isinstance(ctx.author, discord.User):
            return

        authroles = [role.id for role in ctx.author.roles]
        if int(edit_tag[3]) == ctx.author.id:
            modal = EditTagModal(bot=self.bot, title="Edit a tag.")
            await ctx.send_modal(modal)
        elif self.bot.roles.get("admin", 0) in authroles:
            modal = EditTagModal(
                bot=self.bot, title="Edit a tag (this is not your tag!)."
            )
            await ctx.send_modal(modal)
        else:
            embed = discord.Embed(
                title="Not author",
                description="You are not authorised to edit this tag!",
                colour=self.bot.color(1),
            )
            await ctx.respond(embed=embed)

    @tags.command(description="⛔️ Delete a tag.")
    @option("tag", description="The tag you want to delete.", autocomplete=get_tags)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def delete(self, ctx: discord.ApplicationContext, tag: str):
        await ctx.defer()
        async with aiosqlite.connect(DB["main"]) as db:
            curs = await db.cursor()
            del_tag = await curs.execute("SELECT * FROM tags WHERE name=?", (tag,))
            del_tag = await del_tag.fetchone()
            if not del_tag:
                raise ValueError("Couldn't fetch tag from database.")

        if isinstance(ctx.author, discord.User):
            return

        authroles = [role.id for role in ctx.author.roles]
        if int(del_tag[3]) == ctx.author.id:
            async with aiosqlite.connect(DB["main"]) as db:
                cursor = await db.cursor()
                await cursor.execute("DELETE FROM tags WHERE name=?", (tag,))
                await db.commit()
            embed = discord.Embed(
                title=f"Tag `{tag}` deleted successfully", colour=self.bot.color()
            )
        elif self.bot.roles.get("admin", 0) in authroles:
            async with aiosqlite.connect(DB["main"]) as db:
                cursor = await db.cursor()
                await cursor.execute("DELETE FROM tags WHERE name=?", (tag,))
                await db.commit()
            embed = discord.Embed(
                title=f"Tag `{tag}` deleted successfully (it was not yours!)",
                colour=self.bot.color(),
            )
        else:
            embed = discord.Embed(
                title="Not author",
                description="You are not authorised to delete this tag!",
                colour=self.bot.color(1),
            )

        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(TagCommands(bot))
