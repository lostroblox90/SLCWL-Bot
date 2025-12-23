import discord
from discord import app_commands
from discord.ext import tasks
import aiohttp
import os


# ================= CONFIG =================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ERLC_API_KEY = os.getenv("ERLC_API_KEY")

_log_channel = os.getenv("LOG_CHANNEL_ID")
if not _log_channel:
    raise RuntimeError("LOG_CHANNEL_ID not set")

LOG_CHANNEL_ID = int(_log_channel)

# ================= ID CONFIG =================

SSU_REQUIRED_ROLE_ID = 1054172988318158949
SSU_SSD_TARGET_CHANNEL_ID = 1203290074645790730

CREATE_WARRANT_ROLE_ID = 1380992005089263717
WARRANT_BUTTON_ALLOWED_ROLES = {
    1444775839567708260,
    1444775731031838750,
    1213814988251070525,
}
WARRANT_CHANNEL_ID = 1444673525167161374

MOD_REQUIRED_ROLE_ID = 1207461773532471407
MOD_LOG_CHANNEL_ID = 1347593236952125503

CITATION_REQUIRED_ROLE_ID = 1380992005089263717
CITATION_CHANNEL_ID = 1444675977706868879

ARREST_REQUIRED_ROLE_ID = 1380992005089263717
ARREST_CHANNEL_ID = 1444676107768041574

SSUVOTE_REQUIRED_ROLE_IDS = {
    1207461773532471407,
    1054172988318158949,
}

# ================= HELPERS =================

def has_role_or_admin(member: discord.Member, role_id: int) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(role.id == role_id for role in member.roles)

def has_any_role(member: discord.Member, role_ids: set[int]) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(role.id in role_ids for role in member.roles)

# ================= BOT =================

class ManagementBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.last_players = None

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        await self.tree.sync()
        await self.initialize_players()
        poll_players.start()
        print("Bot ready.")

    # ================= ERLC =================

    async def fetch_players(self):
        headers = {"Authorization": f"Bearer {ERLC_API_KEY}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, headers=headers) as resp:
                if resp.status != 200:
                    return set()
                data = await resp.json()
                return set(p["Username"] for p in data)

    async def initialize_players(self):
        self.last_players = await self.fetch_players()

bot = ManagementBot()

# ================= JOIN / LEAVE LOGGER =================

@tasks.loop(seconds=CHECK_INTERVAL)
async def poll_players():
    current = await bot.fetch_players()
    if bot.last_players is None:
        bot.last_players = current
        return

    joined = current - bot.last_players
    left = bot.last_players - current

    channel = bot.get_channel(LOG_CHANNEL_ID)

    for user in joined:
        embed = discord.Embed(
            title="Player Joined",
            description=f"**{user}** has joined the server",
            color=0x2ECC71,
        )
        await channel.send(embed=embed)

    for user in left:
        embed = discord.Embed(
            title="Player Left",
            description=f"**{user}** has left the server",
            color=0xE74C3C,
        )
        await channel.send(embed=embed)

    bot.last_players = current

# ================= SSU / SSD =================

@bot.tree.command(name="ssu", description="Send the SSU announcement.")
async def ssu(interaction: discord.Interaction):
    if not has_role_or_admin(interaction.user, SSU_REQUIRED_ROLE_ID):
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True,
        )
        return

    channel = interaction.guild.get_channel(SSU_SSD_TARGET_CHANNEL_ID)
    embed = discord.Embed(
        title="Server Start-Up",
        description=(
            "Our whitelisted server has now started up. We highly recommend you review our "
            "<#1213248186513363004> prior to joining.\n\n"
            "**Server Name:** Salt Lake City Whitelisted\n"
            "**Code:** slcwl\n\n"
            "If you have voted, you have **15 minutes** to join or you will face moderation actions."
        ),
        color=0x2B2D31,
    )
    embed.set_footer(text="Salt Lake City Whitelisted")
    await channel.send(
        content="@everyone",
        embed=embed,
        allowed_mentions=discord.AllowedMentions(everyone=True),
    )
    await interaction.response.send_message("SSU sent.", ephemeral=True)

@bot.tree.command(name="ssd", description="Send the SSD announcement.")
async def ssd(interaction: discord.Interaction):
    if not has_role_or_admin(interaction.user, SSU_REQUIRED_ROLE_ID):
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True,
        )
        return

    channel = interaction.guild.get_channel(SSU_SSD_TARGET_CHANNEL_ID)
    embed = discord.Embed(
        title="Server Shut Down",
        description="Our whitelisted server has now shut down. Thank you for joining.",
        color=0x2B2D31,
    )
    embed.set_footer(text="Salt Lake City Whitelisted")
    await channel.send(embed=embed)
    await interaction.response.send_message("SSD sent.", ephemeral=True)

# ================= SSU VOTE =================

class SSUVoteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.attendees = set()

    @discord.ui.button(label="Attend Session", style=discord.ButtonStyle.success)
    async def attend(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        uid = interaction.user.id
        if uid in self.attendees:
            self.attendees.remove(uid)
            await interaction.response.send_message(
                "<:whitecheck:1191923481928028200> Sucessfully unmarked your attendance.",
                ephemeral=True,
            )
        else:
            self.attendees.add(uid)
            await interaction.response.send_message(
                "<:whitecheck:1191923481928028200> Successfully marked your attendance..",
                ephemeral=True,
            )

@bot.tree.command(
    name="ssu_vote",
    description="Start a session vote.",
)
@app_commands.describe(
    session_time="Enter the time using a timestamp generator.",
)
async def ssu_vote(
    interaction: discord.Interaction,
    session_time: str,
):
    if not has_any_role(interaction.user, SSUVOTE_REQUIRED_ROLE_IDS):
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title="Session Vote",
        description=(
            "A session vote is being held. The time for the session is listed below. "
            "If you plan to attend, please use the green button listed below to mark your attendance. "
            "If you fail to join the session within **15** minutes of it starting after voting, you will be moderated."
        ),
        color=0x232428,
    )
    embed.add_field(
        name="Session Time",
        value=session_time,
        inline=False,
    )

    msg = await interaction.channel.send(
        embed=embed,
        view=SSUVoteView(),
    )

    embed.set_footer(text=f"Session Vote ID: {msg.id}")
    await msg.edit(embed=embed)

    await interaction.response.send_message(
        "Successfully ran the session vote command.",
        ephemeral=True,
    )

# ================= RUN =================

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN not set")
    bot.run(DISCORD_TOKEN)










