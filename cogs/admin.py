import discord
from discord import option
from discord.ext import commands


#cfc = 0x2681b4 #<- default color
#cfc = 0xcc8d0e # <- halloween color
cfc = 0x00771d # <- christmas color
errorc = 0xFF0000


class AdminCommands(discord.Cog):

    def __init__(self, bot):
        self.bot = bot

    
    admin = discord.SlashCommandGroup(name="admin", description="Commands for admins")
        
    @admin.command(name="echo",description="Send a message as ClearBot.")
    @option("text", description="The text you want to send as the bot.")
    @commands.has_permissions(manage_channels=True)
    async def echo(self,ctx, text: str):
        await ctx.respond('posted your message!',ephemeral  = True)
        await ctx.channel.send(text)
        pfp = ctx.author.avatar.url
        channel = self.bot.get_channel(1001405648828891187)
        emb = discord.Embed(title=f"{ctx.author} used echo:", description=text, color = cfc)
        emb.set_thumbnail(url=pfp)
        await channel.send(embed=emb)

    @admin.command(name="embed",description="Send an embed as ClearBot.")
    @option("title", description="The title of the embed.")
    @option("description", description="The description of the embed.")
    @commands.has_permissions(manage_channels=True)
    async def embed(self,ctx, title: str, description: str):
        await ctx.respond('posted your embed!',ephemeral  = True)
        emb = discord.Embed(title=title, description=description, color=cfc)
        await ctx.channel.send(embed=emb)
        pfp = ctx.author.avatar.url
        channel2 = self.bot.get_channel(1001405648828891187)
        embed = discord.Embed(title=f"{ctx.author} used embed:", color = cfc)
        embed.add_field(
            name="Title",
            value=f"""
```
{title}
```
                """
        )
        embed.add_field(
                name="Description",
                value=f"""
```
{description}
```
                """
        , inline = False)
        embed.set_thumbnail(url=pfp)
        await channel2.send(embed=embed)

    @admin.command(name="spam", description="Spam the channel to oblivion.")
    @option("amount", description="Amount of messages to spam.")
    @option("text", description="What you want to spam.")
    @commands.has_permissions(manage_channels=True)
    async def spam(self, ctx, amount: int,text):
        channel = self.bot.get_channel(1001405648828891187)
        user = ctx.author
        global confirm
        confirm = 0
        if amount > 100:
            class Spam(discord.ui.View):
                def __init__(self, bot):
                    self.bot = bot
                    super().__init__(timeout=15.0)

                @discord.ui.button(custom_id="okbutton", style=discord.ButtonStyle.green, emoji="<:yes:765068298004987904>")
                async def button_callback(self, button, interaction):
                    global confirm
                    confirm = 1
                    channel = self.bot.get_channel(1001405648828891187)
                    await interaction.response.send_message(f"Ok, here we go! `{ctx.channel}` {amount} times", ephemeral=True)
                    embed = discord.Embed(title=f"**{ctx.author}** spammed `{ctx.channel}` **{amount} times**(after confirmation) with the following text:", description=text, color=cfc)
                    embed.set_thumbnail(url=ctx.author.avatar.url)
                    await channel.send(embed=embed)
                    for i in range(amount):
                        await ctx.send(text)
                @discord.ui.button(custom_id="nobutton", style=discord.ButtonStyle.danger, emoji="<:No:744714930946572371>")
                async def second_button_callback(self, button, interaction):
                    global confirm
                    confirm = 1
                    await interaction.response.send_message(f"Ok, cancelling.", ephemeral=True)
                    await ctx.edit(view=None)

                async def on_timeout(self):
                    global confirm
                    if confirm == 0:
                        await ctx.edit(view=None)
                        await ctx.respond("You waited too long. Rerun the command to start over!", ephemeral=True)
                    else:
                        return

            embed=discord.Embed(title="**Do you want to continue?**", description=f"You are spamming **{amount} times**. That's a lot!", color=cfc)
            await ctx.respond(embed=embed,view=Spam(bot=self.bot),ephemeral=True)
        else:
            chnlmention = self.bot.get_channel(ctx.channel.id)
            embed = discord.Embed(title=f"**{ctx.author}** spammed `{ctx.channel}` **{amount} times** with the following text:", description=text, color=cfc)
            embed.set_thumbnail(url=user.avatar.url)
            await ctx.respond("Get ready for the show <:aye:965627580743024671>", ephemeral=True)
            await channel.send(embed=embed)
            for i in range(amount):
                await ctx.send(text)

    @admin.command(name="slowmode", description="Set the slowmode time of a channel.")
    @option("slowmode", description="The amount of time the slowmode should be, in seconds.")
    @option("channel", description="The channel to apply the slowmode to.", required=False)
    @commands.has_permissions(manage_channels=True)
    async def sm(self, ctx, slowmode:int, channel: discord.TextChannel):
        logchannel = self.bot.get_channel(1001405648828891187)
        if slowmode > 21600:
            await ctx.respond("Maximum slowmode is 21600 seconds!")
        if channel == None:
            await ctx.channel.edit(slowmode_delay=slowmode)
            embed = discord.Embed(title=f"This channel's slow mode has been set to {slowmode} second(s)!", color=cfc)
            await ctx.respond(embed=embed)
            embed = discord.Embed(title=f"{ctx.author} changed `{ctx.channel}`'s slowmode to {slowmode} second(s).", colour=cfc)
            embed.set_thumbnail(url=ctx.author.avatar.url)
            await logchannel.send(embed=embed)
        else:
            await channel.edit(slowmode_delay=slowmode)
            embed = discord.Embed(title=f"`{channel}`'s slow mode has been set to {slowmode} second(s)!", color=cfc)
            await ctx.respond(embed=embed)
            embed = discord.Embed(title=f"{ctx.author} changed `{channel.mention}` slowmode to {slowmode} second(s).", colour=cfc)
            embed.set_thumbnail(url=ctx.author.avatar.url)
            await logchannel.send(embed=embed)

    @admin.command(description='Delete large amounts of messages from a channel.')
    @option("amount", description="The number of messages you want to delete.")
    @commands.has_permissions(manage_channels=True)
    async def purge(self, ctx, amount: int):
        global confirm
        confirm = 0
        channel = self.bot.get_channel(1001405648828891187)
        if amount > 100:
            class PurgeView(discord.ui.View):
                def __init__(self, bot):
                    self.bot = bot
                    super().__init__(timeout=15.0)

                @discord.ui.button(custom_id="okbutton", style=discord.ButtonStyle.green, emoji="<:yes:765068298004987904>")
                async def button_callback(self, button, interaction):
                    global confirm 
                    confirm = 1
                    channel = self.bot.get_channel(1001405648828891187)
                    await interaction.response.send_message(f"Ok, purging {amount} messages.", ephemeral=True)
                    await ctx.channel.purge(limit=amount, check=lambda message: not message.pinned)
                    embed = discord.Embed(title=f"{ctx.author} purged **{amount}** messages in `{ctx.channel}` after confirmation!", color=cfc)
                    embed.set_thumbnail(url=ctx.author.avatar.url)
                    await channel.send(embed=embed)
                    await ctx.edit(view=None)
                @discord.ui.button(custom_id="nobutton", style=discord.ButtonStyle.danger, emoji="<:No:744714930946572371>")
                async def second_button_callback(self, button, interaction):
                    global confirm
                    confirm = 1
                    await interaction.response.send_message(f"Ok, cancelling purge.", ephemeral=True)
                    await ctx.edit(view=None)

                async def on_timeout(self):
                    global confirm
                    if confirm == 0:
                        await ctx.edit(view=None)
                        await ctx.respond("You waited too long. Rerun the command to purge!", ephemeral=True)
                    else:
                        return
            embed=discord.Embed(title="**Do you want to continue?**", description=f"You are purging **{amount} messages**. that's a lot!", color=cfc)
            await ctx.respond(embed=embed,view=PurgeView(bot=self.bot),ephemeral=True)
        else:
            await ctx.channel.purge(limit=amount, check=lambda message: not message.pinned)
            await ctx.respond(f"Purging {amount} messages.", ephemeral=True)
            chnlmention = self.bot.get_channel(ctx.channel.id)
            embed = discord.Embed(title=f"{ctx.author} purged **{amount}** messages in `{ctx.channel}`!", color=cfc)
            embed.set_thumbnail(url=ctx.author.avatar.url)
            await channel.send(embed=embed)

def setup(bot):
    bot.add_cog(AdminCommands(bot))
