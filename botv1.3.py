# IMPORTS
from interactions import slash_command, SlashContext, Client, OptionType, slash_option, listen, Intents
from discord import Embed, User
import sqlite3
import os
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta
import time


# ENVIRONMENT VARIABLES
load_dotenv()
# Store the bot's start time
bot_start_time = time.time()

WHITELISTED_IDS = [468965192408236054]


# Fetch the bot token from environment variables
bot_token = os.getenv("DISCORD_BOT_TOKEN")

# DATABASE SETUP
conn = sqlite3.connect('virtual_economy.db')
cursor = conn.cursor()

# Database Initialization
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance REAL,
    registered BOOLEAN,
    last_daily_claim INTEGER
    last_claim TEXT
)
''')
conn.commit()

DEFAULT_BALANCE = 1000.0
DAILY_AMOUNT = 500.0  # Amount to give to users daily
INFLATION_RATE = 0.02  # Inflation rate: 2% per day
AUTHORIZED_USERS = ["468965192408236054"]
DISCORD_SUPPORT_LINK = "https://discord.gg/TeHdXDugbY"
DEVELOPER_WEBSITE_LINK = "https://www.goosecrash.com"




# Slash commands and their implementations
@slash_command(name="start", description="Register in the virtual economy system.")
async def start(ctx: SlashContext):
    user_id = ctx.author.id
    try:
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        user = cursor.fetchone()
        if user:
            await ctx.send("You are already registered in the virtual economy system.")
        else:
            cursor.execute("INSERT INTO users (user_id, balance, registered) VALUES (?, ?, TRUE)", (user_id, DEFAULT_BALANCE))
            conn.commit()
            await ctx.send(f"Welcome to the virtual economy system! You've been awarded a default balance of {DEFAULT_BALANCE}.")

    except sqlite3.Error as e:
        print(f"Database error in /start command: {e}")
        await ctx.send("An error occurred while registering. Please try again.")

@slash_command(name="balance", description="Check your own or another user's virtual currency balance.")
@slash_option(
    name="user",
    description="User to check balance for (optional)",
    required=False,
    opt_type=OptionType.USER
)
async def balance(ctx: SlashContext, user: User = None):
    if user is None:
        user_id = ctx.author.id
        message = "your"
    else:
        user_id = user.id
        message = f"{user.name}'s"

    try:
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        user = cursor.fetchone()
        if user:
            await ctx.send(f"{message} current balance is {user[0]}.")
        else:
            await ctx.send(f"{message} are not registered in the virtual economy system.")

    except sqlite3.Error as e:
        print(f"Database error in /balance command: {e}")
        await ctx.send("An error occurred while fetching balance. Please try again.")

# ... [rank, daily, remove, cleanup commands]
@slash_command(name="rank", description="Check your rank based on your virtual currency balance.")
async def rank(ctx: SlashContext):
    try:
        cursor.execute("SELECT user_id, balance FROM users ORDER BY balance DESC")
        user_ranks = cursor.fetchall()

        embed = Embed(title="Rank Leaderboard", description="Ranking based on virtual currency balance:", color=0x00ff00)
        
        for index, (user_id, balance) in enumerate(user_ranks):
            user = await bot.fetch_user(user_id)
            if user:
                position = index + 1
                embed.add_field(name=f"#{position} - {user.display_name}", value=f"Balance: {balance} virtual currency", inline=False)

        await ctx.send(embed=embed.to_dict())
        
    except sqlite3.Error as e:
        print(f"Database error in /rank command: {e}")
        await ctx.send("An error occurred while fetching rank leaderboard. Please try again.")
@slash_command(name="uptime", description="Check bot's uptime")
async def uptime_command(ctx: SlashContext):
    current_time = time.time()
    uptime_seconds = int(current_time - bot_start_time)

    # Calculate hours, minutes, and seconds
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    uptime_seconds %= 60

    uptime_message = f"Bot uptime: {uptime_hours} hours, {uptime_minutes} minutes, {uptime_seconds} seconds"
    await ctx.send(uptime_message)


# ... [other imports and setup]

DAILY_AMOUNT = 500.0  # Daily virtual currency amount


from interactions import slash_command, SlashContext
from datetime import datetime, timedelta
import pytz
import sqlite3

@slash_command(name="daily", description="Claim your daily virtual currency reward.")
async def daily(ctx: SlashContext):
    user_id = ctx.author.id
    
    # Use Eastern Standard Time (EST)
    est = pytz.timezone('US/Eastern')
    est_time = datetime.now(est)
    current_date_est = est_time.strftime("%Y-%m-%d")

    try:
        cursor.execute("SELECT last_daily_claim FROM users WHERE user_id=?", (user_id,))
        last_claim_date = cursor.fetchone()

        if last_claim_date and last_claim_date[0] == current_date_est:
            await ctx.send("You've already claimed your daily reward today. Please try again tomorrow.")
            return

        # Award 100 coins
        cursor.execute("UPDATE users SET balance=balance+100, last_daily_claim=? WHERE user_id=?", (current_date_est, user_id))
        conn.commit()

        await ctx.send("Congratulations! You've claimed 100 virtual currency as your daily reward.")
    except sqlite3.Error as e:
        print(f"Database error in /daily command: {e}")
        await ctx.send("An error occurred while processing your daily reward. Please try again.")
@slash_command(name="cleanup", description="Clean up the economy by reducing balances and preventing inflation (Authorized users only).")
async def economy_cleanup(ctx: SlashContext):
    if str(ctx.author.id) in AUTHORIZED_USERS:
        try:
            cursor.execute("UPDATE users SET balance=balance*0.9 WHERE balance > 1000")
            conn.commit()
            await ctx.send("Economy cleanup completed.")
        except sqlite3.Error as e:
            print(f"Database error in /cleanup command: {e}")
            await ctx.send("An error occurred while performing economy cleanup.")
    else:
        await ctx.send("You are not authorized to use this command.")
@slash_command(name="create_corporation", description="Create your own corporation.")
@slash_option(
    name="corporation_name",
    description="Name of the corporation",
    required=True,
    opt_type=OptionType.STRING
)
async def create_corporation(ctx: SlashContext, corporation_name: str):
    user_id = ctx.author.id
    
    # Check if the user is already registered
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    
    if user:
        if user[0] >= 10000:  # Check if user has sufficient balance
            try:
                # Deduct the capital from user's balance
                cursor.execute("UPDATE users SET balance=balance-10000 WHERE user_id=?", (user_id,))
                
                # Create the corporation
                cursor.execute("INSERT INTO corporations (corporation_name, owner_id, stock_price) VALUES (?, ?, 100.0)", (corporation_name, user_id))
                conn.commit()
                
                await ctx.send(f"Congratulations! You have successfully created the corporation '{corporation_name}'.")
            except sqlite3.Error as e:
                print(f"Database error in /create_corporation command: {e}")
                await ctx.send("An error occurred while creating the corporation. Please try again.")
        else:
            await ctx.send("You do not have enough capital to create a corporation.")
    else:
        await ctx.send("You are not registered in the virtual economy system. Use the /start command to register.")


@slash_command(
    name="send_dm",
    description="Send a DM to the user who invoked the command",
)
async def send_dm(ctx, message: str):
    user = ctx.author
    await user.send(f"Hello, {user.mention}! Here's your DM: {message}")










@slash_command(name="help", description="Provides a description of the available commands.")
async def help_command(ctx: SlashContext):
    embed = Embed(title="Virtual Economy Bot Help", description="Here's how to use the Virtual Economy Bot!", color=0x3498db)
    embed.add_field(name="/start", value="Register in the virtual economy system and receive a default balance.", inline=True)
    embed.add_field(name="/balance", value="Check your virtual currency balance or the balance of another user by mentioning them.", inline=True)
    embed.add_field(name="/rank", value="Check your rank based on your virtual currency balance.", inline=True)
    embed.add_field(name="/daily", value="Claim your daily virtual currency reward.", inline=True)
    embed.add_field(name="/remove", value="Remove a specified amount of virtual currency from your balance (Authorized users only).", inline=True)
    embed.add_field(name="/cleanup", value="Reduce the balance of all registered users to prevent inflation (Authorized users only).", inline=True)
    embed.add_field(name="Support Server", value=f"[Click here for support]({DISCORD_SUPPORT_LINK})", inline=False)
    embed.add_field(name="/uptime", value="Displays the bot's uptime in days, hours, minutes, and seconds.")

    embed.add_field(name="Developer Website", value=f"[Visit our website]({DEVELOPER_WEBSITE_LINK})", inline=False)
    # ... [additional commands and descriptions]
    await ctx.send(embed=embed.to_dict())











# ======================
# Gambling Command Block
# ======================

# Required Imports for Gambling Command
from interactions import slash_command, SlashContext, OptionType, slash_option
import random

# Gambling Command using slash command syntax
@slash_command(name="gamble", description="Try your luck with gambling!")
@slash_option(
    name="amount",
    description="Amount of virtual currency to gamble",
    required=True,
    opt_type=OptionType.INTEGER
)
async def gamble_command(ctx: SlashContext, amount: int):
    """Handle the gambling command."""
    
    # Fetch the user's balance from the database
    user_id = ctx.author.id
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    user_balance = cursor.fetchone()
    
    # Check if the user is registered in the virtual economy
    if not user_balance:
        await ctx.send("You are not registered in the virtual economy.")
        return
    
    user_balance = user_balance[0]
    
    # Validate user's currency balance
    if amount > user_balance:
        await ctx.send("You don't have enough currency to gamble this amount.")
        return

    # Perform the gamble and determine the outcome
    outcome = random.choice(['win', 'lose'])
    
    if outcome == 'win':
        new_balance = user_balance + amount
        await ctx.send(f"Congratulations, you won! Your new balance is {new_balance}.")
    else:
        new_balance = user_balance - amount
        await ctx.send(f"Sorry, you lost. Your new balance is {new_balance}.")
    
    # Update the user's balance in the database
    cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
    conn.commit()

# End of Gambling Command Block
if __name__ == "__main__":
    # Store the bot's start time for uptime calculation
    start_time = datetime.utcnow()


def get_total_money_circulation():
    cursor.execute("SELECT SUM(balance) FROM users")
    total_money = cursor.fetchone()[0]
    return total_money

@listen()
async def on_ready():
    print("Ready")
    print(f"This bot is owned by {bot.owner}")
    
    guilds = bot.guilds
    print(f"The bot is in {len(guilds)} guilds:")
    for guild in guilds:
        print(f"- {guild.name} (ID: {guild.id})")
    
    total_money = get_total_money_circulation()
    await bot.change_presence(activity="Developer is hard at work!")


bot = Client(token=bot_token)
bot.start()
# Create a new SQLite database for logging commands
command_log_conn = sqlite3.connect('command_log.db')

# Create a table to log commands
command_log_cursor = command_log_conn.cursor()
command_log_cursor.execute('''
CREATE TABLE IF NOT EXISTS command_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_name TEXT NOT NULL,
    execution_time TEXT NOT NULL,
    user_id TEXT NOT NULL,
    server_id TEXT NOT NULL
);
''')
command_log_conn.commit()


# BOT INITIALIZATION
bot_token = os.getenv("DISCORD_BOT_TOKEN")

# SQLite database setup
conn = sqlite3.connect('virtual_economy.db')
cursor = conn.cursor()

# Database Initialization
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance REAL,
    registered BOOLEAN,
    last_daily_claim INTEGER
    last_claim TEXT
)
''')
conn.commit()

