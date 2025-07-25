import os
import json
import discord
from discord import app_commands

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
POINTS_FILE = os.path.join(DATA_DIR, "points_data.json")
INVENTORY_FILE = os.path.join(DATA_DIR, "gacha_inventory.json")
def get_prestige_file():
    return os.path.join(os.path.dirname(__file__), "data/prestige_data.json")
def load_prestige():
    prestige_file = get_prestige_file()
    if os.path.exists(prestige_file):
        with open(prestige_file, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}
def save_prestige(prestige):
    prestige_file = get_prestige_file()
    with open(prestige_file, "w") as f:
        json.dump(prestige, f)
def get_user_prestige(user_id):
    prestige = load_prestige()
    return prestige.get(str(user_id), 0)
def set_user_prestige(user_id, value):
    prestige = load_prestige()
    prestige[str(user_id)] = value
    save_prestige(prestige)
def get_point_multiplier(user_id):
    prestige = get_user_prestige(user_id)
    return 1 + prestige * 0.1  # 10% more points per prestige level
def load_points():
    if os.path.exists(POINTS_FILE):
        with open(POINTS_FILE, "r") as f:
            data = json.load(f)
            return data.get("user_points", {})
    return {}
def save_points(user_points):
    if os.path.exists(POINTS_FILE):
        with open(POINTS_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}
    data["user_points"] = user_points
    with open(POINTS_FILE, "w") as f:
        json.dump(data, f)
def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, "r") as f:
            return json.load(f)
    return {}
def save_inventory(inventory):
    with open(INVENTORY_FILE, "w") as f:
        json.dump(inventory, f)
def register_prestige_commands(client, GUILD_ID):
    class PrestigeConfirmView(discord.ui.View):
        def __init__(self, user_id, cost_points, cost_units, next_level, bonus):
            super().__init__(timeout=30)
            self.user_id = user_id
            self.cost_points = cost_points
            self.cost_units = cost_units
            self.next_level = next_level
            self.bonus = bonus
            self.add_item(PrestigeButton(self))

    class PrestigeButton(discord.ui.Button):
        def __init__(self, parent_view):
            super().__init__(label="Confirm Prestige", style=discord.ButtonStyle.danger)
            self.parent_view = parent_view
        async def callback(self, interaction):
            user_id = str(interaction.user.id)
            if user_id != self.parent_view.user_id:
                await interaction.response.send_message("This button is not for you!", ephemeral=True)
                return
            user_points = load_points()
            inventory = load_inventory()
            points = user_points.get(user_id, 0)
            # Check cost again in case user changed points
            if points < self.parent_view.cost_points:
                await interaction.response.send_message("❌ You no longer meet the prestige cost!", ephemeral=True)
                return
            # Sacrifice required points and delete all units
            user_points[user_id] = points - self.parent_view.cost_points
            inventory[user_id] = []
            save_points(user_points)
            save_inventory(inventory)
            set_user_prestige(user_id, self.parent_view.next_level)
            await interaction.response.edit_message(
                content=(f"🏆 You have prestiged! Prestige Level: {self.parent_view.next_level}\n"
                         f"You now earn {int(self.parent_view.bonus*100)}% points from all sources."),
                view=None)
    @client.tree.command(name="prestige", description="Prestige: Sacrifice points and units to increase your prestige level!", guild=GUILD_ID)
    async def prestige(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        prestige = get_user_prestige(user_id)
        user_points = load_points()
        inventory = load_inventory()
        units = inventory.get(user_id, [])
        points = user_points.get(user_id, 0)
        next_prestige = prestige + 1
        bonus = get_point_multiplier(user_id)
        # Cost: fixed by prestige level
        cost_points = 10000 + (10000 * prestige * 0.10)
        cost_units = 0  # No unit requirement
        cost_str = f"{cost_points} points"
        if points < cost_points:
            await interaction.response.send_message(
                f"❌ You need at least {cost_points} points to prestige!",
                ephemeral=True)
            return
        embed = discord.Embed(title="Prestige Confirmation", color=discord.Color.gold())
        embed.add_field(name="Current Prestige Level", value=str(prestige), inline=True)
        embed.add_field(name="Next Prestige Level", value=str(next_prestige), inline=True)
        embed.add_field(name="Your Current Points", value=str(points), inline=True)
        embed.add_field(name="Total Bonus After Prestige", value=f"{int((1+next_prestige*0.1)*100)}% points", inline=False)
        embed.add_field(name="Cost", value=cost_str, inline=False)
        embed.set_footer(text="Prestiging will consume the required points!")
        view = PrestigeConfirmView(user_id, cost_points, cost_units, next_prestige, 1+next_prestige*0.1)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)