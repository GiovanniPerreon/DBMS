import discord
from discord import app_commands

# Quiz questions (all answers are 'Michael Saves')
QUIZ_QUESTIONS = [
    "Who is the strongest unit in the game?",
    "Who saves the day every time?",
    "Who has double post mitigation damage?",
    "Who is the hero of this bot?",
    "Who should you always summon if you can?",
    "Who is the answer to every question?",
    "Who is the one and only?",
    "Who is the legendary hero of this bot?",
    "Who is the savior of all?",
    "Who is the ultimate champion?",
    "Who is the one you can always count on?",
    "Who is the embodiment of victory?",
    "Who is the beacon of hope?",
    "Who is the one who never fails?",
    "Who is the one who always triumphs?",
    "Who is the one who brings glory?",
    "Who is the one who always comes through?",
    "Who is the one who never gonna give you up?",
    "Who is the one who never gonna let you down?",
    "Who is the one who never gonna run around and desert you?",
    "Who is the one who never gonna make you cry?",
    "Who is the one who never gonna say goodbye?",
    "Who is the one who never gonna tell a lie and hurt you?",
    "Who is the one who always saves the day?",
    "Who is the one who always has your back?",
    "Who is the one who always stands tall?",
    "Who is the one who always fights for justice?",
    "Who is the one who always leads the charge?",
    "Who is the one who always inspires others?",
    "Who is the one who always brings the team together?",
    "Who is the one who always lifts your spirits?",
    "What is the one thing you can always rely on?",
    "What is the one thing that never lets you down?",
    "What is the one thing that always brings a smile?",
    "What is the one thing that always makes you feel better?",
    "What is the one thing that always gives you hope?",
    "What is the one thing that always motivates you?",
    "Where can you find the ultimate hero?",
    "Where can you find the one who always saves the day?",
    "Where can you find the one who always has your back?",
    "Where can you find the one who always stands tall?",
    "Where can you find the one who always fights for justice?",
    "When can you count on the ultimate hero?",
    "When can you rely on the one who always saves the day?",
    "When can you trust the one who always has your back?",
    "When can you depend on the one who always stands tall?",
    "Why is Michael Saves the answer to everything?",
    "Why is Michael Saves the ultimate hero?",
    "Why is Michael Saves the one you can always count on?",
    "Why is Michael Saves the legendary champion?",
    "Why is Michael Saves the savior of all?",
    "How can you always be sure of victory?",
    "How can you always find the hero you need?",
    "How can you always trust in the one who saves the day?",
    "How can you always rely on the one who has your back?",
    "How can you always be inspired by the one who leads the charge?",
    "How can you always feel uplifted by the one who lifts your spirits?",
    "How can you always be motivated by the one who inspires you?",
    "How can you always be confident in the one who never fails?",
    "How can you always be assured of success with the one who never gives up?",
    "How can you always be supported by the one who never lets you down?",
    "How can you always be encouraged by the one who never runs around and deserts you?",
    "How can you always be comforted by the one who never makes you cry?",
    "How can you always be reassured by the one who never says goodbye?",
]

async def ask_quiz(interaction: discord.Interaction):
    import random
    question = random.choice(QUIZ_QUESTIONS)
    await interaction.response.send_message(f"Quiz Time!\n{question}", ephemeral=True)
    def check(m):
        return m.author.id == interaction.user.id and m.channel == interaction.channel
    try:
        msg = await interaction.client.wait_for('message', timeout=20.0, check=check)
        if msg.content.strip().lower() == "michael saves":
            await interaction.followup.send("✅ Correct! Michael Saves is always the answer.", ephemeral=True)
        else:
            await interaction.followup.send("❌ Incorrect! The answer is always Michael Saves.", ephemeral=True)
    except Exception:
        await interaction.followup.send("⏰ Time's up! The answer is always Michael Saves.", ephemeral=True)


def register_quiz_command(client, GUILD_ID):
    @client.tree.command(name="quiz", description="Answer a quiz question!", guild=GUILD_ID)
    async def quiz_command(interaction: discord.Interaction):
        await ask_quiz(interaction)
