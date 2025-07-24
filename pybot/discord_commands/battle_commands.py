import discord
import random
import os
import json
import asyncio
from discord import app_commands
from discord.ui import View, Button

from .gacha_commands import UNIT_POOL


# --- Boss System Integration ---
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
BOSS_FILE = os.path.join(DATA_DIR, "boss_data.json")

def load_boss():
    if os.path.exists(BOSS_FILE):
        with open(BOSS_FILE, "r") as f:
            return json.load(f)
    # Pick a random unit and buff it
    boss_unit = random.choice(UNIT_POOL).copy()
    boss_unit["stats"] = boss_unit["stats"].copy()
    for stat in boss_unit["stats"]:
        boss_unit["stats"][stat] = int(boss_unit["stats"][stat] * 10)
    boss = {
        "name": boss_unit["name"],
        "stars": boss_unit["stars"],
        "stats": boss_unit["stats"],
        "max_hp": boss_unit["stats"]["HP"],
        "current_hp": boss_unit["stats"]["HP"],
        "image": boss_unit.get("image"),
        "damage_log": [],
        "defeated": False
    }
    with open(BOSS_FILE, "w") as f:
        json.dump(boss, f)
    return boss

def save_boss(boss):
    with open(BOSS_FILE, "w") as f:
        json.dump(boss, f)

# --- Battle System Core ---
class BattleUnit:
    def __init__(self, unit_data):
        self.name = unit_data['name']
        self.stars = unit_data['stars']
        self.stats = unit_data['stats'].copy()
        self.ability = unit_data['ability']
        self.max_hp = self.stats['HP']
        self.current_hp = self.max_hp
        self.passives = []  # List of passive functions
        self.image = unit_data.get('image')
        # Register passives based on ability string (extendable)
        self.register_passives()

    def register_passives(self):
        # Add passive hooks based on ability name or keywords
        if 'Double Defence' in self.ability or 'Sticky Body' in self.ability:
            self.passives.append(self.sticky_body)
        if 'Reduces incoming damage' in self.ability or 'Shield Wall' in self.ability:
            self.passives.append(self.shield_wall)
        if 'Sneak Attack' in self.ability:
            self.passives.append(self.sneak_attack)
        if 'Arcane Blast' in self.ability:
            self.passives.append(self.arcane_blast)
        if 'Inferno' in self.ability:
            self.passives.append(self.inferno)
        if 'America supports Michael Saves' in self.ability:
            self.passives.append(self.america_supports)

    # --- Passive Implementations ---
    def sticky_body(self, trigger, attacker, damage, battle):
        if trigger == 'on_defend':
            reduced = max(0, damage - self.stats['DEF'])
            battle.log.append(f"{self.name}'s Sticky Body activates! DEF doubled, damage reduced to {reduced}.")
            return reduced
        return damage

    def shield_wall(self, trigger, attacker, damage, battle):
        if trigger == 'on_defend':
            reduced = max(0, damage - 10)
            battle.log.append(f"{self.name}'s Shield Wall activates! Damage reduced by 10 to {reduced}.")
            return reduced
        return damage

    def sneak_attack(self, trigger, attacker, damage, battle):
        # Deals double damage on first hit
        if trigger == 'on_attack':
            if not hasattr(self, '_sneak_attack_used'):
                self._sneak_attack_used = True
                doubled = damage * 2
                battle.log.append(f"{self.name}'s Sneak Attack! First hit deals double damage: {doubled}.")
                return doubled
        return damage

    def arcane_blast(self, trigger, attacker, damage, battle):
        # Ignores 50% of enemy DEF
        if trigger == 'on_attack':
            if hasattr(attacker, 'stats') and hasattr(battle, 'units'):
                defender = battle.units[1 - battle.turn]
                orig_def = defender.stats['DEF']
                reduced_def = orig_def * 0.5
                base_damage = max(0, attacker.stats['ATK'] - reduced_def)
                battle.log.append(f"{self.name}'s Arcane Blast! Ignores 50% DEF, damage is {base_damage}.")
                return base_damage
        return damage

    def inferno(self, trigger, attacker, damage, battle):
        # Deals 30 splash damage to all enemies at the end of the turn
        if trigger == 'on_turn_end':
            # Only apply if this unit is the attacker
            if hasattr(self, 'name') and 'Dragon' in self.name:
                for unit in battle.units:
                    if unit is not self:
                        unit.current_hp -= 30
                        battle.log.append(f"{self.name}'s Inferno triggers! Deals 30 splash damage to {unit.name}.")
        return damage

    def america_supports(self, trigger, attacker, damage, battle):
        # Increases post-mitigation damage by 20%
        if trigger == 'on_attack':
            boosted = int(damage * 1.2)
            battle.log.append(f"{self.name}'s America supports Michael Saves! Post-mitigation damage increased by 20%: {damage} → {boosted}.")
            return boosted
        return damage

    def on_attack(self, target, battle):
        # Called when this unit attacks
        damage = max(0, self.stats['ATK'] - target.stats['DEF'])
        # Apply passives that modify outgoing damage
        for passive in self.passives:
            damage = passive('on_attack', self, damage, battle)
        return damage

    def on_defend(self, attacker, damage, battle):
        # Called when this unit is attacked
        for passive in self.passives:
            damage = passive('on_defend', attacker, damage, battle)
        return damage

    def on_turn_start(self, battle):
        # Called at the start of this unit's turn
        pass

    def on_turn_end(self, battle):
        # Called at the end of this unit's turn
        pass

    # Example passive implementations
    def sticky_body(self, trigger, attacker, damage, battle):
        if trigger == 'on_defend':
            # Double DEF for this attack
            return max(0, damage - self.stats['DEF'])
        return damage

    def shield_wall(self, trigger, attacker, damage, battle):
        if trigger == 'on_defend':
            return max(0, damage - 10)
        return damage

