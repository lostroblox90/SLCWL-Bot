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

API_URL = "https://api.policeroleplay.community/v1/server/players"
CHECK_INTERVAL = 20  # seconds

FETCH_REACTIONS_REQUIRED_ROLE_ID = 1207461773532471407

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

# ================= FETCH REACTIONS =================

@bot.tree.command(
    name="fetch_reactions",
    description="Fetch users who reacted to a message and mention them.",
)
@app_commands.describe(
    message_id="The ID of the message to fetch reactions from",
    emoji="The emoji reaction to check (✅ or <:name:id>)",
)
async def fetch_reactions(
    interaction: discord.Interaction,
    message_id: str,
    emoji: str,
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command can only be used in a server.",
            ephemeral=True,
        )
        return

    member = interaction.user
    if not isinstance(member, discord.Member):
        await interaction.response.send_message(
            "Could not verify your roles.",
            ephemeral=True,
        )
        return

    # Role OR admin check
    if not (
        member.guild_permissions.administrator
        or any(role.id == FETCH_REACTIONS_REQUIRED_ROLE_ID for role in member.roles)
    ):
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True,
        )
        return

    # Fetch message from SAME channel
    try:
        message = await interaction.channel.fetch_message(int(message_id))
    except Exception:
        await interaction.response.send_message(
            "Could not find a message with that ID in this channel.",
            ephemeral=True,
        )
        return

    # Find the reaction
    target_reaction = None
    for reaction in message.reactions:
        if str(reaction.emoji) == emoji:
            target_reaction = reaction
            break

    if target_reaction is None:
        await interaction.response.send_message(
            "That reaction was not found on the message.",
            ephemeral=True,
        )
        return

    users = []
    async for user in target_reaction.users():
        if not user.bot:
            users.append(user)

    if not users:
        await interaction.response.send_message(
            "No users have reacted with that emoji.",
            ephemeral=True,
        )
        return

    mentions = " ".join(user.mention for user in users)

    await interaction.response.send_message(
        f"**Users who reacted ({len(users)}):**\n{mentions}",
        ephemeral=True,
    )

# ================= RUN =================

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN not set")
    bot.run(DISCORD_TOKEN)
