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
        "ability": "Sticky Body: Double Defence.",
        "spell": "Heal: Restore 30% HP"
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
        "ability": "Shield Wall: Reduces incoming damage by 10.",
        "spell": "Power Surge: Double attack for 1 turn"
    },
    {
        "name": "Mage",
        "stars": 4,
        "image": "images/Mage.png",
        "stats": {"HP": 90, "ATK": 50, "DEF": 10},
        "ability": "Arcane Blast: Ignores 50% of enemy DEF.",
        "spell": "Heal: Restore 30% HP"
    },
    {
        "name": "Dragon",
        "stars": 5,
        "image": "images/Dragon.png",
        "stats": {"HP": 200, "ATK": 80, "DEF": 40},
        "ability": "Inferno: Deals 30 splash damage to all enemies at the end of the turn.",
        "spell": "Fire Breath: Deal damage equal to ATK (reduced by enemy DEF)"
    },
    {
        "name": "Michael Saves",
        "stars": 6,
        "image": "images/Michael_Saves.png",
        "stats": {"HP": 250, "ATK": 100, "DEF": 60},
        "ability": "America supports Michael Saves: Double Post Mitigation Damage.; Sticky Body: Double Defence.",
        "spell": [
            "Heal: Restore 30% HP",
            "Power Surge: Double attack for 1 turn",
            "Stat Boost: Permanently increase all stats by 10"
        ]
    },
    {
        "name": "Shrek",
        "stars": 4,
        "image": "images/Shrek.png",
        "stats": {"HP": 160, "ATK": 45, "DEF": 35},
        "ability": "Get Out Of My Swamp: Reduces enemy ATK by 20%.",
        "spell": [
            "Swamp Heal: Restore 40% HP",
            "Onion Smash: Deal double ATK as damage"
        ]
    },
    {
        "name": "Amongus",
        "stars": 2,
        "image": "images/Amongus.png",
        "stats": {"HP": 70, "ATK": 18, "DEF": 12},
        "ability": "Sus Attack: Has a chance to instantly defeat the enemy.",
        "spell": [
            "Emergency Meeting: Heal 40% HP and gain +10% DEF for 1 turn",
            "Vent: 50% chance to dodge next attack"
        ]
    },
    {
        "name": "Elon Musk",
        "stars": 5,
        "image": "images/Elon_Musk.png",
        "stats": {"HP": 180, "ATK": 65, "DEF": 30},
        "ability": "To The Moon: Deals 15% more damage on attack and Rocket Launch deals bonus damage equal to 100% of ATK.",
        "spell": [
            "Rocket Launch: Deal bonus damage equal to 100% of ATK (ignores DEF)",
            "Dogecoin Pump: Double ATK for 2 turns"
        ]
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
def sync_unit_metadata_to_inventory():
    inventory = load_inventory()
    updated = False
    # Build a lookup for UNIT_POOL by (name, stars)
    pool_lookup = {(u["name"], u["stars"]): u for u in UNIT_POOL}
    for user_id, units in inventory.items():
        for unit in units:
            key = (unit.get("name"), unit.get("stars"))
            pool_unit = pool_lookup.get(key)
            if pool_unit:
                # Sync all non-stat fields (skip 'stats')
                for field in pool_unit:
                    if field != "stats" and unit.get(field) != pool_unit[field]:
                        unit[field] = pool_unit[field]
                        updated = True
    if updated:
        save_inventory(inventory)
        print("Synced all non-stat fields from UNIT_POOL to inventory units.")
    else:
        print("No inventory units needed updating.")
# Register gacha commands

def register_gacha_commands(client, GUILD_ID):
    @client.tree.command(name="buff_all_units", description="Buff all units in your inventory by combining duplicates!", guild=GUILD_ID)
    async def buff_all_units(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        inventory = load_inventory()
        user_units = inventory.get(user_id, [])
        # Group units by (name, stars)
        groups = {}
        for u in user_units:
            key = (u['name'].lower(), u['stars'])
            groups.setdefault(key, []).append(u)
        buffed_any = False
        messages = []
        new_units = user_units.copy()
        for (name, stars), matches in groups.items():
            if len(matches) < 2:
                continue
            buffed_any = True
            to_buff = matches[0]
            num_to_remove = len(matches) - 1
            # Remove all but one from inventory
            removed = 0
            temp_units = []
            for u in new_units:
                if u is to_buff:
                    temp_units.append(u)
                elif u['name'].lower() == name and u['stars'] == stars and removed < num_to_remove:
                    removed += 1
                    continue
                else:
                    temp_units.append(u)
            new_units = temp_units
            # Buff: for each unit being combined, randomly select a stat and add stars to to_buff
            stat_increases = {"HP": 0, "ATK": 0, "DEF": 0}
            for _ in range(num_to_remove):
                stat = random.choice(["HP", "ATK", "DEF"])
                stat_increases[stat] += stars
            # Apply buffs and build message
            buff_msgs = []
            for stat in ["HP", "ATK", "DEF"]:
                if stat_increases[stat] > 0:
                    old_val = to_buff["stats"][stat] - stat_increases[stat]
                    new_val = to_buff["stats"][stat]
                    to_buff["stats"][stat] += stat_increases[stat]
                    buff_msgs.append(f"{stat} +{stat_increases[stat]}")
            messages.append(f"{to_buff['name']} ({stars}⭐): {'; '.join(buff_msgs)} (combined {len(matches)} copies)")
        if not buffed_any:
            await interaction.response.send_message("❌ You need at least two of a unit (same name and star) to buff anything!", ephemeral=True)
            return
        inventory[user_id] = new_units
        save_inventory(inventory)
        await interaction.response.send_message(
            "✨ Buff results for all units:\n" + "\n".join(messages), ephemeral=True
        )
    @client.tree.command(name="strongest_units", description="Show your strongest unit for each name", guild=GUILD_ID)
    async def strongest_units(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        inventory = load_inventory()
        units = inventory.get(user_id, [])
        if not units:
            await interaction.response.send_message("Your inventory is empty!", ephemeral=True)
            return
        # Find strongest unit for each name (by total stats)
        best_units = {}
        for unit in units:
            name = unit["name"]
            total_stats = sum(unit["stats"].values())
            if name not in best_units or total_stats > sum(best_units[name]["stats"].values()):
                best_units[name] = unit
        # Build response
        lines = []
        for name, unit in sorted(best_units.items(), key=lambda x: (-x[1]["stars"], x[0])):
            stats_str = ", ".join([f"{k}: {v}" for k, v in unit["stats"].items()])
            lines.append(f"{name} ({unit['stars']}⭐): {stats_str}")
        await interaction.response.send_message("Your strongest units:\n" + "\n".join(lines), ephemeral=True)
    @client.tree.command(name="buff_unit", description="Combine all identical units (by name and star) to buff one!", guild=GUILD_ID)
    @app_commands.describe(name="Name of the unit to buff (case-insensitive)")
    async def buff_unit(interaction: discord.Interaction, name: str):
        user_id = str(interaction.user.id)
        inventory = load_inventory()
        user_units = inventory.get(user_id, [])
        # Group units by (name, stars)
        groups = {}
        for u in user_units:
            if u['name'].lower() == name.lower():
                key = u['stars']
                groups.setdefault(key, []).append(u)
        buffed_any = False
        messages = []
        new_units = user_units.copy()
        for stars, matches in groups.items():
            if len(matches) < 2:
                continue
            buffed_any = True
            to_buff = matches[0]
            num_to_remove = len(matches) - 1
            # Remove all but one from inventory
            removed = 0
            temp_units = []
            for u in new_units:
                if u is to_buff:
                    temp_units.append(u)
                elif u['name'].lower() == name.lower() and u['stars'] == stars and removed < num_to_remove:
                    removed += 1
                    continue
                else:
                    temp_units.append(u)
            new_units = temp_units
            # Buff: for each unit being combined, randomly select a stat and add stars to to_buff
            stat_increases = {"HP": 0, "ATK": 0, "DEF": 0}
            for _ in range(num_to_remove):
                stat = random.choice(["HP", "ATK", "DEF"])
                stat_increases[stat] += stars
            # Apply buffs and build message
            buff_msgs = []
            for stat in ["HP", "ATK", "DEF"]:
                if stat_increases[stat] > 0:
                    old_val = to_buff["stats"][stat] - stat_increases[stat]
                    new_val = to_buff["stats"][stat]
                    to_buff["stats"][stat] += stat_increases[stat]
                    buff_msgs.append(f"{stat} +{stat_increases[stat]}")
            messages.append(f"{name} ({stars}⭐): {'; '.join(buff_msgs)} (combined {len(matches)} copies)")
        if not buffed_any:
            await interaction.response.send_message("❌ You need at least two of a unit (same name and star) to buff!", ephemeral=True)
            return
        inventory[user_id] = new_units
        save_inventory(inventory)
        await interaction.response.send_message(
            "✨ Buff results:\n" + "\n".join(messages), ephemeral=True
        )
    @client.tree.command(name="all_inventories", description="Show all users' summoned units", guild=GUILD_ID)
    async def all_inventories(interaction: discord.Interaction):
        # Sync all non-stat fields before displaying inventories
        sync_unit_metadata_to_inventory()
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
            self.add_item(HundredPullButton(user_id))
            self.add_item(ThousandPullButton(user_id))

    class ThousandPullButton(discord.ui.Button):
        def __init__(self, user_id):
            super().__init__(label="1000 Pull", style=discord.ButtonStyle.danger)
            self.user_id = user_id
        async def callback(self, interaction):
            inventory = load_inventory()
            user_points = load_points()
            points = user_points.get(self.user_id, 0)
            total_cost = SUMMON_COST * 1000
            if points < total_cost:
                await interaction.response.edit_message(content=f"❌ Not enough points! You need {total_cost} points for 1000 pulls.", view=SummonView(self.user_id))
                return
            results = []
            for _ in range(1000):
                unit = get_random_unit()
                results.append(unit)
                if self.user_id not in inventory:
                    inventory[self.user_id] = []
                inventory[self.user_id].append(unit)
            user_points[self.user_id] = points - total_cost
            save_points(user_points)
            save_inventory(inventory)
            # Show a summary by unit name and stars
            summary = {}
            for unit in results:
                key = (unit['name'], unit['stars'])
                summary[key] = summary.get(key, 0) + 1
            lines = [f"{name} ({stars}⭐) x{count}" for (name, stars), count in sorted(summary.items(), key=lambda x: (-x[0][1], x[0][0]))]
            await interaction.response.edit_message(content=f"✨ 1000 Pull Results:\n" + "\n".join(lines) + f"\n💰 Points left: {user_points[self.user_id]}", view=SummonView(self.user_id))

    class HundredPullButton(discord.ui.Button):
        def __init__(self, user_id):
            super().__init__(label="100 Pull", style=discord.ButtonStyle.danger)
            self.user_id = user_id
        async def callback(self, interaction):
            inventory = load_inventory()
            user_points = load_points()
            points = user_points.get(self.user_id, 0)
            total_cost = SUMMON_COST * 100
            if points < total_cost:
                await interaction.response.edit_message(content=f"❌ Not enough points! You need {total_cost} points for 100 pulls.", view=SummonView(self.user_id))
                return
            results = []
            for _ in range(100):
                unit = get_random_unit()
                results.append(unit)
                if self.user_id not in inventory:
                    inventory[self.user_id] = []
                inventory[self.user_id].append(unit)
            user_points[self.user_id] = points - total_cost
            save_points(user_points)
            save_inventory(inventory)
            # Show a summary by unit name and stars
            summary = {}
            for unit in results:
                key = (unit['name'], unit['stars'])
                summary[key] = summary.get(key, 0) + 1
            lines = [f"{name} ({stars}⭐) x{count}" for (name, stars), count in sorted(summary.items(), key=lambda x: (-x[0][1], x[0][0]))]
            await interaction.response.edit_message(content=f"✨ 100 Pull Results:\n" + "\n".join(lines) + f"\n💰 Points left: {user_points[self.user_id]}", view=SummonView(self.user_id))

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
        # Add Spells field if present
        spell_field = unit.get("spell")
        if spell_field:
            if isinstance(spell_field, list):
                spells_str = "\n".join(spell_field)
            else:
                spells_str = spell_field
            embed.add_field(name="Spells", value=spells_str, inline=False)
        # If image exists, send as file
        if os.path.exists(image_path):
            file = discord.File(image_path, filename=os.path.basename(image_path))
            await interaction.response.send_message(embed=embed, file=file, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