DEFAULT_BALANCE = 1000.0
DAILY_AMOUNT = 500.0  # Amount to give to users daily
INFLATION_RATE = 0.02  # Inflation rate: 2% per day
AUTHORIZED_USERS = ["468965192408236054"]
DISCORD_SUPPORT_LINK = "https://discord.gg/TeHdXDugbY"
DEVELOPER_WEBSITE_LINK = "https://www.goosecrash.com"




# Slash commands and their implementations
@slash_command(name="start", description="Register in the virtual economy system.")
async def start(ctx: SlashContext):
    user_id = ctx.author.id
    try:
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        user = cursor.fetchone()
        if user:
            await ctx.send("You are already registered in the virtual economy system.")
        else:
            cursor.execute("INSERT INTO users (user_id, balance, registered) VALUES (?, ?, TRUE)", (user_id, DEFAULT_BALANCE))
            conn.commit()
            await ctx.send(f"Welcome to the virtual economy system! You've been awarded a default balance of {DEFAULT_BALANCE}.")

    except sqlite3.Error as e:
        print(f"Database error in /start command: {e}")
        await ctx.send("An error occurred while registering. Please try again.")

@slash_command(name="balance", description="Check your own or another user's virtual currency balance.")
@slash_option(
    name="user",
    description="User to check balance for (optional)",
    required=False,
    opt_type=OptionType.USER
)
async def balance(ctx: SlashContext, user: User = None):
    if user is None:
        user_id = ctx.author.id
        message = "your"
    else:
        user_id = user.id
        message = f"{user.name}'s"

    try:
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        user = cursor.fetchone()
        if user:
            await ctx.send(f"{message} current balance is {user[0]}.")
        else:
            await ctx.send(f"{message} are not registered in the virtual economy system.")

    except sqlite3.Error as e:
        print(f"Database error in /balance command: {e}")
        await ctx.send("An error occurred while fetching balance. Please try again.")

