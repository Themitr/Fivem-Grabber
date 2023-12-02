import asyncio
import logging
import discord
from discord import app_commands
from discord.ext import commands
import requests
import json
import datetime

#=======================================================================================
#                                  FILL THE FOLLOWING                                  #
#=======================================================================================

# Your bot token here
bot_token = ""

# Your discord log channel webhook url here
webhook_url = ""

#=======================================================================================
#                                  FILL THE ABOVE                                      #
#=======================================================================================

server_ip = "cfx.re/join/6p4vq4"

def fetch_player_data(discord_id: int):
    url = "https://lookupguru.herokuapp.com/lookup"
    payload = {"input": str(discord_id)}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    json_response = response.json()

    # Filter out unwanted data from the response
    filtered_data = {
        "id": json_response["data"]["id"],
        "username": json_response["data"]["username"],
        "discriminator": json_response["data"]["discriminator"],
        "avatar_url": f"https://cdn.discordapp.com/avatars/{discord_id}/{json_response['data']['avatar']['id']}.png"
    }

    return filtered_data
#old discord 1.7.3
token = bot_token
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("Bot is Up and Ready!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)

# create a file handler
handler = logging.FileHandler(filename="bot.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))

# add the file handler to the logger
logger.addHandler(handler)


def server_name_fetch(data):

    server_name = data["Data"]["hostname"]
    if "^6" in server_name:
        server_name = server_name.split("^6")[1]
    if "^4" in server_name:
        server_name = server_name.split("^4")[1]
    if "|" in server_name:
        server_name = server_name.split("|")[0]
    if "-" in server_name:
        server_name = server_name.split("-")[0]
    if "^" in server_name:
        server_name = server_name.split("^")[0]

    return server_name

@bot.tree.command(name="hey")
async def hello(interaction: discord.Interaction):

    # log the user's command
    logger.info(f"{interaction.user.name} used the 'hey'.")

    # send the log to the webhook
    webhook_data = {
        "content": f"{interaction.user.name} | ({interaction.user}) used the command /hey."
    }
    requests.post(webhook_url, json=webhook_data)

    await interaction.response.send_message(f"Hey {interaction.user.mention}!", ephemeral=False)

@bot.tree.command(name="say")
@app_commands.describe(thing_to_say="What should I say?")
async def say(interaction: discord.Interaction, thing_to_say: str):

    # send the log to the webhook
    webhook_data = {
        "content": f"{interaction.user.name} | ({interaction.user}) used the command /say."
    }
    requests.post(webhook_url, json=webhook_data)

    await interaction.response.send_message(f"{interaction.user.name} said: {thing_to_say}")

    # log the user's command
    logger.info(f"{interaction.user.name} used the 'say' command with the argument: {thing_to_say}")


@bot.tree.command(name="ip")
@app_commands.describe(ip_address="Please enter the server cfx link")
async def set_server_ip(interaction: discord.Interaction, ip_address: str):

    global server_ip
    server_ip = ip_address

    server = server_ip.split("/")[-1]
    # make the API call
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    url = f"https://servers-frontend.fivem.net/api/servers/single/{server}"
    response = requests.get(url, headers=headers)
    data = response.json()

    server_name = server_name_fetch(data)

    # Construct the embed object
    embed = {
        "title": f"{interaction.user.name} used the command /ip",
        "description": f"Server: {server_name}\nIp: {server_ip}",
        "color": 16711680  # Red color
    }

    # Construct the data to be sent to the webhook
    webhook_data = {
        "embeds": [embed]
    }

    # Send the data to the webhook
    requests.post(webhook_url, json=webhook_data)

    await interaction.response.send_message(f"Server IP set to: {ip_address}\nServer: {server_name}", ephemeral=False)

    # log the user's command
    logger.info(f"{interaction.user.name} used the 'ip' command with the ip: {ip_address}\nServer: {server_name}")



@bot.tree.command(name="id")
@app_commands.describe(id="Please enter the player ID")
async def get_identifiers(interaction: discord.Interaction, id: str):

    identifiers = []

    server = server_ip.split("/")[-1]
    # make the API call
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    url = f"https://servers-frontend.fivem.net/api/servers/single/{server}"
    response = requests.get(url, headers=headers)
    data = response.json()

    server_name = server_name_fetch(data)

    for player in data["Data"]["players"]:
        if player['id'] == int(id):
            identifiers = player['identifiers']
            break

    if not identifiers:
        embed = discord.Embed(
            title=f"No player with ID {id} found.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)
    else:
        user_id = None
        for identifier in identifiers:
            if identifier.startswith("discord:"):
                user_id = identifier.split(":")[1]
                break

        if user_id is None:
            embed = discord.Embed(
                title=f"No Discord account found for player with ID {id}.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            user_info = fetch_player_data(user_id)
            embed = discord.Embed(
                title=f"Player Info for ID {id}\nServer: {server_name}",
                color=discord.Color.dark_green()
            )
            embed.set_thumbnail(url=user_info['avatar_url'])
            embed.add_field(name="Discord Username", value=f"<@{user_info['id']}>", inline=False)
            embed.add_field(name="Steam Name", value=player['name'], inline=False)
            identifiers_str = "\n".join(identifiers) if identifiers else "No identifiers found."
            embed.add_field(name="Identifiers", value=identifiers_str, inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=False)

    # Construct the embed object
    embed = {
        "title": f"{interaction.user.name} used the id: {id}",
        "description": f"Server: {server_name}\nIp: {server_ip}",
        "color": 16711680  # Red color
    }

    # Construct the data to be sent to the webhook
    webhook_data = {
        "embeds": [embed]
    }

    # Send the data to the webhook
    requests.post(webhook_url, json=webhook_data)
    
    # log the user's command
    logger.info(f"{interaction.user.name} used the 'id' command with the id: {id}\nServer: {server_name}")


@bot.tree.command(name="all")
async def show_players(interaction: discord.Interaction):

    server = server_ip.split("/")[-1]
    # make the API call
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    url = f"https://servers-frontend.fivem.net/api/servers/single/{server}"
    response = requests.get(url, headers=headers)
    data = response.json()
    clients = data["Data"]["clients"]

    server_name = server_name_fetch(data)

    players_sorted = sorted(data["Data"]["players"], key=lambda p: p["id"])
    chunks = [players_sorted[i:i + 40] for i in range(0, len(players_sorted), 40)]

    embeds = []
    for i, chunk in enumerate(chunks):
        player_info = ""
        for player in chunk:
            player_info += f"**ID:** {player['id']}, **Name:** {player['name']}, **Ping:** {player['ping']} ms\n"

        embed = discord.Embed(
            title=f"Players online - {clients}\nServer: {server_name}",
            description=player_info,
            color=discord.Color.dark_green()
        )

        timestamp = datetime.datetime.utcnow()
        # Add 3 hours to the timestamp
        timestamp = timestamp + datetime.timedelta(hours=3)

        embed.set_author(name="FiveM Server Status", icon_url="https://cdn3.iconfinder.com/data/icons/databases-3/512/search_data-512.png")
        embed.set_footer(text="Data last updated")
        embed.timestamp = timestamp

        # Add a suffix to the title if there's more than one embed
        if len(chunks) > 1:
            embed.title += f" ({i+1}/{len(chunks)})"

        embeds.append(embed)

    # send a reply title
    await interaction.response.send_message("Fetching...", ephemeral=True)

    # send the first embed
    message = await interaction.channel.send(embed=embeds[0])
    

    # add the reactions
    if len(embeds) > 1:
        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")

# =======================================================================================================

    # define the check for the reaction collector
    def check(reaction, user):
        return user == interaction.user and str(reaction.emoji) in ["⬅️", "➡️"]

    # Construct the embed object
    embed = {
        "title": f"{interaction.user.name} used the command /all",
        "description": f"Server: {server_name}\nIp: {server_ip}",
        "color": 16711680  # Red color
    }

    # Construct the data to be sent to the webhook
    webhook_data = {
        "embeds": [embed]
    }

    # Send the data to the webhook
    requests.post(webhook_url, json=webhook_data)

    # log the user's command
    logger.info(f"{interaction.user.name} used the 'all' command.\nServer: {server_name}")

# =======================================================================================================

    # start the reaction collector
    i = 0
    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=600.0, check=check)

            if str(reaction.emoji) == "➡️":
                i = (i + 1) % len(embeds)
                await message.edit(embed=embeds[i])
            elif str(reaction.emoji) == "⬅️":
                i = (i - 1) % len(embeds)
                await message.edit(embed=embeds[i])

            await message.remove_reaction(reaction, user)

        except asyncio.TimeoutError:
            break

#============================================================================

@bot.tree.command(name="name")
async def show_players(interaction: discord.Interaction, name: str = None):

    server = server_ip.split("/")[-1]
    # make the API call
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    url = f"https://servers-frontend.fivem.net/api/servers/single/{server}"
    response = requests.get(url, headers=headers)
    data = response.json()
    clients = data["Data"]["clients"]

    server_name = server_name_fetch(data)

    c_name = str(name).upper()
    un = str(c_name).lower()
    players_sorted = ""
    for player in data["Data"]["players"]:
        if un in str(player['name']).lower():
            players_sorted += f"**ID:** {player['id']}, **Name:** {player['name']}, **Ping:** {player['ping']} ms\n"

    if players_sorted:
        embed = discord.Embed(
            title=f"Players online with ***{un}*** in name\nServer: {server_name}",
            description=players_sorted,
            color=discord.Color.dark_green()
        )
    else:
        embed = discord.Embed(
            title=f"No players found online with ***{un}*** in name",
            color=discord.Color.red()
        )
    await interaction.response.send_message(embed=embed, ephemeral=False)

    # Construct the embed object
    embed = {
        "title": f"{interaction.user.name} searched for players with ***{un}*** in name.",
        "description": f"Server: {server_name}\nIp: {server_ip}",
        "color": 16711680  # Red color
    }

    # Construct the data to be sent to the webhook
    webhook_data = {
        "embeds": [embed]
    }

    # Send the data to the webhook
    requests.post(webhook_url, json=webhook_data)

    # log the user's command
    logger.info(f"{interaction.user.name} searched for players with {un} in name.\nServer: {server_name}")

#============================================================================
def fetch_player_data(discord_id: int):
    url = "https://lookupguru.herokuapp.com/lookup"
    payload = {"input": str(discord_id)}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    json_response = response.json()

    # Filter out unwanted data from the response
    filtered_data = {
        "id": json_response["data"]["id"],
        "username": json_response["data"]["username"],
        "discriminator": json_response["data"]["discriminator"],
        "avatar_url": f"https://cdn.discordapp.com/avatars/{discord_id}/{json_response['data']['avatar']['id']}.png"
    }

    return filtered_data

bot.run(token)
