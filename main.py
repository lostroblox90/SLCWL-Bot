import discord
from discord import app_commands

# ================== ID CONFIG ==================

# SSU / SSD
SSU_REQUIRED_ROLE_ID = 1054172988318158949
SSU_SSD_TARGET_CHANNEL_ID = 1203290074645790730  # same for SSU + SSD

# Warrant
CREATE_WARRANT_ROLE_ID = 1380992005089263717
WARRANT_BUTTON_ALLOWED_ROLES = {
    1444775839567708260,
    1444775731031838750,
    1213814988251070525,
}
WARRANT_CHANNEL_ID = 1444673525167161374

# Moderation
MOD_REQUIRED_ROLE_ID = 1207461773532471407
MOD_LOG_CHANNEL_ID = 1347593236952125503

# Citation
CITATION_REQUIRED_ROLE_ID = 1380992005089263717
CITATION_CHANNEL_ID = 1444675977706868879

# Arrest
ARREST_REQUIRED_ROLE_ID = 1380992005089263717
ARREST_CHANNEL_ID = 1444676107768041574

# ================== HELPERS ==================


def has_role_or_admin(member: discord.Member, role_id: int) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(role.id == role_id for role in member.roles)


# ================== WARRANT VIEW ==================


class WarrantView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _button_permission_check(self, interaction: discord.Interaction) -> bool:
        member = interaction.user

        if not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Could not verify your roles.",
                ephemeral=True,
            )
            return False

        # Admin bypass
        if member.guild_permissions.administrator:
            return True

        # Check allowed roles
        has_role = any(role.id in WARRANT_BUTTON_ALLOWED_ROLES for role in member.roles)
        if not has_role:
            await interaction.response.send_message(
                "You do not have permission to approve or deny warrants.",
                ephemeral=True,
            )
            return False

        return True

    def _disable_buttons(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(
        label="Approve",
        style=discord.ButtonStyle.success,
        custom_id="warrant_approve",
    )
    async def approve_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not await self._button_permission_check(interaction):
            return

        if not interaction.message.embeds:
            await interaction.response.send_message(
                "No embed found to update.",
                ephemeral=True,
            )
            return

        embed = interaction.message.embeds[0].copy()
        embed.color = discord.Color.green()
        embed.set_author(
            name=f"Warrant Approved by {interaction.user.display_name}"
        )

        self._disable_buttons()
        await interaction.message.edit(embed=embed, view=self)

        await interaction.response.send_message(
            "Warrant approved.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Deny",
        style=discord.ButtonStyle.danger,
        custom_id="warrant_deny",
    )
    async def deny_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not await self._button_permission_check(interaction):
            return

        if not interaction.message.embeds:
            await interaction.response.send_message(
                "No embed found to update.",
                ephemeral=True,
            )
            return

        embed = interaction.message.embeds[0].copy()
        embed.color = discord.Color.red()
        embed.set_author(
            name=f"Warrant Denied by {interaction.user.display_name}"
        )

        self._disable_buttons()
        await interaction.message.edit(embed=embed, view=self)

        await interaction.response.send_message(
            "Warrant denied.",
            ephemeral=True,
        )


# ================== MODERATION CONFIRM VIEWS ==================


class DeleteConfirmView(discord.ui.View):
    def __init__(self, log_channel_id: int, message_id: int, invoker: discord.Member):
        super().__init__(timeout=60)
        self.log_channel_id = log_channel_id
        self.message_id = message_id
        self.invoker_id = invoker.id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.invoker_id:
            await interaction.response.send_message(
                "You are not allowed to interact with this confirmation.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Confirm Delete", style=discord.ButtonStyle.danger)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "Guild not found.",
                ephemeral=True,
            )
            return

        channel = guild.get_channel(self.log_channel_id)
        if channel is None:
            await interaction.response.send_message(
                "Log channel not found.",
                ephemeral=True,
            )
            return

        try:
            msg = await channel.fetch_message(self.message_id)
        except discord.NotFound:
            await interaction.response.send_message(
                "That moderation log message no longer exists.",
                ephemeral=True,
            )
            return

        await msg.delete()
        await interaction.response.edit_message(
            content="Moderation log deleted.",
            view=None,
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            content="Moderation delete cancelled.",
            view=None,
        )