# ... [rank, daily, remove, cleanup commands]
@slash_command(name="rank", description="Check your rank based on your virtual currency balance.")
async def rank(ctx: SlashContext):
    try:
        cursor.execute("SELECT user_id, balance FROM users ORDER BY balance DESC")
        user_ranks = cursor.fetchall()

        embed = Embed(title="Rank Leaderboard", description="Ranking based on virtual currency balance:", color=0x00ff00)
        
        for index, (user_id, balance) in enumerate(user_ranks):
            user = await bot.fetch_user(user_id)
            if user:
                position = index + 1
                embed.add_field(name=f"#{position} - {user.display_name}", value=f"Balance: {balance} virtual currency", inline=False)

        await ctx.send(embed=embed.to_dict())
        
    except sqlite3.Error as e:
        print(f"Database error in /rank command: {e}")
        await ctx.send("An error occurred while fetching rank leaderboard. Please try again.")
@slash_command(name="uptime", description="Check bot's uptime")
async def uptime_command(ctx: SlashContext):
    current_time = time.time()
    uptime_seconds = int(current_time - bot_start_time)

    # Calculate hours, minutes, and seconds
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    uptime_seconds %= 60

    uptime_message = f"Bot uptime: {uptime_hours} hours, {uptime_minutes} minutes, {uptime_seconds} seconds"
    await ctx.send(uptime_message)


