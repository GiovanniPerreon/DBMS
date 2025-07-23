import discord
import json
import random
import os

DATA_FILE = "gacha_inventory.json"
UNIT_POOL = [
    # Example units, you can expand this list
    {"name": "Slime", "stars": 1},
    {"name": "Goblin", "stars": 2},
    {"name": "Knight", "stars": 3},
    {"name": "Mage", "stars": 4},
    {"name": "Dragon", "stars": 5},
    {"name": "Legendary Hero", "stars": 6},
]
STAR_RATES = [
    (1, 0.40),  # 40% chance for 1-star
    (2, 0.25),  # 25% for 2-star
    (3, 0.15),  # 15% for 3-star
    (4, 0.10),  # 10% for 4-star
    (5, 0.07),  # 7% for 5-star
    (6, 0.03),  # 3% for 6-star
]
SUMMON_COST = 50  # Points per summon

# Load inventory from JSON

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

# Register gacha commands

def register_gacha_commands(client, user_points):
    @client.tree.command(name="summon", description="Summon a random unit using points!")
    async def summon(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        inventory = load_inventory()
        points = user_points.get(user_id, 0)
        if points < SUMMON_COST:
            await interaction.response.send_message(f"❌ Not enough points! You need {SUMMON_COST} points to summon.", ephemeral=True)
            return
        unit = get_random_unit()
        user_points[user_id] -= SUMMON_COST
        # Add unit to inventory
        if user_id not in inventory:
            inventory[user_id] = []
        inventory[user_id].append(unit)
        save_inventory(inventory)
        await interaction.response.send_message(f"✨ You summoned: {unit['name']} ({unit['stars']}⭐)!\n💰 Points left: {user_points[user_id]}", ephemeral=True)

    @client.tree.command(name="inventory", description="Show your summoned units!")
    async def inventory_cmd(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        inventory = load_inventory()
        units = inventory.get(user_id, [])
        if not units:
            await interaction.response.send_message("Your inventory is empty!", ephemeral=True)
            return
        lines = [f"{unit['name']} ({unit['stars']}⭐)" for unit in units]
        await interaction.response.send_message("Your units:\n" + "\n".join(lines), ephemeral=True)

# To use: import and call register_gacha_commands(client, user_points) from your main bot setup
