import datetime
import os
import re
import sqlite3
import time
from typing import List, Literal

import aiofiles
import aiosqlite
import discord
import requests
from discord.ext.pages import PaginatorButton

DB = {"main": os.path.join("database","main.db"), "va": os.path.join("database","va.db")}

class UserObject(discord.Object):
    def __init__(self) -> None:
        self.id = 0
        self.name = "N/A"
        self.display_name = "N/A"
        self.global_name = "N/A"
        super().__init__(self.id)


class VA:
    @classmethod
    async def get_users(cls, get_type: Literal["id", "full"] = "id"):
        out = []
        async with aiosqlite.connect(DB["va"]) as db:
            cur = await db.execute("SELECT * FROM users")
            out = await cur.fetchall()
        if (get_type == "full") or (get_type is None):
            return out
        elif get_type == "id":
            return [usr[1] for usr in out]
        else:
            raise ValueError(f"Didn't found get_type '{get_type}'")

    @classmethod
    async def has_flights(cls, user: discord.User | discord.Member):
        async with aiosqlite.connect(DB["va"]) as db:
            cur = await db.execute(
                "SELECT id FROM flights WHERE user_id=?", (str(user.id),)
            )
            flights = await cur.fetchall()

        if (flights == []) or (flights is None):
            return False
        else:
            return True

    @classmethod
    async def generate_flight_number(
        cls, aircraft_icao, origin_icao, destination_icao, prefix="CR"
    ):
        async with aiosqlite.connect(DB["va"]) as db:
            cur = await db.execute("SELECT icao FROM aircraft")
            aircraft = await cur.fetchall()
            aircraft = [aircraft[0] for aircraft in aircraft]
        abc = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"

        org_num = 0
        for l in list(origin_icao):
            org_num = org_num + list(abc).index(l)

        des_num = 0
        for l in list(destination_icao):
            des_num = des_num + list(abc).index(l)

        if len(str(aircraft.index(aircraft_icao))) > 2:
            ac_incode = str(aircraft.index(aircraft_icao))[:2]
            org_num += 1
            des_num += 1
        else:
            ac_incode = aircraft.index(aircraft_icao)

        flight_number = prefix + str(ac_incode) + str(org_num) + str(des_num)

        return flight_number

    @classmethod
    async def get_aircraft_from_type(
        cls, aircraft_type: str = "All", output_type: str = "list"
    ):
        aircraft_types = ["Airliner", "GA", "All"]
        if aircraft_type not in aircraft_types:
            aircraft_type = "All"
        async with aiosqlite.connect(DB["va"]) as db:
            if aircraft_type != "All":
                cur = await db.execute(
                    "SELECT * FROM aircraft WHERE type=?",
                    (aircraft_type,),
                )
                aircraft = await cur.fetchall()
            else:
                cur = await db.execute("SELECT * FROM aircraft")
                aircraft = await cur.fetchall()
        if output_type == "list":
            aircraft = [ac[1] for ac in aircraft]
        elif output_type == "IN_SQL":
            aircraft = "(" + ", ".join([f"'{ac[1]}'" for ac in aircraft]) + ")"

        return aircraft

    @classmethod
    def get_flights_from_user(cls, user: discord.Member | discord.User) -> list[tuple]:
        db = sqlite3.connect(DB["va"])
        cur = db.execute("SELECT * FROM flights WHERE user_id=?", (str(user.id),))
        flights = cur.fetchall()
        return flights


