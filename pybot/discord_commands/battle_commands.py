import discord
import random
import os
import json
import asyncio
from discord import app_commands
from discord.ui import View, Button, Select

from .gacha_commands import UNIT_POOL

# --- Boss System Integration ---
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
BOSS_FILE = os.path.join(DATA_DIR, "boss_data.json")


def load_boss():
    if os.path.exists(BOSS_FILE):
        with open(BOSS_FILE, "r") as f:
            boss = json.load(f)
            if not boss.get("defeated", False):
                return boss
            # If boss is defeated, delete the file to ensure a fresh boss is created
            try:
                os.remove(BOSS_FILE)
            except Exception:
                pass
    # If no boss file or boss is defeated, spawn a new boss
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
        "ability": boss_unit.get("ability", ""),
        "damage_log": [],
        "defeated": False,
        # Preserve spell data for boss
        "spell": boss_unit.get("spell"),
        "spells": boss_unit.get("spells")
    }
    with open(BOSS_FILE, "w") as f:
        json.dump(boss, f)
    return boss


def save_boss(boss):
    with open(BOSS_FILE, "w") as f:
        json.dump(boss, f)


# --- Battle System Core ---
class BattleUnit:
    def use_spell(self, battle, spell_idx=0):
        # Only allow one spell per turn
        if getattr(self, 'spell_used_this_turn', False):
            battle.log.append(f"{self.name} already cast a spell this turn!")
            return 0
        spells = getattr(self, 'spells', [])
        if not spells or spell_idx >= len(spells):
            battle.log.append(f"{self.name} tried to cast a spell, but has none!")
            return 0
        spell = spells[spell_idx]
        spell_name = spell.split(":")[0].strip().lower()
        # Heal: Restore 30% HP
        if "heal" in spell_name:
            heal_amount = int(self.max_hp * 0.3)
            before = self.current_hp
            self.current_hp = min(self.current_hp + heal_amount, self.max_hp)
            actual_heal = self.current_hp - before
            battle.log.append(f"{self.name} casts Heal and restores {actual_heal} HP! ({self.current_hp}/{self.max_hp} HP)")
            self.spell_used_this_turn = True
            return actual_heal
        # Fire Breath: Deal ATK - DEF damage to enemy
        elif "fire breath" in spell_name:
            # Target is always the other unit
            target = battle.units[1] if battle.units[0] == self else battle.units[0]
            damage = max(0, self.stats['ATK'] - target.stats['DEF'])
            target.current_hp -= damage
            battle.log.append(f"{self.name} uses Fire Breath! Deals {damage} damage to {target.name}. ({target.current_hp}/{target.max_hp} HP left)")
            self.spell_used_this_turn = True
            return damage
        # Power Surge: Double attack for 1 turn
        elif "power surge" in spell_name:
            self._power_surge_active = True
            battle.log.append(f"{self.name} casts Power Surge! Their next attack will deal double damage!")
            self.spell_used_this_turn = True
            return 1
        # Michael Saves: Stat Boost spell
        elif "stat boost" in spell_name or (self.name.lower() == "michael saves" and "boost" in spell_name):
            # Permanently increase all stats by 10
            for stat in self.stats:
                self.stats[stat] += 10
            self.max_hp = self.stats['HP']
            # If current HP was at max, keep it at new max
            if self.current_hp == self.max_hp - 10:
                self.current_hp = self.max_hp
            battle.log.append(f"{self.name} casts Stat Boost! All stats permanently increased by 10! (Now: ATK {self.stats['ATK']}, DEF {self.stats['DEF']}, HP {self.stats['HP']})")
            # --- Make stat boost permanent in inventory or boss file ---
            try:
                # Only make stat boost permanent for player units (not boss)
                # Player is always unit1 (index 0) in battle.units
                if hasattr(battle, 'units') and self is battle.units[0]:
                    from .gacha_commands import load_inventory, save_inventory
                    # Find the user id by searching active_units.json
                    import os, json
                    ACTIVE_UNITS_FILE = os.path.join(os.path.dirname(__file__), "data/active_units.json")
                    if os.path.exists(ACTIVE_UNITS_FILE):
                        with open(ACTIVE_UNITS_FILE, "r") as f:
                            active_units = json.load(f)
                        # Find the user whose active unit matches this one
                        for user_id, active in active_units.items():
                            if active['name'] == self.name and active['stars'] == self.stars:
                                inventory = load_inventory()
                                user_units = inventory.get(user_id, [])
                                for unit in user_units:
                                    if unit['name'] == self.name and unit['stars'] == self.stars:
                                        for stat in self.stats:
                                            unit['stats'][stat] = self.stats[stat]
                                        save_inventory(inventory)
                                        break
            except Exception as e:
                battle.log.append(f"(Permanent stat boost failed to save: {e})")
            self.spell_used_this_turn = True
            return 1
        else:
            battle.log.append(f"{self.name} tried to cast {spell}, but nothing happened.")
            return 0

    def __init__(self, unit_data):
        self.name = unit_data['name']
        self.stars = unit_data['stars']
        self.stats = unit_data['stats'].copy()
        self.ability = unit_data['ability']
        self.max_hp = self.stats['HP']
        self.current_hp = self.max_hp
        self.passives = []  # List of passive functions
        self.image = unit_data.get('image')
        
        # Handle spell data properly
        spell_data = unit_data.get('spell', unit_data.get('spells'))
        if isinstance(spell_data, str):
            self.spells = [spell_data]
        elif isinstance(spell_data, list):
            self.spells = spell_data
        else:
            self.spells = []
            
        # Register passives based on ability string
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
            battle.log.append(
                f"{self.name}'s Sticky Body activates! DEF doubled, damage reduced to {reduced}."
            )
            return reduced
        return damage

    def shield_wall(self, trigger, attacker, damage, battle):
        if trigger == 'on_defend':
            reduced = max(0, damage - 10)
            battle.log.append(
                f"{self.name}'s Shield Wall activates! Damage reduced by 10 to {reduced}."
            )
            return reduced
        return damage

    def sneak_attack(self, trigger, attacker, damage, battle):
        # Deals double damage on first hit
        if trigger == 'on_attack':
            if not hasattr(self, '_sneak_attack_used'):
                self._sneak_attack_used = True
                doubled = damage * 2
                battle.log.append(
                    f"{self.name}'s Sneak Attack! First hit deals double damage: {doubled}."
                )
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
                battle.log.append(
                    f"{self.name}'s Arcane Blast! Ignores 50% DEF, damage is {base_damage}."
                )
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
                        battle.log.append(
                            f"{self.name}'s Inferno triggers! Deals 30 splash damage to {unit.name}."
                        )
        return damage

    def america_supports(self, trigger, attacker, damage, battle):
        # Double post-mitigation damage
        if trigger == 'on_attack':
            boosted = int(damage * 2)
            battle.log.append(
                f"{self.name}'s America supports Michael Saves! Post-mitigation damage DOUBLED: {damage} → {boosted}."
            )
            return boosted
        return damage

    def on_attack(self, target, battle):
        # Called when this unit attacks
        damage = max(0, self.stats['ATK'] - target.stats['DEF'])
        # Power Surge: double damage for one turn if active
        if hasattr(self, '_power_surge_active') and self._power_surge_active:
            damage *= 2
            battle.log.append(f"{self.name}'s Power Surge doubles their attack damage!")
            self._power_surge_active = False
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
        self.spell_used_this_turn = False

    def on_turn_end(self, battle):
        # Called at the end of this unit's turn
        pass


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
        self.log.append(
            f"Second Player Shield: {unit2.name} receives a shield that absorbs the first {shield_val} damage!"
        )

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
        shield_absorbed = 0
        if (self.turn == 0 and not self.second_player_shield_used
                and self.second_player_shield > 0):
            absorbed = min(damage, self.second_player_shield)
            damage -= absorbed
            self.second_player_shield -= absorbed
            shield_absorbed = absorbed
            self.second_player_shield_used = True
            if absorbed > 0:
                self.log.append(
                    f"Second Player Shield absorbs {absorbed} damage from the first attack!"
                )
            if self.second_player_shield <= 0:
                shield_broken = True
                self.log.append(f"Second Player Shield is broken!")
        # Passives on defend
        damage = defender.on_defend(attacker, damage, self)
        defender.current_hp -= damage
        # Recap: show shield absorption if any
        if shield_absorbed > 0:
            self.log.append(
                f"{attacker.name} attacks {defender.name} for {damage} damage! (🛡️ {shield_absorbed} absorbed, {defender.current_hp}/{defender.max_hp} HP left)"
            )
        else:
            self.log.append(
                f"{attacker.name} attacks {defender.name} for {damage} damage! ({defender.current_hp}/{defender.max_hp} HP left)"
            )
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


