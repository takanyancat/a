import discord
from discord import app_commands
import json
from io import BytesIO
from discord.ext import commands

# Store backup information securely
backup_info = {}

async def backup_room(guild: discord.Guild):
    """
    Creates a backup of the server roles and channels.
    """
    backup_data = {"roles": [], "channels": []}

    # Backup roles
    for role in guild.roles:
        if role.name != "@everyone":  # Exclude default role
            backup_data["roles"].append({
                "name": role.name,
                "permissions": role.permissions.value,
                "color": role.color.value,
                "mentionable": role.mentionable,
            })

    # Backup channels
    for channel_obj in guild.channels:
        channel_data = {
            "name": channel_obj.name,
            "type": str(channel_obj.type),
            "category": channel_obj.category.name if channel_obj.category else None,
            "permission_overwrites": [],
        }

        # Backup channel permissions
        for target, overwrite in channel_obj.overwrites.items():
            if isinstance(target, discord.Role):
                channel_data["permission_overwrites"].append({
                    "role": target.name,
                    "permissions": {
                        "allow": overwrite.pair()[0].value,
                        "deny": overwrite.pair()[1].value,
                    },
                })

        backup_data["channels"].append(channel_data)

    return backup_data


async def restore_backup(attachment: discord.Attachment, guild: discord.Guild):
    """
    Restores server roles and channels from a backup file.
    """
    try:
        backup_data = json.loads(await attachment.read())

        # Clear existing data
        await clear_existing_data(guild)

        # Restore roles
        for role_data in backup_data["roles"]:
            await guild.create_role(
                name=role_data["name"],
                permissions=discord.Permissions(role_data["permissions"]),
                color=discord.Color(role_data["color"]),
                mentionable=role_data["mentionable"],
            )

        # Restore channels
        for channel_data in backup_data["channels"]:
            if "text" in channel_data["type"]:
                new_channel = await guild.create_text_channel(
                    name=channel_data["name"],
                    category=discord.utils.get(guild.categories, name=channel_data["category"]),
                )
            elif "voice" in channel_data["type"]:
                new_channel = await guild.create_voice_channel(
                    name=channel_data["name"],
                    category=discord.utils.get(guild.categories, name=channel_data["category"]),
                )

            # Restore permissions
            for overwrite_data in channel_data["permission_overwrites"]:
                role = discord.utils.get(guild.roles, name=overwrite_data["role"])
                if role:
                    await new_channel.set_permissions(
                        role,
                        overwrite=discord.PermissionOverwrite.from_pair(
                            discord.Permissions(overwrite_data["permissions"]["allow"]),
                            discord.Permissions(overwrite_data["permissions"]["deny"])
                        )
                    )

        return "Backup restored successfully!"
    except Exception as e:
        return f"Error during restoration: {str(e)}"


async def clear_existing_data(guild: discord.Guild):
    """
    Clears all existing roles and channels in the server.
    """
    for channel in guild.channels:
        try:
            await channel.delete()
        except Exception as e:
            print(f"Channel deletion error: {channel.name} - {e}")

    for role in guild.roles:
        if role.name != "@everyone":  # Exclude default role
            try:
                await role.delete()
            except Exception as e:
                print(f"Role deletion error: {role.name} - {e}")


async def setup_server_backup(bot: commands.Bot):
    @bot.tree.command(name="backup", description="バックアップを作成します。")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup(interaction: discord.Interaction):
        guild = interaction.guild

        # Create the backup data
        backup_data = await backup_room(guild)

        # Save backup data as a JSON file
        backup_file = BytesIO(json.dumps(backup_data, indent=4).encode())
        backup_file.seek(0)

        # Save backup information for validation during restoration
        backup_info[guild.id] = {"channel_id": interaction.channel.id}

        await interaction.response.send_message(
            "バックアップが正常に作成されました！",
            file=discord.File(backup_file, filename=f"backup_{guild.id}.json")
        )

    @bot.tree.command(name="restore", description="バックアップから復元します。")
    @app_commands.checks.has_permissions(administrator=True)
    async def restore(interaction: discord.Interaction, attachment: discord.Attachment):
        guild = interaction.guild

        # Validate that the backup information exists
        if guild.id not in backup_info:
            await interaction.response.send_message("このサーバーのバックアップ情報が見つかりません。", ephemeral=True)
            return

        try:
            result = await restore_backup(attachment, guild)
            await interaction.response.send_message(result, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"復元に失敗しました: {str(e)}", ephemeral=True)