class EditConfirmView(discord.ui.View):
    def __init__(
        self,
        log_channel_id: int,
        message_id: int,
        invoker: discord.Member,
        new_type: str,
        new_reason: str,
    ):
        super().__init__(timeout=60)
        self.log_channel_id = log_channel_id
        self.message_id = message_id
        self.invoker_id = invoker.id
        self.new_type = new_type
        self.new_reason = new_reason

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.invoker_id:
            await interaction.response.send_message(
                "You are not allowed to interact with this confirmation.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Confirm Edit", style=discord.ButtonStyle.success)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "Guild not found.",
                ephemeral=True,
            )
            return

        channel = guild.get_channel(self.log_channel_id)
        if channel is None:
            await interaction.response.send_message(
                "Log channel not found.",
                ephemeral=True,
            )
            return

        try:
            msg = await channel.fetch_message(self.message_id)
        except discord.NotFound:
            await interaction.response.send_message(
                "That moderation log message no longer exists.",
                ephemeral=True,
            )
            return

        if not msg.embeds:
            await interaction.response.send_message(
                "That message does not contain an embed.",
                ephemeral=True,
            )
            return

        embed = msg.embeds[0]

        new_embed = discord.Embed(title=embed.title, color=embed.color)

        roblox_username = ""
        moderator = ""

        for field in embed.fields:
            if field.name == "Roblox Username":
                roblox_username = field.value
            if field.name == "Moderator":
                moderator = field.value

        new_embed.add_field(
            name="Roblox Username",
            value=roblox_username or "Unknown",
            inline=False,
        )
        new_embed.add_field(name="Type", value=self.new_type, inline=False)
        new_embed.add_field(name="Reason", value=self.new_reason, inline=False)
        new_embed.add_field(
            name="Moderator", value=moderator or "Unknown", inline=False
        )

        if embed.footer and embed.footer.text:
            new_embed.set_footer(text=embed.footer.text)

        await msg.edit(embed=new_embed)

        await interaction.response.edit_message(
            content="Moderation log updated.",
            view=None,
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            content="Moderation edit cancelled.",
            view=None,
        )


# ================== BOT CORE ==================


class ManagementBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f"Logged in as {self.user} (SLCWL Management)")
        self.add_view(WarrantView())  # persistent warrant buttons
        await self.tree.sync()
        print("Slash commands synced.")


bot = ManagementBot()

# ================== SSU / SSD ==================