ACTIVE_UNITS_FILE = os.path.join(os.path.dirname(__file__),
                                 "data/active_units.json")
INVENTORY_FILE = os.path.join(os.path.dirname(__file__),
                              "data/gacha_inventory.json")


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
            if unit['name'] == active['name'] and unit['stars'] == active[
                    'stars']:
                return unit
    # Default: return first unit
    return user_units[0]


async def get_bot_unit():
    return random.choice(UNIT_POOL)


# Global dict to store ongoing battles: {(channel_id, user_id): Battle}
BATTLES = {}


class BattleView(View):
    async def update_battle_embed(self, interaction):
        battle = self.battle
        log = '\n'.join(battle.log[-1:])
        embed = discord.Embed(title="Battle Turn", description=log)
        unit1 = battle.units[0]
        unit2 = battle.units[1]
        file1, url1 = self.get_unit_image_file(unit1)
        file2, url2 = self.get_unit_image_file(unit2)
        if url1:
            embed.set_thumbnail(url=url1)
        if url2:
            embed.set_image(url=url2)
        hp_bar1 = self.get_hp_bar(unit1.current_hp, unit1.max_hp)
        hp_bar2 = self.get_hp_bar(unit2.current_hp, unit2.max_hp)
        label1 = f"Your Unit: {unit1.name} HP"
        label2 = f"Opponent Unit: {unit2.name} HP" if not self.is_bot else f"Bot Unit: {unit2.name} HP"
        stats1 = f"ATK: {unit1.stats['ATK']}  DEF: {unit1.stats['DEF']}"
        stats2 = f"ATK: {unit2.stats['ATK']}  DEF: {unit2.stats['DEF']}"
        shield_val = getattr(battle, 'second_player_shield', 0)
        shield_used = getattr(battle, 'second_player_shield_used', False)
        if not shield_used and shield_val > 0:
            shield_str = f"\n🛡️ Shield: {shield_val}"
        else:
            shield_str = ""
        embed.add_field(name=label1, value=f"{unit1.current_hp}/{unit1.max_hp}\n{hp_bar1}\n{stats1}")
        embed.add_field(name=label2, value=f"{unit2.current_hp}/{unit2.max_hp}\n{hp_bar2}\n{stats2}{shield_str}")
        files = []
        if file1:
            files.append(file1)
        if file2 and (not file1 or file2.filename != file1.filename):
            files.append(file2)
        # Show whose turn it is
        if self.is_bot:
            if battle.turn == 0:
                embed.description += f"\nYour turn!"
            else:
                embed.description += f"\nBot is thinking..."
        else:
            turn_user = self.user_id if battle.turn == 0 else self.opponent_id
            embed.description += f"\n<@{turn_user}>'s turn!"
        await interaction.response.edit_message(embed=embed, attachments=files, view=self)
    def get_hp_bar(self, current, maximum, length=16):
        # Unicode block bar: ▰ = filled, ▱ = empty
        if maximum <= 0:
            maximum = 1
        filled = int(length * max(0, current) / maximum)
        empty = length - filled
        return '▰' * filled + '▱' * empty

    def get_unit_image_file(self, unit):
        # Try to resolve image path for the unit
        if hasattr(unit, 'image') and unit.image:
            image_path = os.path.join(os.path.dirname(__file__), unit.image)
            if os.path.exists(image_path):
                return discord.File(image_path, filename=os.path.basename(image_path)), f"attachment://{os.path.basename(image_path)}"
        return None, None

    def __init__(self,
                 battle,
                 user_id,
                 opponent_id,
                 is_bot=False,
                 show_buttons=True):
        super().__init__(timeout=120)
        self.battle = battle
        self.user_id = user_id
        self.opponent_id = opponent_id
        self.is_bot = is_bot
        
        # Always add AttackButton if show_buttons is True (for the current player)
        if show_buttons:
            self.add_item(AttackButton(self))
        
        # Only add SpellButton if not a boss turn (i.e., not is_bot and it's the boss's turn)
        current_unit = self.battle.units[self.battle.turn]
        spells = getattr(current_unit, 'spells', [])
        # In boss fights, only allow the player to use spells (not the boss)
        if spells and len(spells) > 0:
            if not (self.is_bot and self.battle.turn == 1):
                self.add_item(SpellButton(self, spells))


