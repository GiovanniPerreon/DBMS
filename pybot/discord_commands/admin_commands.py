import discord

def register_admin_commands(client, GUILD_ID):
    @client.tree.command(name="dm_user", description="Send a direct message to a user", guild=GUILD_ID)
    async def dm_user(interaction: discord.Interaction, user: discord.Member, message: str):
        try:
            await user.send(f"{message}")
            await interaction.response.send_message(f"✅ Message sent!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(f"❌ Cannot send DM to {user.display_name}. They may have DMs disabled.", ephemeral=True)
            print(f"❌ DM failed - {user.display_name} has DMs disabled")
        except Exception as e:
            await interaction.response.send_message(f"❌ Error sending message: {str(e)}", ephemeral=True)
            print(f"❌ DM failed with error: {str(e)}")
