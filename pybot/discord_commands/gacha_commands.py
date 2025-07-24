import discord
from discord import app_commands
import json
import random
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
POINTS_FILE = os.path.join(DATA_DIR, "points_data.json")
DATA_FILE = os.path.join(DATA_DIR, "gacha_inventory.json")
UNIT_POOL = [
    {
        "name": "Slime",
        "stars": 1,
        "image": "images/Slime.png",
        "stats": {"HP": 50, "ATK": 10, "DEF": 5},
        "ability": "Sticky Body: Double Defence."
    },
    {
        "name": "Goblin",
        "stars": 2,
        "image": "images/Goblin.png",
        "stats": {"HP": 80, "ATK": 20, "DEF": 10},
        "ability": "Sneak Attack: Deals double damage on first hit."
    },
    {
        "name": "Knight",
        "stars": 3,
        "image": "images/Knight.png",
        "stats": {"HP": 120, "ATK": 35, "DEF": 25},
        "ability": "Shield Wall: Reduces incoming damage by 10."
    },
    {
        "name": "Mage",
        "stars": 4,
        "image": "images/Mage.png",
        "stats": {"HP": 90, "ATK": 50, "DEF": 10},
        "ability": "Arcane Blast: Ignores 50% of enemy DEF."
    },
    {
        "name": "Dragon",
        "stars": 5,
        "image": "images/Dragon.png",
        "stats": {"HP": 200, "ATK": 80, "DEF": 40},
        "ability": "Inferno: Deals 30 splash damage to all enemies at the end of the turn."
    },
    {
        "name": "Michael Saves",
        "stars": 6,
        "image": "images/Michael_Saves.png",
        "stats": {"HP": 250, "ATK": 100, "DEF": 60},
        "ability": "America supports Michael Saves: Increases Post Mitigation Damage by 20%." 
    },
]
STAR_RATES = [
    (1, 0.35),  # 35% chance for 1-star
    (2, 0.25),  # 25% for 2-star
    (3, 0.20),  # 20% for 3-star
    (4, 0.12),  # 12% for 4-star
    (5, 0.07),  # 7% for 5-star
    (6, 0.01),  # 1% for 6-star
]
SUMMON_COST = 50  # Points per summon

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
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_inventory(inventory):
    with open(DATA_FILE, "w") as f:
        json.dump(inventory, f)

def get_random_unit():
    roll = random.random()
    cumulative = 0.0
    for stars, rate in STAR_RATES:
        cumulative += rate
        if roll < cumulative:
            candidates = [u for u in UNIT_POOL if u["stars"] == stars]
            return random.choice(candidates)
    return random.choice([u for u in UNIT_POOL if u["stars"] == 1])

def get_unit_image_path(unit):
    # Returns absolute path for unit image, using same logic as DATA_FILE
    path = os.path.join(os.path.dirname(__file__), unit['image'])
    return path

# Register gacha commands