class SpellButton(Button):
    def __init__(self, battle_view, spells):
        self.battle_view = battle_view
        self.spells = spells
        if len(spells) == 1:
            label = spells[0].split(":")[0].strip()
        else:
            label = "Spell"
        super().__init__(label=label, style=discord.ButtonStyle.success, emoji="✨")

    async def callback(self, interaction):
        # Turn check logic
        battle = self.battle_view.battle
        current_turn_user = self.battle_view.user_id if battle.turn == 0 else self.battle_view.opponent_id
        if str(interaction.user.id) != str(current_turn_user):
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        unit = battle.units[battle.turn]
        if getattr(unit, 'spell_used_this_turn', False):
            await interaction.response.send_message("You already cast a spell this turn!", ephemeral=True)
            return
        if len(self.spells) == 1:
            # Cast the only spell
            await self.cast_spell(interaction, 0)
        else:
            # Show dropdown to pick spell
            await interaction.response.send_message(
                "Choose a spell to cast:",
                view=SpellSelectView(self.battle_view, self.spells, self),
                ephemeral=True
            )

    async def cast_spell(self, interaction, idx):
        battle = self.battle_view.battle
        unit = battle.units[battle.turn]
        spell_name = self.spells[idx]
        # Use the spell
        if hasattr(unit, 'use_spell'):
            unit.use_spell(battle, idx)
        # Update the battle embed
        await self.battle_view.update_battle_embed(interaction)


