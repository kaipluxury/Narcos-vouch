import discord
from discord.ext import commands
from discord import app_commands
import os
import sqlite3

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

PRODUCTS = [
    ("tr1gg3rb0t", "Tr1ggerbot"),
    ("pvt-redux", "Pvt-Redux"),
    ("gta-account", "Gta-Account"),
    ("grandrp-money", "GrandRP-Money"),
    ("grandrp-money-method", "GrandRP-Money-method"),
    ("custom-redux-and-guns", "Custom-redux-and-Guns"),
    ("pc-check", "Pc-Check"),
    ("skriptgg", "Skriptgg"),
    ("1337", "1337"),
    ("leader-application", "Leader-Application"),
    ("valo-z0ne", "VALO-Z0NE"),
    ("pc-check-procedure", "Pc-check-procedure"),
    ("pvt-cleaner", "Pvt-cleaner"),
    ("shax-cleaner", "Shax-cleaner")
]

LOGO_URL = "https://cdn.discordapp.com/attachments/1328282907814531073/1368135021256146944/narcos_sells_logo.png"

intents = discord.Intents.default()
intents.message_content = False
bot = commands.Bot(command_prefix="!", intents=intents)

def get_total_vouches():
    conn = sqlite3.connect("vouches.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS vouches (customer TEXT, product TEXT, feedback TEXT)")
    cursor.execute("SELECT COUNT(*) FROM vouches")
    count = cursor.fetchone()[0]
    conn.close()
    return count

async def update_bot_status():
    count = get_total_vouches()
    activity = discord.Activity(type=discord.ActivityType.watching, name=f"{count} vouches")
    await bot.change_presence(activity=activity)

class ProductDropdown(discord.ui.Select):
    def __init__(self, user: discord.User):
        self.user = user
        options = [discord.SelectOption(label=label, value=value) for value, label in PRODUCTS]
        super().__init__(placeholder="Select a product", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(FeedbackModal(product=self.values[0], user=self.user))

class ProductView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=60)
        self.add_item(ProductDropdown(user))

class FeedbackModal(discord.ui.Modal, title="Provide Feedback"):
    def __init__(self, product: str, user: discord.User):
        super().__init__()
        self.product = product
        self.user = user
        self.feedback_input = discord.ui.TextInput(label="Feedback", style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.feedback_input)

    async def on_submit(self, interaction: discord.Interaction):
        feedback = self.feedback_input.value

        # Save to DB
        conn = sqlite3.connect("vouches.db")
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS vouches (
            customer TEXT, product TEXT, feedback TEXT
        )""")
        cursor.execute("INSERT INTO vouches (customer, product, feedback) VALUES (?, ?, ?)",
                       (str(self.user), self.product, feedback))
        conn.commit()
        conn.close()

        vouch_count = get_total_vouches()

        # Build embed
        embed = discord.Embed(title=f"No. of Vouches: {vouch_count}", color=discord.Color.red())
        embed.add_field(name="Customer", value=self.user.mention, inline=False)
        embed.add_field(name="Product", value=self.product, inline=False)
        embed.add_field(name="Feedback", value=feedback, inline=False)
        embed.set_thumbnail(url=LOGO_URL)
        embed.set_image(url=LOGO_URL)  # Big logo
        embed.set_footer(text="Thanks For Vouching | Made By Kai", icon_url=LOGO_URL)

        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)

        await update_bot_status()
        await interaction.response.send_message("✅ Vouch submitted successfully!", ephemeral=True)

@bot.tree.command(name="vouch", description="Submit a vouch", guild=discord.Object(id=GUILD_ID))
async def vouch(interaction: discord.Interaction):
    await interaction.response.send_message("Please select a product:", view=ProductView(interaction.user), ephemeral=True)

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Bot is ready. Logged in as {bot.user}")
        await update_bot_status()
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

bot.run(TOKEN)