class ClearBot(discord.Bot):
    def __init__(self, *args, **kwargs) -> None:
        self.color = self.embed_color
        self.dev_mode = os.path.exists(".dev")
        
        self.start_time = datetime.datetime.utcnow()
        self.cog_list = [
            x.split(".")[0] for x in os.listdir("cogs") if x.endswith(".py")
        ]

        resp = requests.get("https://github.com/mwgg/Airports/raw/master/airports.json")
        self.airports = resp.json()

        self.airports_ac = []

        for ap in self.airports:
            icao = self.airports[ap].get("icao")
            iata = self.airports[ap].get("iata")
            name = self.airports[ap].get("name")

            self.airports_ac.append(
                f"{icao if icao else 'N/A'}, {iata if iata else 'N/A'}, {name if name else 'N/A'}"
            )

        self.airports_icao = [
            self.airports[ap].get("icao")
            for ap in self.airports
            if self.airports[ap].get("icao")
        ]

        con = sqlite3.connect(DB["main"])
        # 0 = normal
        # 1 = halloween
        # 2 = Christmas
        self.theme = int(
            con.execute("SELECT value FROM config WHERE key='theme'").fetchone()[0]
        )
        con.close()

        self.paginator_buttons = [
            PaginatorButton("first", label="<<", style=discord.ButtonStyle.secondary),
            PaginatorButton("prev", label="<", style=discord.ButtonStyle.danger),
            PaginatorButton(
                "page_indicator", style=discord.ButtonStyle.gray, disabled=True
            ),
            PaginatorButton("next", label=">", style=discord.ButtonStyle.primary),
            PaginatorButton("last", label=">>", style=discord.ButtonStyle.secondary),
        ]

        self.server_id = 965419296937365514
        self.bot_author = 668874138160594985
        self.bot_id = 0

        self.channels = {
            "info": 1002194493304479784,
            "arrivals": 965600413376200726,
            "fbo": 1013934267966967848 if not self.dev_mode else 1001401783689678868,
            "va-overview": 1099712642916044881,
            "va-liveries": 1041057335449227314,
            "news": 1066124540318588928,
            "logs": 1001405648828891187,
            "dev-chat": 965655791468183612,
        }
        self.roles = {
            "admin": 965422406036488282,
            "member": 1002200398905483285,
            "clearfly-pilot": 1013933799777783849,
            "count-god": 977868778815758356,
            "livery-painter": 1055919452086087720,
            "clearfly-livery-painter": 1055909461488844931,
            "clearfly-unofficial-painter": 1098964227689033759,
            "bot": 970019585858363482,
        }

        self._colors = {
            0: {
                0: 0x6DB2D9,
                1: 0xCC8D0E,
                2: 0x00771D,
            },
            1: {0: 0xFF0000, 1: 0xFF0000, 2: 0xFF0000},
            2: {0: 0xFFAA00, 1: 0xFFAA00, 2: 0xFFAA00},
        }

        self.va = VA

        super().__init__(*args, **kwargs)

    def embed_color(self, type: int = 0) -> int:
        try:
            return self._colors[type][self.theme]
        except KeyError:
            return self._colors[0][self.theme]

    def sendable_channel(
        self, channel
    ) -> discord.TextChannel | discord.VoiceChannel | None:
        if isinstance(channel, discord.StageChannel):
            return
        elif isinstance(channel, discord.ForumChannel):
            return
        elif isinstance(channel, discord.CategoryChannel):
            return
        elif not channel.can_send():
            return
        elif not channel:
            return
        else:
            return channel

    def user_object(
        self, user: discord.User | discord.Member | None
    ) -> UserObject | discord.Member | discord.User:
        if user:
            return user
        else:
            user_o = UserObject()
            return user_o

    def is_interaction_owner(
        self, interaction: discord.Interaction, user_id: int
    ) -> bool:
        if interaction.user:
            return interaction.user.id == user_id
        else:
            return False

    async def setup_server(self) -> bool:
        file1 = discord.File(
            f"ui/images/banners/{self.theme}/rules.png", filename="rules.png"
        )
        rembed1 = discord.Embed(color=self.color()).set_image(
            url="attachment://rules.png"
        )
        rembed2 = discord.Embed(
            color=self.color(),
            description="""
**1.** Don’t post any inappropriate content.

**2.** Use channels for their intended use.

**3.** Do not spam mention members.

**4.** Do not be overly political.

**5.** Use common sense.

**6.** Follow the [Discord TOS](https://discord.com/terms) and [Community Guidelines](https://discord.com/guidelines).

**7.** Use </report:1018970055972757506> to let us know about anyone breaking the rules.
        """,
        )
        rembed3 = discord.Embed(
            title="Links",
            description="""
- [X-Plane.org Forums](https://forums.x-plane.org/index.php?/forums/topic/265735-clearfly-boeing-737-100/&page=99999999999)
- [Discord](https://discord.gg/jjpwtusf6n)
                               """,
            colour=self.color(),
        )

        def check(msg: discord.Message) -> bool:
            return msg.author.bot

        fbo = self.sendable_channel(self.get_channel(self.channels.get("fbo", 0)))
        if not fbo:
            raise Exception("Didn't find the fbo channel.")
        vembed = discord.Embed(
            title="ClearFly VA",
            colour=self.color(),
            description=f"""
ClearFly VA is a Virtual Airline that offers a fun way to fly without requiring any prior training or extensive knowledge on aviation. However, we expect our pilots to behave professionally, without engaging in any intentional crashing, starting engines on the runway, or any other unprofessional activities.

## Ready to get started with ClearFly VA? Follow these steps
    **1.** Visit {fbo.mention} and enter </va flight file:1016059999056826479>.
    **2.** Click on the command that appears and input the necessary information. Then, run the command.
    **3.** Fly your flight with a ClearFly livery (available in <#1041057335449227314> or <#1087399445966110881>).
    **4.** Once you complete your flight, run the command </va flight complete:1016059999056826479> within 24 hours. Otherwise, the flight will be automatically cancelled.

## Wondering what aircraft you can fly?
You can choose any aircraft that has a ClearFly livery, available in <#1041057335449227314> for official paints or in <#1087399445966110881> for community-made liveries. Just be sure you equip your aircraft with a ClearFly livery before taking off. 

Happy flying!
            """,
        )
        vembed2 = discord.Embed(
            title="Recommended add-ons: StableApproach",
            colour=self.color(),
            description="""
## Download
https://forums.x-plane.org/index.php?/files/file/76763-stableapproach-flight-data-monitoring-for-x-plane/ 
## Setup
**1.** Open the StableApproach settings in the plugins menu.
**2.** Open the “Virtual Airline” category.
**3.** Put the text in the box labeled “Virtual Airline”: “ClearFly-Official/StableApproach”. Also copy your User ID, you'll need this later.
**4.** Go to the “Aircraft” tab. Click “Download VA Profile”, and click “Apply + Save”. This will enable StableApproach to use our profile for that aircraft whenever you fly it.
**5.** Use the </va user set_sa_id:1164987729969430603> command and paste the User ID you copied earlier in it.
**6.** That’s it! StableApproach will now download our custom aircraft profiles and send landing reports in <#1013934267966967848>.
        """,
        )
        emb = discord.Embed(
            title="ClearFly VA Official Liveries",
            colour=self.color(),
            description="Below you can find all official ClearFly liveries. Don't see the aircraft you want to fly? Someone might have made it in <#1087399445966110881>!\n\n",
        )

        livs = {
            "Boeing 737-800 by Zibo": "https://drive.google.com/file/d/1bNXkHHlItE-MhfM6Nc-l5-W75zW9thYP/view?usp=share_link",
            "Cessna Citation X by Laminar Research": "https://drive.google.com/file/d/1X4sShTh58rDucdeJQbX1VdkZtqvBXJIQ/view?usp=sharing",
            "Cessna 172SP by Laminar Research": "https://drive.google.com/file/d/1wQgPFIhMJixk3xt2gNrvfa-okTLWIjgv/view?usp=share_link",
            "Cessna 172SP (G1000) by Laminar Research": "https://drive.google.com/file/d/1jGElFWge_vb_6riAol6bnOIos-thwJJA/view?usp=share_link",
            "Cessna 152 by ZL Simulation": "https://drive.google.com/file/d/1JPrYuTcR7k2iga_mQwDz1uvvB95Xygi4/view?usp=sharing",
            "Airbus A330-900neo by X-Works": "https://drive.google.com/file/d/1kFsR6CYRa94e12uZDZ24QeIXX8A6rwiT/view?usp=sharing"
        }

        for name, link in livs.items():
            emb.description += f"- [{name}]({link})\n"

        liv_channel = self.sendable_channel(
            self.get_channel(self.channels.get("va-liveries", 0))
        )
        overv_channel = self.sendable_channel(
            self.get_channel(self.channels.get("va-overview", 0))
        )
        info = self.sendable_channel(self.get_channel(self.channels.get("info", 0)))
        if info and overv_channel and liv_channel:
            await info.purge(check=check)
            await overv_channel.purge(check=check)
            await liv_channel.purge(check=check)
            await info.send(
                embeds=[rembed1, rembed2], view=RulesView(bot=self), file=file1
            )
            await info.send(embeds=[rembed3])
            await overv_channel.send(
                embeds=[vembed, vembed2], view=VAStartView(bot=self)
            )
            await liv_channel.send(embed=emb)
            return True
        else:
            return False

    async def set_theme(self, author: str, theme: int = 0) -> dict[str, bool | list]:
        if not self.is_ready():
            return {"guild_success": False, "failed_roles": list(self.roles.items())}

        async with aiosqlite.connect(DB["main"]) as db:
            await db.execute(
                "UPDATE config SET value = ? WHERE key = 'theme'", (theme,)
            )
            await db.commit()

        self.theme = theme

        role_colors = {
            "*": {0: 0x6DB2D9, 1: 0xFEB32D, 2: 0x00A628},
            "member": {0: 0x2681B4, 1: 0xFD852D, 2: 0x00771D},
        }

        guild = self.get_guild(self.server_id)
        if not guild:
            guild = await self.fetch_guild(self.server_id)

        failed = []
        guild_success = False

        if guild:
            for name, role_id in self.roles.items():
                try:
                    if name == "member":
                        role = guild.get_role(role_id)
                        if role:
                            await role.edit(
                                color=role_colors["member"][self.theme],
                                reason=f"{author} asked for a theme ({self.theme_name}) change.",
                            )
                        else:
                            raise discord.DiscordException("Role not found")

                    elif name != "admin":
                        role = guild.get_role(role_id)
                        if role:
                            await role.edit(
                                color=role_colors["*"][self.theme],
                                reason=f"{author} asked for a theme ({self.theme_name}) change.",
                            )
                        else:
                            raise discord.DiscordException("Role not found")
                except Exception:
                    role = guild.get_role(role_id)
                    if role:
                        failed.append(role.name)
                    else:
                        failed.append("Unknown Role")

            async with aiofiles.open(
                os.path.join("ui", "images", "logo", str(theme), "logo.png"), "rb"
            ) as f:
                data = await f.read()
                await guild.edit(icon=data)
                if self.user:
                    await self.user.edit(avatar=data)

            guild_success = await self.setup_server()

        return {"guild_success": guild_success, "failed_roles": failed}

    async def send_log(self, *args, **kwargs) -> None:
        logs = self.get_channel(self.channels.get("logs", 0))
        if isinstance(logs, discord.TextChannel):
            await logs.send(*args, **kwargs)

    def is_valid_url(self, url: str) -> bool:
        pattern = "(http|https):\/\/([a-zA-Z-0-9]*)\..*"

        return True if re.search(pattern, url) else False

    @property
    def theme_name(self):
        match self.theme:
            case 0:
                return "Default"
            case 1:
                return "Halloween"
            case 2:
                return "Christmas"
            case _:
                return "Unknown"