def register_gacha_commands(client, GUILD_ID):
    @client.tree.command(name="all_inventories", description="Show all users' summoned units", guild=GUILD_ID)
    async def all_inventories(interaction: discord.Interaction):
        inventory = load_inventory()
        if not inventory:
            await interaction.response.send_message("No inventories found!", ephemeral=True)
            return
        lines = []
        for user_id, units in inventory.items():
            # Count each unit by name and stars
            unit_counts = {}
            for unit in units:
                key = (unit['name'], unit['stars'])
                unit_counts[key] = unit_counts.get(key, 0) + 1
            unit_lines = [f"{name} ({stars}⭐) x{count}" for (name, stars), count in sorted(unit_counts.items(), key=lambda x: (-x[0][1], x[0][0]))]
            # Try to get user mention if possible
            member = interaction.guild.get_member(int(user_id)) if interaction.guild else None
            user_display = member.mention if member else f"User {user_id}"
            lines.append(f"**{user_display}**\n" + "\n".join(unit_lines))
        await interaction.response.send_message("All Inventories:\n" + "\n\n".join(lines), ephemeral=True)
    class SummonView(discord.ui.View):
        def __init__(self, user_id):
            super().__init__(timeout=60)
            self.user_id = user_id
            self.add_item(SinglePullButton(user_id))
            self.add_item(TenPullButton(user_id))

    class SinglePullButton(discord.ui.Button):
        def __init__(self, user_id):
            super().__init__(label="Single Pull", style=discord.ButtonStyle.primary)
            self.user_id = user_id
        async def callback(self, interaction):
            inventory = load_inventory()
            user_points = load_points()
            points = user_points.get(self.user_id, 0)
            if points < SUMMON_COST:
                await interaction.response.edit_message(content=f"❌ Not enough points! You need {SUMMON_COST} points to summon.", view=SummonView(self.user_id))
                return
            unit = get_random_unit()
            user_points[self.user_id] = points - SUMMON_COST
            save_points(user_points)
            if self.user_id not in inventory:
                inventory[self.user_id] = []
            inventory[self.user_id].append(unit)
            save_inventory(inventory)
            await interaction.response.edit_message(content=f"✨ You summoned: {unit['name']} ({unit['stars']}⭐)!\n💰 Points left: {user_points[self.user_id]}", view=SummonView(self.user_id))

    class TenPullButton(discord.ui.Button):
        def __init__(self, user_id):
            super().__init__(label="10 Pull", style=discord.ButtonStyle.success)
            self.user_id = user_id
        async def callback(self, interaction):
            inventory = load_inventory()
            user_points = load_points()
            points = user_points.get(self.user_id, 0)
            total_cost = SUMMON_COST * 10
            if points < total_cost:
                await interaction.response.edit_message(content=f"❌ Not enough points! You need {total_cost} points for 10 pulls.", view=SummonView(self.user_id))
                return
            results = []
            for _ in range(10):
                unit = get_random_unit()
                results.append(unit)
                if self.user_id not in inventory:
                    inventory[self.user_id] = []
                inventory[self.user_id].append(unit)
            user_points[self.user_id] = points - total_cost
            save_points(user_points)
            save_inventory(inventory)
            lines = [f"{unit['name']} ({unit['stars']}⭐)" for unit in results]
            await interaction.response.edit_message(content=f"✨ 10 Pull Results:\n" + "\n".join(lines) + f"\n💰 Points left: {user_points[self.user_id]}", view=SummonView(self.user_id))

    @client.tree.command(name="summon", description="Open the summon interface", guild=GUILD_ID)
    async def summon(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_points = load_points()
        points = user_points.get(user_id, 0)
        view = SummonView(user_id)
        await interaction.response.send_message(f"Summon Interface:\n💰 Your points: {points}", view=view, ephemeral=True)

    @client.tree.command(name="inventory", description="Show your summoned units!", guild=GUILD_ID)
    async def inventory_cmd(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        inventory = load_inventory()
        units = inventory.get(user_id, [])
        if not units:
            await interaction.response.send_message("Your inventory is empty!", ephemeral=True)
            return
        # Count each unit by name and stars
        unit_counts = {}
        for unit in units:
            key = (unit['name'], unit['stars'])
            unit_counts[key] = unit_counts.get(key, 0) + 1
        lines = [f"{name} ({stars}⭐) x{count}" for (name, stars), count in sorted(unit_counts.items(), key=lambda x: (-x[0][1], x[0][0]))]
        await interaction.response.send_message("Your units:\n" + "\n".join(lines), ephemeral=True)

    @client.tree.command(name="unitinfo", description="Check info for a unit by name", guild=GUILD_ID)
    async def unitinfo(interaction: discord.Interaction, name: str):
        # Case-insensitive search for unit name
        unit = next((u for u in UNIT_POOL if u["name"].lower() == name.lower()), None)
        if not unit:
            await interaction.response.send_message(f"❌ No unit found with name '{name}'.", ephemeral=True)
            return
        embed = discord.Embed(title=f"{unit['name']} ({unit['stars']}⭐)", color=discord.Color.blue())
        image_path = get_unit_image_path(unit)
        
        if os.path.exists(image_path):
            embed.set_image(url=f"attachment://{os.path.basename(image_path)}")
        stats = unit["stats"]
        stats_str = "\n".join([f"**{k}:** {v}" for k, v in stats.items()])
        embed.add_field(name="Stats", value=stats_str, inline=False)
        embed.add_field(name="Ability", value=unit["ability"], inline=False)
        # If image exists, send as file
        if os.path.exists(image_path):
            file = discord.File(image_path, filename=os.path.basename(image_path))
            await interaction.response.send_message(embed=embed, file=file, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