class Battle:
    def __init__(self, unit1, unit2):
        self.units = [unit1, unit2]
        self.turn = 0  # 0 or 1
        self.log = []
        # Second player shield: scales with ATK, DEF, HP
        atk = unit2.stats.get('ATK', 0)
        defense = unit2.stats.get('DEF', 0)
        hp = unit2.stats.get('HP', 0)
        shield_val = int(0.2 * (atk + defense) + 0.1 * hp)
        self.second_player_shield = shield_val
        self.second_player_shield_used = False
        self.log.append(f"Second Player Shield: {unit2.name} receives a shield that absorbs the first {shield_val} damage!")

    def next_turn(self):
        attacker = self.units[self.turn]
        defender = self.units[1 - self.turn]
        # Start of turn passives
        attacker.on_turn_start(self)
        defender.on_turn_start(self)
        # Attack phase
        damage = attacker.on_attack(defender, self)
        # Second player shield logic: only applies to unit2 (index 1), only on first hit
        shield_broken = False
        if (self.turn == 0 and not self.second_player_shield_used and self.second_player_shield > 0):
            absorbed = min(damage, self.second_player_shield)
            damage -= absorbed
            self.second_player_shield -= absorbed
            self.second_player_shield_used = True
            if absorbed > 0:
                self.log.append(f"Second Player Shield absorbs {absorbed} damage from the first attack!")
            if self.second_player_shield <= 0:
                shield_broken = True
                self.log.append(f"Second Player Shield is broken!")
        # Passives on defend
        damage = defender.on_defend(attacker, damage, self)
        defender.current_hp -= damage
        self.log.append(f"{attacker.name} attacks {defender.name} for {damage} damage! ({defender.current_hp}/{defender.max_hp} HP left)")
        # End of turn passives
        attacker.on_turn_end(self)
        defender.on_turn_end(self)
        # Special: Dragon's Inferno triggers at end of turn
        if hasattr(attacker, 'passives'):
            for passive in attacker.passives:
                passive('on_turn_end', attacker, 0, self)
        self.turn = 1 - self.turn
        return self.check_winner()

    def check_winner(self):
        if self.units[0].current_hp <= 0:
            return 1  # unit2 wins
        if self.units[1].current_hp <= 0:
            return 0  # unit1 wins
        return None

ACTIVE_UNITS_FILE = os.path.join(os.path.dirname(__file__), "data/active_units.json")
INVENTORY_FILE = os.path.join(os.path.dirname(__file__), "data/gacha_inventory.json")