class SpellSelectView(View):
    def __init__(self, battle_view, spells, spell_button):
        super().__init__(timeout=30)
        self.battle_view = battle_view
        self.spells = spells
        self.spell_button = spell_button
        self.add_item(SpellSelect(self, spells))


class SpellSelect(Select):
    def __init__(self, parent_view, spells):
        options = [discord.SelectOption(label=spell, value=str(i)) for i, spell in enumerate(spells)]
        super().__init__(placeholder="Choose a spell...", min_values=1, max_values=1, options=options)
        self.parent_view = parent_view

    async def callback(self, interaction):
        idx = int(self.values[0])
        await self.parent_view.spell_button.cast_spell(interaction, idx)


class AttackButton(Button):

    def __init__(self, battle_view):
        super().__init__(label="Attack",
                         style=discord.ButtonStyle.primary,
                         emoji="⚔️")
        self.battle_view = battle_view

    async def callback(self, interaction):
        # Turn check logic
        battle = self.battle_view.battle
        current_turn_user = self.battle_view.user_id if battle.turn == 0 else self.battle_view.opponent_id
        if str(interaction.user.id) != str(current_turn_user):
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
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
        # Only show shield on the first turn (before it is used)
        if not shield_used and shield_val > 0:
            shield_str = f"\n🛡️ Shield: {shield_val}"
        else:
            shield_str = ""
        embed.add_field(
            name=label1,
            value=f"{unit1.current_hp}/{unit1.max_hp}\n{hp_bar1}\n{stats1}")
        embed.add_field(
            name=label2,
            value=
            f"{unit2.current_hp}/{unit2.max_hp}\n{hp_bar2}\n{stats2}{shield_str}"
        )
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

        # --- Save boss HP after every turn if boss fight ---
        if self.battle_view.is_bot:
            from .battle_commands import load_boss, save_boss
            boss = load_boss()
            boss["current_hp"] = unit2.current_hp
            save_boss(boss)

        # Remove button for the player who shouldn't act
        if winner is not None:
            if self.battle_view.is_bot:
                result = f"{unit1.name} (You) wins!" if winner == 0 else f"{unit2.name} (Bot) wins!"
                embed.add_field(name="Result", value=result, inline=False)
                await interaction.response.edit_message(embed=embed,
                                                        attachments=files,
                                                        view=None)
                BATTLES.pop(
                    (interaction.channel_id, str(self.battle_view.user_id)),
                    None)
                # If boss was defeated, handle defeat, prize, and respawn immediately
                if winner == 0:  # Player wins
                    from .battle_commands import load_boss, save_boss
                    from .gacha_commands import load_points, save_points
                    boss = load_boss()
                    if not boss["defeated"]:
                        boss["defeated"] = True
                        total_stats = sum(boss["stats"].values())
                        JACKPOT_MULTIPLIER = 10  # Change this value to adjust the multiplier
                        jackpot = int(total_stats * JACKPOT_MULTIPLIER)
                        user_points = load_points()
                        user_points[str(
                            self.battle_view.user_id)] = user_points.get(
                                str(self.battle_view.user_id), 0) + jackpot
                        save_points(user_points)
                        boss["current_hp"] = 0
                        save_boss(boss)
                        # Announce the prize
                        await interaction.followup.send(
                            f"🎉 You defeated the boss and won the jackpot: {jackpot} points! A new boss has appeared!",
                            ephemeral=False)
                        # Spawn a new boss
                        load_boss()
                return
            else:
                # Get the winner's Discord display name
                winner_id = self.battle_view.user_id if winner == 0 else self.battle_view.opponent_id
                winner_member = interaction.guild.get_member(
                    int(winner_id)) if interaction.guild else None
                winner_name = winner_member.display_name if winner_member else f"<@{winner_id}>"
                result = f"{unit1.name if winner == 0 else unit2.name} ({winner_name}) wins!"
                embed.add_field(name="Result", value=result, inline=False)
                await interaction.response.edit_message(embed=embed,
                                                        attachments=files,
                                                        view=None)
                BATTLES.pop(
                    (interaction.channel_id, str(self.battle_view.user_id)),
                    None)
                return

        # If bot, handle bot turn
        if self.battle_view.is_bot and battle.turn == 1:
            await interaction.response.edit_message(embed=embed,
                                                    attachments=files,
                                                    view=BattleView(self.battle_view.battle,
                                                                    self.battle_view.user_id,
                                                                    self.battle_view.opponent_id,
                                                                    is_bot=True,
                                                                    show_buttons=False))
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
            hp_bar1b = self.battle_view.get_hp_bar(unit1.current_hp,
                                                   unit1.max_hp)
            hp_bar2b = self.battle_view.get_hp_bar(unit2.current_hp,
                                                   unit2.max_hp)
            label1b = f"Your Unit: {unit1.name} HP"
            label2b = f"Bot Unit: {unit2.name} HP"
            stats1b = f"ATK: {unit1.stats['ATK']}  DEF: {unit1.stats['DEF']}"
            stats2b = f"ATK: {unit2.stats['ATK']}  DEF: {unit2.stats['DEF']}"
            embed2.add_field(
                name=label1b,
                value=
                f"{unit1.current_hp}/{unit1.max_hp}\n{hp_bar1b}\n{stats1b}")
            embed2.add_field(
                name=label2b,
                value=
                f"{unit2.current_hp}/{unit2.max_hp}\n{hp_bar2b}\n{stats2b}")

            # --- Save boss HP after every bot turn ---
            from .battle_commands import load_boss, save_boss
            boss = load_boss()
            boss["current_hp"] = unit2.current_hp
            save_boss(boss)

            if winner is not None:
                result = f"{unit1.name} (You) wins!" if winner == 0 else f"{unit2.name} (Bot) wins!"
                embed2.add_field(name="Result", value=result, inline=False)
                await interaction.edit_original_response(
                    embed=embed2,
                    attachments=[f for f in [file1b, file2b] if f],
                    view=None)
                BATTLES.pop(
                    (interaction.channel_id, str(self.battle_view.user_id)),
                    None)
                return
            embed2.description += "\nYour turn!"
            # Always reuse the same battle object for the view, so spell button is correct
            await interaction.edit_original_response(
                embed=embed2,
                attachments=[f for f in [file1b, file2b] if f],
                view=BattleView(self.battle_view.battle,
                                self.battle_view.user_id,
                                self.battle_view.opponent_id,
                                is_bot=True,
                                show_buttons=True))
        else:
            # PvP: Only show button to the player whose turn it is
            turn_user = self.battle_view.user_id if battle.turn == 0 else self.battle_view.opponent_id
            show_buttons = str(interaction.user.id) == str(turn_user)
            # Always reuse the same battle object for the view, so spell button is correct
            await interaction.response.edit_message(
                embed=embed,
                attachments=files,
                view=BattleView(self.battle_view.battle,
                                self.battle_view.user_id,
                                self.battle_view.opponent_id,
                                is_bot=self.battle_view.is_bot,
                                show_buttons=show_buttons))

    async def update_battle_embed(self, interaction):
        battle = self.battle
        log = '\n'.join(battle.log[-1:])
        embed = discord.Embed(title="Battle Turn", description=log)
        unit1 = battle.units[0]
        unit2 = battle.units[1]
        file1, url1 = self.get_unit_image_file(unit1)
        file2, url2 = self.get_unit_image_file(unit2)
        if url1:
            embed.set_thumbnail(url=url1)
        if url2:
            embed.set_image(url=url2)
        hp_bar1 = self.get_hp_bar(unit1.current_hp, unit1.max_hp)
        hp_bar2 = self.get_hp_bar(unit2.current_hp, unit2.max_hp)
        label1 = f"Your Unit: {unit1.name} HP"
        label2 = f"Opponent Unit: {unit2.name} HP"
        stats1 = f"ATK: {unit1.stats['ATK']}  DEF: {unit1.stats['DEF']}"
        stats2 = f"ATK: {unit2.stats['ATK']}  DEF: {unit2.stats['DEF']}"
        shield_val = getattr(battle, 'second_player_shield', 0)
        shield_used = getattr(battle, 'second_player_shield_used', False)
        if not shield_used and shield_val > 0:
            shield_str = f"\n🛡️ Shield: {shield_val}"
        else:
            shield_str = ""
        embed.add_field(name=label1, value=f"{unit1.current_hp}/{unit1.max_hp}\n{hp_bar1}\n{stats1}")
        embed.add_field(name=label2, value=f"{unit2.current_hp}/{unit2.max_hp}\n{hp_bar2}\n{stats2}{shield_str}")
        files = []
        if file1:
            files.append(file1)
        if file2 and (not file1 or file2.filename != file1.filename):
            files.append(file2)
        await interaction.response.edit_message(embed=embed, attachments=files, view=self)

    def get_unit_image_file(self, unit):
        # Try to resolve image path for the unit
        if hasattr(unit, 'image') and unit.image:
            image_path = os.path.join(os.path.dirname(__file__), unit.image)
            if os.path.exists(image_path):
                return discord.File(
                    image_path, filename=os.path.basename(image_path)
                ), f"attachment://{os.path.basename(image_path)}"
        return None, None