# ... [other imports and setup]

DAILY_AMOUNT = 500.0  # Daily virtual currency amount


from interactions import slash_command, SlashContext
from datetime import datetime, timedelta
import pytz
import sqlite3

@slash_command(name="daily", description="Claim your daily virtual currency reward.")
async def daily(ctx: SlashContext):
    user_id = ctx.author.id
    
    # Use Eastern Standard Time (EST)
    est = pytz.timezone('US/Eastern')
    est_time = datetime.now(est)
    current_date_est = est_time.strftime("%Y-%m-%d")

    try:
        cursor.execute("SELECT last_daily_claim FROM users WHERE user_id=?", (user_id,))
        last_claim_date = cursor.fetchone()

        if last_claim_date and last_claim_date[0] == current_date_est:
            await ctx.send("You've already claimed your daily reward today. Please try again tomorrow.")
            return

        # Award 100 coins
        cursor.execute("UPDATE users SET balance=balance+100, last_daily_claim=? WHERE user_id=?", (current_date_est, user_id))
        conn.commit()

        await ctx.send("Congratulations! You've claimed 100 virtual currency as your daily reward.")
    except sqlite3.Error as e:
        print(f"Database error in /daily command: {e}")
        await ctx.send("An error occurred while processing your daily reward. Please try again.")
