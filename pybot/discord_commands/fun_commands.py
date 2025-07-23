import discord
import random
import json
import os

def register_fun_commands(client, GUILD_ID):
    DATA_FILE = "points_data.json"
    def load_data():
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                return data.get("user_points", {}), data.get("bot_bank", {"amount": 0})
        return {}, {"amount": 0}

    def save_data():
        with open(DATA_FILE, "w") as f:
            json.dump({"user_points": user_points, "bot_bank": bot_bank}, f)

    user_points, bot_bank = load_data()

    class GambleView(discord.ui.View):
        def __init__(self, user_id):
            super().__init__(timeout=120)
            self.user_id = user_id
            self.update_buttons()

        def update_buttons(self):
            self.clear_items()
            self.add_item(FarmButton(self.user_id))
            self.add_item(GambleButton(self.user_id, 0.1, label="🚫💸Gamble 10%", bot_bank=bot_bank))
            self.add_item(GambleButton(self.user_id, 0.25, label="🎲 Gamble 25%", bot_bank=bot_bank))
            self.add_item(GambleButton(self.user_id, 0.5, label="🎲🎲 Gamble 50%", bot_bank=bot_bank))
            self.add_item(GambleButton(self.user_id, 1.0, label="🎲🎲🎲 All In", bot_bank=bot_bank, style=discord.ButtonStyle.primary))
            self.add_item(LeaderboardButton())

    class LeaderboardButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="🏆 Leaderboard", style=discord.ButtonStyle.secondary)
        async def callback(self, interaction):
            # Sort users by points, descending
            top = sorted(user_points.items(), key=lambda x: x[1], reverse=True)[:10]
            embed = discord.Embed(title="🏆 Leaderboard", color=discord.Color.gold())
            lines = []
            # Add bot bank as the first entry
            lines.append(f"**🤖 Bot Bank** — {bot_bank['amount']} points")
            if not top:
                lines.append("No users have points yet.")
            else:
                for idx, (uid, pts) in enumerate(top, 1):
                    member = interaction.guild.get_member(int(uid)) if interaction.guild else None
                    name = member.display_name if member else f"User {uid}"
                    lines.append(f"**{idx}. {name}** — {pts} points")
            embed.description = "\n".join(lines)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        # No interaction_check needed; view already restricts to correct user

    class FarmButton(discord.ui.Button):
        def __init__(self, user_id):
            super().__init__(label="🌾Farm Points", style=discord.ButtonStyle.success)
            self.user_id = user_id
        async def callback(self, interaction):
            import random
            points = user_points.get(self.user_id, 0)
            luck = random.random()
            if luck < 0.01:
                gain = random.randint(1000, 5000)
            elif luck < 0.05:
                gain = random.randint(200, 1000)
            elif luck < 0.2:
                gain = random.randint(50, 200)
            else:
                gain = random.randint(1, 50)
            user_points[self.user_id] = points + gain
            save_data()
            await interaction.response.edit_message(content=f"🌾 You farmed {gain} points!\n💰 Current points: {user_points[self.user_id]}", view=GambleView(self.user_id))

    class GambleButton(discord.ui.Button):
        def __init__(self, user_id, percent, label, bot_bank, style=discord.ButtonStyle.danger):
            super().__init__(label=label, style=style)
            self.user_id = user_id
            self.percent = percent
            self.bot_bank = bot_bank
        async def callback(self, interaction):
            import random
            points = user_points.get(self.user_id, 0)
            gamble_amount = max(1, int(points * self.percent))
            if points < gamble_amount:
                await interaction.response.edit_message(content=f"❌ Not enough points to gamble!\n💰 Current points: {points}\n🏦 Bot Bank: {self.bot_bank['amount']}", view=GambleView(self.user_id))
                return
            win = random.random() < 0.45  # 45% win chance
            if win:
                user_points[self.user_id] = points + gamble_amount
                msg = f"You WON! You gained {gamble_amount} points!"
            else:
                user_points[self.user_id] = points - gamble_amount
                self.bot_bank["amount"] += gamble_amount
                msg = f"You LOST! You lost {gamble_amount} points!"
            save_data()
            await interaction.response.edit_message(content=f"{msg}\n💰 Current points: {user_points[self.user_id]}\n🏦 Bot Bank: {self.bot_bank['amount']}", view=GambleView(self.user_id))

    @client.tree.command(name="gamble", description="Open the gambling panel", guild=GUILD_ID)
    async def gamble(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if user_id not in user_points:
            user_points[user_id] = 100  # Start with 100 points
            save_data()
        view = GambleView(user_id)
        await interaction.response.send_message(f"Gambling Panel\n💰 Current points: {user_points[user_id]}\n🏦 Bot Bank: {bot_bank['amount']}", view=view, ephemeral=True)
        # Play Gambling.wav after the panel opens
        try:
            from audio_actions import play_gambling_audio
            loop = getattr(interaction.client, 'loop', None)
            if loop and loop.is_running():
                loop.create_task(play_gambling_audio(interaction.client))
        except Exception as e:
            print(f"Error playing Gambling.wav: {e}")

    @client.tree.command(name="slot", description="Spin the slot machine to win points!", guild=GUILD_ID)
    async def slot(interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if user_id not in user_points:
            user_points[user_id] = 100
        symbols = ["🍒", "🍋", "🔔", "⭐", "🍀", "💎"]
        spin = [random.choice(symbols) for _ in range(3)]
        result = " ".join(spin)
        payout = 0
        # Simple payout logic
        if spin[0] == spin[1] == spin[2]:
            payout = 1000
            msg = f"JACKPOT! {result} You win {payout} points!"
        elif spin[0] == spin[1] or spin[1] == spin[2] or spin[0] == spin[2]:
            payout = 100
            msg = f"Nice! {result} You win {payout} points!"
        else:
            msg = f"{result} No win this time."
            # Play dang_it.wav on loss
            try:
                from audio_actions import play_dang_it_audio
                loop = getattr(interaction.client, 'loop', None)
                if loop and loop.is_running():
                    loop.create_task(play_dang_it_audio(interaction.client))
            except Exception as e:
                print(f"Error playing dang_it.wav: {e}")
        user_points[user_id] += payout
        save_data()
        await interaction.response.send_message(f"{msg}\n💰 Your points: {user_points[user_id]}", ephemeral=True)

    @client.tree.command(name="michael_saves", description="Michael Saves the Day", guild=GUILD_ID)
    async def michael_saves(interaction: discord.Interaction):
        await interaction.response.send_message("Michael Saves the Day!", ephemeral=True)
        await interaction.followup.send("<a:jd:1395904586317041794>")