def register_battle_commands(client, GUILD_ID):

    @client.tree.command(name="set_active_unit",
                         description="Set your active unit for battle",
                         guild=GUILD_ID)
    @app_commands.describe(
        name="Name of the unit to set active (case-insensitive)")
    async def set_active_unit(interaction: discord.Interaction, name: str):
        user_id = str(interaction.user.id)
        inventory = load_inventory()
        user_units = inventory.get(user_id, [])
        # Find by name (case-insensitive)
        chosen = next(
            (u for u in user_units if u['name'].lower() == name.lower()), None)
        if not chosen:
            await interaction.response.send_message(
                f"❌ You don't own a unit named '{name}'.", ephemeral=True)
            return
        active_units = load_active_units()
        active_units[user_id] = {
            "name": chosen['name'],
            "stars": chosen['stars']
        }
        save_active_units(active_units)
        await interaction.response.send_message(
            f"✅ Set your active unit to {chosen['name']} ({chosen['stars']}⭐)",
            ephemeral=True)

    @client.tree.command(
        name="fight",
        description="Fight another player or the Boss! (Boss fight if 'boss')",
        guild=GUILD_ID)
    @app_commands.describe(
        opponent="@mention a user or type 'boss' to fight the AI/Boss")
    async def fight(interaction: discord.Interaction, opponent: str):
        user_id = str(interaction.user.id)
        if opponent.lower() == 'boss':
            opp_id = 'boss'
            boss = load_boss()
            if boss["defeated"]:
                # Respawn a new boss automatically
                boss = load_boss()
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
                await interaction.response.send_message(
                    "Please mention a user or type 'boss'!", ephemeral=True)
                return
            opp_unit_data = await get_user_unit(opp_id)
            is_bot = False
        user_unit_data = await get_user_unit(user_id)
        if not user_unit_data or not opp_unit_data:
            await interaction.response.send_message(
                "Both players must have an active unit set!", ephemeral=True)
            return
        unit1 = BattleUnit(user_unit_data)
        unit2 = BattleUnit(opp_unit_data)
        # If boss fight, set boss HP to persistent value
        if is_bot and opponent.lower() == 'boss':
            unit2.current_hp = boss["current_hp"]
            unit2.max_hp = boss["max_hp"]
        battle = Battle(unit1, unit2)
        # Store battle state
        BATTLES[(interaction.channel_id, user_id)] = battle
        # Prepare the initial battle embed (same as AttackButton logic)
        embed = discord.Embed(title="Battle Start!",
                              description='\n'.join(battle.log[-1:]) +
                              f"\n<@{user_id}>'s turn!")
        file1, url1 = BattleView(battle, user_id, opp_id,
                                 is_bot=is_bot).get_unit_image_file(unit1)
        file2, url2 = BattleView(battle, user_id, opp_id,
                                 is_bot=is_bot).get_unit_image_file(unit2)
        if url1:
            embed.set_thumbnail(url=url1)
        if url2:
            embed.set_image(url=url2)
        hp_bar1 = BattleView(battle, user_id, opp_id,
                             is_bot=is_bot).get_hp_bar(unit1.current_hp,
                                                       unit1.max_hp)
        hp_bar2 = BattleView(battle, user_id, opp_id,
                             is_bot=is_bot).get_hp_bar(unit2.current_hp,
                                                       unit2.max_hp)
        label1 = f"Your Unit: {unit1.name} HP"
        label2 = f"Boss Unit: {unit2.name} HP" if is_bot else f"Opponent Unit: {unit2.name} HP"
        stats1 = f"ATK: {unit1.stats['ATK']}  DEF: {unit1.stats['DEF']}"
        stats2 = f"ATK: {unit2.stats['ATK']}  DEF: {unit2.stats['DEF']}"
        shield_val = getattr(battle, 'second_player_shield', 0)
        shield_used = getattr(battle, 'second_player_shield_used', False)
        if not shield_used and shield_val > 0:
            shield_str = f"\n🛡️ Shield: {shield_val}"
        else:
            shield_str = ""
        embed.add_field(
            name=label1,
            value=f"{unit1.current_hp}/{unit1.max_hp}\n{hp_bar1}\n{stats1}")
        embed.add_field(
            name=label2,
            value=
            f"{unit2.current_hp}/{unit2.max_hp}\n{hp_bar2}\n{stats2}{shield_str}")
        files = []
        if file1:
            files.append(file1)
        if file2 and (not file1 or file2.filename != file1.filename):
            files.append(file2)
        await interaction.response.send_message(embed=embed,
                                                files=files,
                                                view=BattleView(
                                                    battle,
                                                    user_id,
                                                    opp_id,
                                                    is_bot=is_bot,
                                                    show_buttons=True),
                                                ephemeral=False)
        # After the battle, update boss HP and handle defeat if boss fight
        if is_bot and opponent.lower() == 'boss':
            # This logic should be triggered after the battle ends, e.g. in AttackButton or similar
            # Patch: scale prize on all boss stats, award points, and spawn new boss
            from .gacha_commands import load_points, save_points
            boss = load_boss()
            if unit2.current_hp <= 0 and not boss["defeated"]:
                boss["defeated"] = True
                # Prize: 50% of the sum of all boss stats
                total_stats = sum(boss["stats"].values())
                JACKPOT_MULTIPLIER = 10  # Change this value to adjust the multiplier
                jackpot = int(total_stats * JACKPOT_MULTIPLIER)
                # Award to the winner (user)
                user_points = load_points()
                user_points[user_id] = user_points.get(user_id, 0) + jackpot
                save_points(user_points)
                boss["current_hp"] = 0
                save_boss(boss)
                # Announce the prize
                await interaction.followup.send(
                    f"🎉 You defeated the boss and won the jackpot: {jackpot} points! A new boss has appeared!",
                    ephemeral=False)
                # Spawn a new boss
                load_boss()