@bot.tree.command(name="ssu", description="Send the SSU announcement.")
async def ssu(interaction: discord.Interaction):
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

    if not has_role_or_admin(member, SSU_REQUIRED_ROLE_ID):
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True,
        )
        return

    channel = interaction.guild.get_channel(SSU_SSD_TARGET_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message(
            "Could not find the SSU announcement channel.",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title="Server Start-Up",
        description=(
            "Our whitelisted server has now started up. We highly recommend you review our "
            "<#1213248186513363004> prior to joining.\n"
            "\n"
            "**Server Name:** Salt Lake City Whitelisted"
            "**Code:** slcwl\n"
            "\n"
            "If you have voted, you have **15 minutes** to join or you will face moderation actions. "
            "Ensure to join a voice channel as it is required. To join in-game you must be in our Roblox "
            "group found [here](https://www.roblox.com/groups/34003840/Salt-Lake-Whitelisted#!/about)."
        ),
        color=0x2B2D31,
    )

    embed.set_image(
        url="https://media.discordapp.net/attachments/1054189485308518541/1445323712789217352/image.png"
    )
    embed.set_footer(text="Salt Lake City Whitelisted")

    await channel.send(
        content="@everyone",
        embed=embed,
        allowed_mentions=discord.AllowedMentions(everyone=True),
    )

    await interaction.response.send_message(
        f"SSU announcement sent in {channel.mention}.",
        ephemeral=True,
    )


@bot.tree.command(name="ssd", description="Send the SSD announcement.")
async def ssd(interaction: discord.Interaction):
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

    if not has_role_or_admin(member, SSU_REQUIRED_ROLE_ID):
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True,
        )
        return

    channel = interaction.guild.get_channel(SSU_SSD_TARGET_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message(
            "Could not find the SSD announcement channel.",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title="Server Shut Down",
        description=(
            "Our whitelisted server has now concluded operations. We highly recommend you review our "
            "<#1213248186513363004> for future updates.\n"
            "\n"
            "**Server Name:** Salt Lake City Whitelisted"
            "**Code:** slcwl\n"
            "\n"
            "We appreciate everyone who participated in today's session. To continue playing future SSUs, "
            "make sure you remain in our Roblox group found "
            "[here](https://www.roblox.com/groups/34003840/Salt-Lake-Whitelisted#!/about)."
        ),
        color=0x2B2D31,
    )

    embed.set_image(
        url="https://media.discordapp.net/attachments/1054189485308518541/1445323712789217352/image.png"
    )
    embed.set_footer(text="Salt Lake City Whitelisted")

    await channel.send(embed=embed)

    await interaction.response.send_message(
        f"SSD announcement sent in {channel.mention}.",
        ephemeral=True,
    )


# ================== WARRANT COMMANDS ==================


@bot.tree.command(name="warrant", description="Create a warrant request.")
@app_commands.describe(
    suspect_username="Suspect's username",
    charges="List the charges",
)
async def warrant(
    interaction: discord.Interaction, suspect_username: str, charges: str
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command must be used in a server.",
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

    if not has_role_or_admin(member, CREATE_WARRANT_ROLE_ID):
        await interaction.response.send_message(
            "You do not have permission to create warrants.",
            ephemeral=True,
        )
        return

    channel = interaction.guild.get_channel(WARRANT_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message(
            "Could not find the warrant channel.",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        description=(
            f"**User Requested:** {member.mention}\n"
            f"**Suspect's Username:** {suspect_username}\n"
            f"**Charges:** {charges}"
        ),
        color=discord.Color.blurple(),
    )
    embed.set_author(name="Warrant Pending")

    view = WarrantView()

    message = await channel.send(embed=embed, view=view)

    embed.set_footer(text=f"Warrant ID: {message.id}")
    await message.edit(embed=embed)

    await interaction.response.send_message(
        f"Warrant created in {channel.mention}",
        ephemeral=True,
    )


@bot.tree.command(
    name="warrant_lookup",
    description="Look up a warrant by its ID.",
)
@app_commands.describe(
    warrant_id="The Warrant ID found in the embed footer",
)
async def warrant_lookup(interaction: discord.Interaction, warrant_id: str):
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command must be used in a server.",
            ephemeral=True,
        )
        return

    channel = interaction.guild.get_channel(WARRANT_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message(
            "Could not find the warrant channel.",
            ephemeral=True,
        )
        return

    try:
        message = await channel.fetch_message(int(warrant_id))
    except Exception:
        await interaction.response.send_message(
            "No warrant found with that ID.",
            ephemeral=True,
        )
        return

    if not message.embeds:
        await interaction.response.send_message(
            "This message does not contain a valid warrant.",
            ephemeral=True,
        )
        return

    embed = message.embeds[0]

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ================== MODERATION COMMANDS ==================


async def get_mod_log_channel(guild: discord.Guild):
    return guild.get_channel(MOD_LOG_CHANNEL_ID)


@bot.tree.command(
    name="log_moderation",
    description="Log a moderation action for a Roblox user.",
)
@app_commands.describe(
    roblox_username="Roblox username of the user being moderated",
    mod_type="Type of moderation (e.g., Strike 1, Strike 2, Removal)",
    reason="Reason for the moderation action",
)
async def log_moderation(
    interaction: discord.Interaction,
    roblox_username: str,
    mod_type: str,
    reason: str,
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

    if not has_role_or_admin(member, MOD_REQUIRED_ROLE_ID):
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True,
        )
        return

    log_channel = await get_mod_log_channel(interaction.guild)
    if log_channel is None:
        await interaction.response.send_message(
            "Could not find the moderation log channel.",
            ephemeral=True,
        )
        return

    embed = discord.Embed(title="Moderation Log", color=discord.Color.blurple())
    embed.add_field(
        name="Roblox Username", value=roblox_username, inline=False
    )
    embed.add_field(name="Type", value=mod_type, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Moderator", value=member.mention, inline=False)

    message = await log_channel.send(embed=embed)

    embed.set_footer(text=f"Moderation ID: {message.id}")
    await message.edit(embed=embed)

    await interaction.response.send_message(
        f"Moderation logged in {log_channel.mention} with ID {message.id}.",
        ephemeral=True,
    )


@bot.tree.command(
    name="moderation_logs",
    description="View moderation logs for a Roblox user.",
)
@app_commands.describe(
    roblox_username="Roblox username to search for",
)
async def moderation_logs(
    interaction: discord.Interaction, roblox_username: str
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

    if not has_role_or_admin(member, MOD_REQUIRED_ROLE_ID):
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True,
        )
        return

    log_channel = await get_mod_log_channel(interaction.guild)
    if log_channel is None:
        await interaction.response.send_message(
            "Could not find the moderation log channel.",
            ephemeral=True,
        )
        return

    roblox_lower = roblox_username.lower()
    matches = []

    async for msg in log_channel.history(limit=1000):
        if not msg.embeds:
            continue
        embed = msg.embeds[0]
        for field in embed.fields:
            if (
                field.name == "Roblox Username"
                and field.value.lower() == roblox_lower
            ):
                case_id = msg.id
                mod_type = next(
                    (f.value for f in embed.fields if f.name == "Type"),
                    "Unknown",
                )
                reason = next(
                    (f.value for f in embed.fields if f.name == "Reason"),
                    "Unknown",
                )
                moderator = next(
                    (f.value for f in embed.fields if f.name == "Moderator"),
                    "Unknown",
                )
                matches.append(
                    (case_id, mod_type, reason, moderator, msg.jump_url)
                )
                break

    if not matches:
        await interaction.response.send_message(
            f"No moderation logs found for Roblox user '{roblox_username}'.",
            ephemeral=True,
        )
        return

    lines = [f"Moderation logs for Roblox user '{roblox_username}':", ""]
    for case_id, mod_type, reason, moderator, jump_url in matches:
        lines.append(f"ID: {case_id}")
        lines.append(f"Type: {mod_type}")
        lines.append(f"Reason: {reason}")
        lines.append(f"Moderator: {moderator}")
        lines.append(f"Link: {jump_url}")
        lines.append("")

    text = "\n".join(lines)

    await interaction.response.send_message(text, ephemeral=True)


@bot.tree.command(
    name="moderation_delete",
    description="Delete a moderation log by its ID.",
)
@app_commands.describe(
    moderation_id="The Moderation ID (shown in the log footer)",
)
async def moderation_delete(
    interaction: discord.Interaction, moderation_id: str
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

    if not has_role_or_admin(member, MOD_REQUIRED_ROLE_ID):
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True,
        )
        return

    log_channel = await get_mod_log_channel(interaction.guild)
    if log_channel is None:
        await interaction.response.send_message(
            "Could not find the moderation log channel.",
            ephemeral=True,
        )
        return

    try:
        msg = await log_channel.fetch_message(int(moderation_id))
    except Exception:
        await interaction.response.send_message(
            "No moderation log found with that ID.",
            ephemeral=True,
        )
        return

    if not msg.embeds:
        await interaction.response.send_message(
            "That message does not contain a moderation embed.",
            ephemeral=True,
        )
        return

    embed = msg.embeds[0]
    summary = [f"Moderation ID: {moderation_id}"]
    for field in embed.fields:
        summary.append(f"{field.name}: {field.value}")

    text = "\n".join(summary)

    view = DeleteConfirmView(MOD_LOG_CHANNEL_ID, int(moderation_id), member)

    await interaction.response.send_message(
        f"You are about to delete this moderation log:\n\n{text}",
        view=view,
        ephemeral=True,
    )


@bot.tree.command(
    name="moderation_edit",
    description="Edit a moderation log by its ID.",
)
@app_commands.describe(
    moderation_id="The Moderation ID (shown in the log footer)",
    new_type="New moderation type (e.g., Strike 1, Strike 2, Removal)",
    new_reason="New reason for the moderation action",
)
async def moderation_edit(
    interaction: discord.Interaction,
    moderation_id: str,
    new_type: str,
    new_reason: str,
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

    if not has_role_or_admin(member, MOD_REQUIRED_ROLE_ID):
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True,
        )
        return

    log_channel = await get_mod_log_channel(interaction.guild)
    if log_channel is None:
        await interaction.response.send_message(
            "Could not find the moderation log channel.",
            ephemeral=True,
        )
        return

    try:
        msg = await log_channel.fetch_message(int(moderation_id))
    except Exception:
        await interaction.response.send_message(
            "No moderation log found with that ID.",
            ephemeral=True,
        )
        return

    if not msg.embeds:
        await interaction.response.send_message(
            "That message does not contain a moderation embed.",
            ephemeral=True,
        )
        return

    embed = msg.embeds[0]

    summary = [f"Moderation ID: {moderation_id}"]
    for field in embed.fields:
        summary.append(f"{field.name}: {field.value}")
    summary.append("")
    summary.append("New values:")
    summary.append(f"Type: {new_type}")
    summary.append(f"Reason: {new_reason}")

    text = "\n".join(summary)

    view = EditConfirmView(
        MOD_LOG_CHANNEL_ID,
        int(moderation_id),
        member,
        new_type,
        new_reason,
    )

    await interaction.response.send_message(
        f"You are about to edit this moderation log:\n\n{text}",
        view=view,
        ephemeral=True,
    )


# ================== CITATION ==================


@bot.tree.command(
    name="citation_log",
    description="Log a citation for a suspect.",
)
@app_commands.describe(
    suspect_username="Suspect's Roblox username",
    reason="Reason for the citation",
    fine_amount="Fine amount (e.g. 5,000 or 10k)",
)
async def citation_log(
    interaction: discord.Interaction,
    suspect_username: str,
    reason: str,
    fine_amount: str,
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

    if not has_role_or_admin(member, CITATION_REQUIRED_ROLE_ID):
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True,
        )
        return

    channel = interaction.guild.get_channel(CITATION_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message(
            "Could not find the citation log channel.",
            ephemeral=True,
        )
        return

    embed = discord.Embed(title="Citation Log", color=discord.Color.blurple())
    embed.add_field(
        name="Suspect's Roblox Username",
        value=suspect_username,
        inline=False,
    )
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Fine Amount", value=fine_amount, inline=False)
    embed.add_field(
        name="Issuing Officer", value=member.mention, inline=False
    )

    message = await channel.send(embed=embed)

    embed.set_footer(text=f"Citation ID: {message.id}")
    await message.edit(embed=embed)

    await interaction.response.send_message(
        f"Citation logged in {channel.mention} with ID {message.id}.",
        ephemeral=True,
    )


# ================== ARREST ==================


@bot.tree.command(
    name="arrest_log",
    description="Log an arrest for a suspect.",
)
@app_commands.describe(
    suspect_username="Suspect's Roblox username",
    charges="Charges for the arrest (e.g. 1x evasion, 2x reckless driving)",
)
async def arrest_log(
    interaction: discord.Interaction, suspect_username: str, charges: str
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

    if not has_role_or_admin(member, ARREST_REQUIRED_ROLE_ID):
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True,
        )
        return

    channel = interaction.guild.get_channel(ARREST_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message(
            "Could not find the arrest log channel.",
            ephemeral=True,
        )
        return

    embed = discord.Embed(title="Arrest Log", color=discord.Color.blurple())
    embed.add_field(
        name="Suspect's Roblox Username",
        value=suspect_username,
        inline=False,
    )
    embed.add_field(name="Charges", value=charges, inline=False)
    embed.add_field(
        name="Arresting Officer", value=member.mention, inline=False
    )

    message = await channel.send(embed=embed)

    embed.set_footer(text=f"Arrest ID: {message.id}")
    await message.edit(embed=embed)

    await interaction.response.send_message(
        f"Arrest logged in {channel.mention} with ID {message.id}.",
        ephemeral=True,
    )

@bot.tree.command(
    name="most-wanted",
    description="Request a most wanted warrant on a user.",
)
@app_commands.describe(
    roblox_username="Suspect's Roblox username",
    reason="Reason for requesting most wanted status",
)
async def most_wanted(
    interaction: discord.Interaction,
    roblox_username: str,
    reason: str,
):
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command must be used in a server.",
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

    # Permission check: request role or admin
    if not has_role_or_admin(member, MOST_WANTED_REQUEST_ROLE_ID):
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True,
        )
        return

    channel = interaction.guild.get_channel(MOST_WANTED_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message(
            "Could not find the most wanted request channel.",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        description=(
            f"**User Requested:** {member.mention}\n"
            f"**Suspect's Roblox Username:** {roblox_username}\n"
            f"**Reason:** {reason}"
        ),
        color=discord.Color.blurple(),
    )
    embed.set_author(name="Most Wanted Pending")

    view = MostWantedView()

    # Send the main message with buttons
    message = await channel.send(embed=embed, view=view)

    # Put an ID in the footer
    embed.set_footer(text=f"Most Wanted ID: {message.id}")
    await message.edit(embed=embed)

    # Create a thread attached to this message
    thread_name = f"Most Wanted: {roblox_username}"
    thread = await message.create_thread(name=thread_name)

    # Ping the requester in the thread
    await thread.send(f"{member.mention} Discuss this request here.")

    # Acknowledge to the command user (ephemeral)
    await interaction.response.send_message(
        f"Most wanted request created in {channel.mention}.",
        ephemeral=True,
    )



# ================== RUN BOT ==================

import os

if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable not set")
    bot.run(token)