@slash_command(name="cleanup", description="Clean up the economy by reducing balances and preventing inflation (Authorized users only).")
async def economy_cleanup(ctx: SlashContext):
    if str(ctx.author.id) in AUTHORIZED_USERS:
        try:
            cursor.execute("UPDATE users SET balance=balance*0.9 WHERE balance > 1000")
            conn.commit()
            await ctx.send("Economy cleanup completed.")
        except sqlite3.Error as e:
            print(f"Database error in /cleanup command: {e}")
            await ctx.send("An error occurred while performing economy cleanup.")
    else:
        await ctx.send("You are not authorized to use this command.")
@slash_command(name="create_corporation", description="Create your own corporation.")
@slash_option(
    name="corporation_name",
    description="Name of the corporation",
    required=True,
    opt_type=OptionType.STRING
)
async def create_corporation(ctx: SlashContext, corporation_name: str):
    user_id = ctx.author.id
    
    # Check if the user is already registered
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    
    if user:
        if user[0] >= 10000:  # Check if user has sufficient balance
            try:
                # Deduct the capital from user's balance
                cursor.execute("UPDATE users SET balance=balance-10000 WHERE user_id=?", (user_id,))
                
                # Create the corporation
                cursor.execute("INSERT INTO corporations (corporation_name, owner_id, stock_price) VALUES (?, ?, 100.0)", (corporation_name, user_id))
                conn.commit()
                
                await ctx.send(f"Congratulations! You have successfully created the corporation '{corporation_name}'.")
            except sqlite3.Error as e:
                print(f"Database error in /create_corporation command: {e}")
                await ctx.send("An error occurred while creating the corporation. Please try again.")
        else:
            await ctx.send("You do not have enough capital to create a corporation.")
    else:
        await ctx.send("You are not registered in the virtual economy system. Use the /start command to register.")



@slash_command(name="help", description="Provides a description of the available commands.")
async def help_command(ctx: SlashContext):
    embed = Embed(title="Virtual Economy Bot Help", description="Here's how to use the Virtual Economy Bot!", color=0x3498db)
    embed.add_field(name="/start", value="Register in the virtual economy system and receive a default balance.", inline=True)
    embed.add_field(name="/balance", value="Check your virtual currency balance or the balance of another user by mentioning them.", inline=True)
    embed.add_field(name="/rank", value="Check your rank based on your virtual currency balance.", inline=True)
    embed.add_field(name="/daily", value="Claim your daily virtual currency reward.", inline=True)
    embed.add_field(name="/remove", value="Remove a specified amount of virtual currency from your balance (Authorized users only).", inline=True)
    embed.add_field(name="/cleanup", value="Reduce the balance of all registered users to prevent inflation (Authorized users only).", inline=True)
    embed.add_field(name="Support Server", value=f"[Click here for support]({DISCORD_SUPPORT_LINK})", inline=False)
    embed.add_field(name="/uptime", value="Displays the bot's uptime in days, hours, minutes, and seconds.")

    embed.add_field(name="Developer Website", value=f"[Visit our website]({DEVELOPER_WEBSITE_LINK})", inline=False)
    # ... [additional commands and descriptions]
    await ctx.send(embed=embed.to_dict())











if __name__ == "__main__":
    # Store the bot's start time for uptime calculation
    start_time = datetime.utcnow()


def get_total_money_circulation():
    cursor.execute("SELECT SUM(balance) FROM users")
    total_money = cursor.fetchone()[0]
    return total_money

@listen()
async def on_ready():
    print("Ready")
    print(f"This bot is owned by {bot.owner}")
    
    guilds = bot.guilds
    print(f"The bot is in {len(guilds)} guilds:")
    for guild in guilds:
        print(f"- {guild.name} (ID: {guild.id})")
    
    total_money = get_total_money_circulation()
    await bot.change_presence(activity="Developer is hard at work!")


bot = Client(token=bot_token)
bot.start()

# UTILITY FUNCTIONS


# COMMANDS


# EVENTS


# RATE LIMITING

# Simple rate limiting
rate_limit = {}
def check_rate_limit(user_id):
    if user_id in rate_limit:
        last_time = rate_limit[user_id]
        if time.time() - last_time < 10:  # 10 seconds cooldown
            return True
    rate_limit[user_id] = time.time()
    return False


# ERROR HANDLING

# Simple error handling
async def handle_error(ctx, error_message):
    await ctx.send(f'An error occurred: {error_message}')


# MAIN