def load_active_units():
    if os.path.exists(ACTIVE_UNITS_FILE):
        with open(ACTIVE_UNITS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_active_units(active_units):
    with open(ACTIVE_UNITS_FILE, "w") as f:
        json.dump(active_units, f)

def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

async def get_user_unit(user_id):
    active_units = load_active_units()
    inventory = load_inventory()
    user_units = inventory.get(str(user_id), [])
    if not user_units:
        return None
    active = active_units.get(str(user_id))
    if active:
        # Find the first unit in inventory matching the name and stars
        for unit in user_units:
            if unit['name'] == active['name'] and unit['stars'] == active['stars']:
                return unit
    # Default: return first unit
    return user_units[0]

async def get_bot_unit():
    return random.choice(UNIT_POOL)

# Global dict to store ongoing battles: {(channel_id, user_id): Battle}
BATTLES = {}

class BattleView(View):
    def __init__(self, battle, user_id, opponent_id, is_bot=False, show_buttons=True):
        super().__init__(timeout=120)
        self.battle = battle
        self.user_id = user_id
        self.opponent_id = opponent_id
        self.is_bot = is_bot
        self.add_item(AttackButton(self))
        # Add more buttons for abilities, defend, etc.

    async def interaction_check(self, interaction):
        # Only allow the current turn's user to click
        current_turn_user = self.user_id if self.battle.turn == 0 else self.opponent_id
        if str(interaction.user.id) != str(current_turn_user):
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return False
        return True

    def get_unit_image_file(self, unit):
        # Try to resolve image path for the unit
        if hasattr(unit, 'image') and unit.image:
            image_path = os.path.join(os.path.dirname(__file__), unit.image)
            if os.path.exists(image_path):
                return discord.File(image_path, filename=os.path.basename(image_path)), f"attachment://{os.path.basename(image_path)}"
        return None, None

    def get_hp_bar(self, current, maximum, length=16):
        # Unicode block bar: ▰ = filled, ▱ = empty
        if maximum <= 0:
            maximum = 1
        filled = int(length * max(0, current) / maximum)
        empty = length - filled
        return '▰' * filled + '▱' * empty

class AttackButton(Button):
    def __init__(self, battle_view):
        super().__init__(label="Attack", style=discord.ButtonStyle.primary, emoji="⚔️")
        self.battle_view = battle_view

    async def callback(self, interaction):
        battle = self.battle_view.battle
        winner = battle.next_turn()
        log = '\n'.join(battle.log[-1:])
        embed = discord.Embed(title="Battle Turn", description=log)
        unit1 = battle.units[0]
        unit2 = battle.units[1]
        file1, url1 = self.battle_view.get_unit_image_file(unit1)
        file2, url2 = self.battle_view.get_unit_image_file(unit2)
        if url1:
            embed.set_thumbnail(url=url1)
        if url2:
            embed.set_image(url=url2)
        hp_bar1 = self.battle_view.get_hp_bar(unit1.current_hp, unit1.max_hp)
        hp_bar2 = self.battle_view.get_hp_bar(unit2.current_hp, unit2.max_hp)
        label1 = f"Your Unit: {unit1.name} HP"
        if self.battle_view.is_bot:
            label2 = f"Bot Unit: {unit2.name} HP"
        else:
            label2 = f"Opponent Unit: {unit2.name} HP"
        # Add stats to the HP fields
        stats1 = f"ATK: {unit1.stats['ATK']}  DEF: {unit1.stats['DEF']}"
        stats2 = f"ATK: {unit2.stats['ATK']}  DEF: {unit2.stats['DEF']}"
        shield_val = getattr(battle, 'second_player_shield', 0)
        shield_used = getattr(battle, 'second_player_shield_used', False)
        # Always show the starting shield value if it was set (even if not used yet)
        if shield_val > 0 and (not shield_used or (shield_used and shield_val > 0)):
            shield_str = f"\n🛡️ Shield: {shield_val}"
        elif shield_used and shield_val <= 0:
            shield_str = "\n🛡️ Shield Broken!"
        else:
            shield_str = ""
        embed.add_field(name=label1, value=f"{unit1.current_hp}/{unit1.max_hp}\n{hp_bar1}\n{stats1}")
        embed.add_field(name=label2, value=f"{unit2.current_hp}/{unit2.max_hp}\n{hp_bar2}\n{stats2}{shield_str}")
        # Show whose turn it is
        if self.battle_view.is_bot:
            if battle.turn == 0:
                embed.description += f"\nYour turn!"
            else:
                embed.description += f"\nBot is thinking..."
        else:
            turn_user = self.battle_view.user_id if battle.turn == 0 else self.battle_view.opponent_id
            embed.description += f"\n<@{turn_user}>'s turn!"
        files = []
        if file1:
            files.append(file1)
        if file2 and (not file1 or file2.filename != file1.filename):
            files.append(file2)
        # Remove button for the player who shouldn't act
        if winner is not None:
            if self.battle_view.is_bot:
                result = f"{unit1.name} (You) wins!" if winner == 0 else f"{unit2.name} (Bot) wins!"
            else:
                # Get the winner's Discord display name
                winner_id = self.battle_view.user_id if winner == 0 else self.battle_view.opponent_id
                winner_member = interaction.guild.get_member(int(winner_id)) if interaction.guild else None
                winner_name = winner_member.display_name if winner_member else f"<@{winner_id}>"
                result = f"{unit1.name if winner == 0 else unit2.name} ({winner_name}) wins!"
            embed.add_field(name="Result", value=result, inline=False)
            await interaction.response.edit_message(embed=embed, attachments=files, view=None)
            BATTLES.pop((interaction.channel_id, str(self.battle_view.user_id)), None)
            return
        # If bot, handle bot turn
        if self.battle_view.is_bot and battle.turn == 1:
            await interaction.response.edit_message(embed=embed, attachments=files, view=None)
            await asyncio.sleep(1)
            winner = battle.next_turn()
            log2 = '\n'.join(battle.log[-1:])
            embed2 = discord.Embed(title="Battle Turn", description=log2)
            file1b, url1b = self.battle_view.get_unit_image_file(unit1)
            file2b, url2b = self.battle_view.get_unit_image_file(unit2)
            if url1b:
                embed2.set_thumbnail(url=url1b)
            if url2b:
                embed2.set_image(url=url2b)
            hp_bar1b = self.battle_view.get_hp_bar(unit1.current_hp, unit1.max_hp)
            hp_bar2b = self.battle_view.get_hp_bar(unit2.current_hp, unit2.max_hp)
            label1b = f"Your Unit: {unit1.name} HP"
            label2b = f"Bot Unit: {unit2.name} HP"
            stats1b = f"ATK: {unit1.stats['ATK']}  DEF: {unit1.stats['DEF']}"
            stats2b = f"ATK: {unit2.stats['ATK']}  DEF: {unit2.stats['DEF']}"
            embed2.add_field(name=label1b, value=f"{unit1.current_hp}/{unit1.max_hp}\n{hp_bar1b}\n{stats1b}")
            embed2.add_field(name=label2b, value=f"{unit2.current_hp}/{unit2.max_hp}\n{hp_bar2b}\n{stats2b}")
            if winner is not None:
                result = f"{unit1.name} (You) wins!" if winner == 0 else f"{unit2.name} (Bot) wins!"
                embed2.add_field(name="Result", value=result, inline=False)
                await interaction.edit_original_response(embed=embed2, attachments=[f for f in [file1b, file2b] if f], view=None)
                BATTLES.pop((interaction.channel_id, str(self.battle_view.user_id)), None)
                return
            embed2.description += "\nYour turn!"
            await interaction.edit_original_response(embed=embed2, attachments=[f for f in [file1b, file2b] if f], view=BattleView(battle, self.battle_view.user_id, self.battle_view.opponent_id, is_bot=True, show_buttons=True))
        else:
            # PvP: Only show button to the player whose turn it is
            turn_user = self.battle_view.user_id if battle.turn == 0 else self.battle_view.opponent_id
            show_buttons = str(interaction.user.id) == str(turn_user)
            await interaction.response.edit_message(embed=embed, attachments=files, view=BattleView(battle, self.battle_view.user_id, self.battle_view.opponent_id, is_bot=self.battle_view.is_bot, show_buttons=show_buttons))

def register_battle_commands(client, GUILD_ID):
    @client.tree.command(name="set_active_unit", description="Set your active unit for battle", guild=GUILD_ID)
    @app_commands.describe(name="Name of the unit to set active (case-insensitive)")
    async def set_active_unit(interaction: discord.Interaction, name: str):
        user_id = str(interaction.user.id)
        inventory = load_inventory()
        user_units = inventory.get(user_id, [])
        # Find by name (case-insensitive)
        chosen = next((u for u in user_units if u['name'].lower() == name.lower()), None)
        if not chosen:
            await interaction.response.send_message(f"❌ You don't own a unit named '{name}'.", ephemeral=True)
            return
        active_units = load_active_units()
        active_units[user_id] = {"name": chosen['name'], "stars": chosen['stars']}
        save_active_units(active_units)
        await interaction.response.send_message(f"✅ Set your active unit to {chosen['name']} ({chosen['stars']}⭐)", ephemeral=True)

    @client.tree.command(name="fight", description="Fight another player or the bot! (Boss fight if 'bot')", guild=GUILD_ID)
    @app_commands.describe(opponent="@mention a user or type 'bot' to fight the AI/Boss")
    async def fight(interaction: discord.Interaction, opponent: str):
        user_id = str(interaction.user.id)
        if opponent.lower() == 'bot':
            opp_id = 'bot'
            boss = load_boss()
            if boss["defeated"]:
                await interaction.response.send_message("The boss has already been defeated! Wait for a new one.", ephemeral=True)
                return
            # Use persistent boss as the opponent
            opp_unit_data = boss.copy()
            # Use current HP for the boss
            opp_unit_data["stats"] = opp_unit_data["stats"].copy()
            opp_unit_data["stats"]["HP"] = boss["current_hp"]
            is_bot = True
        else:
            if opponent.startswith('<@') and opponent.endswith('>'):
                opp_id = opponent.strip('<@!>')
            elif opponent.isdigit():
                opp_id = opponent
            else:
                await interaction.response.send_message("Please mention a user or type 'bot'!", ephemeral=True)
                return
            opp_unit_data = await get_user_unit(opp_id)
            is_bot = False
        user_unit_data = await get_user_unit(user_id)
        if not user_unit_data or not opp_unit_data:
            await interaction.response.send_message("Both players must have an active unit set!", ephemeral=True)
            return
        unit1 = BattleUnit(user_unit_data)
        unit2 = BattleUnit(opp_unit_data)
        # If boss fight, set boss HP to persistent value
        if is_bot and opponent.lower() == 'bot':
            unit2.current_hp = boss["current_hp"]
            unit2.max_hp = boss["max_hp"]
        battle = Battle(unit1, unit2)
        # Store battle state
        BATTLES[(interaction.channel_id, user_id)] = battle
        # Prepare the initial battle embed (same as AttackButton logic)
        embed = discord.Embed(title="Battle Start!", description='\n'.join(battle.log[-1:]) + f"\n<@{user_id}>'s turn!")
        file1, url1 = BattleView(battle, user_id, opp_id, is_bot=is_bot).get_unit_image_file(unit1)
        file2, url2 = BattleView(battle, user_id, opp_id, is_bot=is_bot).get_unit_image_file(unit2)
        if url1:
            embed.set_thumbnail(url=url1)
        if url2:
            embed.set_image(url=url2)
        hp_bar1 = BattleView(battle, user_id, opp_id, is_bot=is_bot).get_hp_bar(unit1.current_hp, unit1.max_hp)
        hp_bar2 = BattleView(battle, user_id, opp_id, is_bot=is_bot).get_hp_bar(unit2.current_hp, unit2.max_hp)
        label1 = f"Your Unit: {unit1.name} HP"
        label2 = f"Bot Unit: {unit2.name} HP" if is_bot else f"Opponent Unit: {unit2.name} HP"
        stats1 = f"ATK: {unit1.stats['ATK']}  DEF: {unit1.stats['DEF']}"
        stats2 = f"ATK: {unit2.stats['ATK']}  DEF: {unit2.stats['DEF']}"
        shield_val = getattr(battle, 'second_player_shield', 0)
        shield_used = getattr(battle, 'second_player_shield_used', False)
        if shield_val > 0 and (not shield_used or (shield_used and shield_val > 0)):
            shield_str = f"\n🛡️ Shield: {shield_val}"
        elif shield_used and shield_val <= 0:
            shield_str = "\n🛡️ Shield Broken!"
        else:
            shield_str = ""
        embed.add_field(name=label1, value=f"{unit1.current_hp}/{unit1.max_hp}\n{hp_bar1}\n{stats1}")
        embed.add_field(name=label2, value=f"{unit2.current_hp}/{unit2.max_hp}\n{hp_bar2}\n{stats2}{shield_str}")
        files = []
        if file1:
            files.append(file1)
        if file2 and (not file1 or file2.filename != file1.filename):
            files.append(file2)
        await interaction.response.send_message(
            embed=embed,
            files=files,
            view=BattleView(battle, user_id, opp_id, is_bot=is_bot, show_buttons=True),
            ephemeral=False
        )

        # After the battle, update boss HP and handle defeat if boss fight
        if is_bot and opponent.lower() == 'bot':
            # Wait for the battle to finish (handled by UI/buttons)
            # This logic should be triggered after the battle ends, e.g. in AttackButton or similar
            # You may want to move boss HP update logic to where the winner is determined
            pass

# To use: import and call register_battle_commands(client, GUILD_ID) from your main bot setup