class RulesView(discord.ui.View):
    def __init__(self, bot: ClearBot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(
        label="I have read and accept the rules",
        custom_id="rulebutton",
        style=discord.ButtonStyle.secondary,
        emoji="<:ClearFly:1054526148576559184>",
    )
    async def button_callback(self, button, interaction):
        guild = self.bot.get_guild(self.bot.server_id)
        if not guild:
            await interaction.response.send_message(
                "Something went wrong while trying to verify your roles...",
                ephemeral=True,
            )
            return

        role = guild.get_role(self.bot.roles.get("member", 0))
        if role in interaction.user.roles:
            await interaction.response.send_message(
                "You already accepted the rules!", ephemeral=True
            )
        else:
            author = interaction.user
            await author.add_roles(role)
            await interaction.response.send_message(
                "Rules accepted, have fun in the server!", ephemeral=True
            )


class VAStartView(discord.ui.View):
    def __init__(self, bot: ClearBot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Start", style=discord.ButtonStyle.green, custom_id="VA:start_button"
    )
    async def start_button_callback(
        self, button: discord.Button, interaction: discord.Interaction
    ):
        user_ids = await self.bot.va.get_users("id")
        if not interaction.user or isinstance(interaction.user, discord.User):
            return
        if str(interaction.user.id) in list(user_ids):
            embed = discord.Embed(
                title="You're already part of the VA!",
                colour=self.bot.color(1),
                description="Joining the VA when you're already in it, is not possible. Flying two aircraft in different parts of the world at the same time is impossible after all.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            guild = self.bot.get_guild(self.bot.server_id)
            if guild:
                role = guild.get_role(self.bot.roles.get("clearfly-pilot", 0))
                if role:
                    await interaction.user.add_roles(role)
            fbo = self.bot.get_channel(self.bot.channels.get("fbo", 0))
            if not isinstance(fbo, discord.TextChannel):
                return

            embed = discord.Embed(
                title="Thanks for joining our VA!",
                colour=self.bot.color(),
                description=f"""
Head over to {fbo.mention} to file your first flight!
*Don't know how to file your first flight? Check the message above!*

**NOTE**: *If you don't file a flight within 24 hours you will be kicked from the VA*""",
            )
            user = {
                "user_id": str(interaction.user.id),
                "sign_time": round(time.time()),
                "is_trial": True,
                "is_ban": False,
            }
            async with aiosqlite.connect(DB["va"]) as db:
                await db.execute(
                    "INSERT INTO users (user_id, sign_time, is_trial, is_ban) VALUES (:user_id, :sign_time, :is_trial, :is_ban)",
                    user,
                )
                await db.commit()
            await interaction.response.send_message(embed=embed, ephemeral=True)
