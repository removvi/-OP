import discord
from discord import app_commands

from bot.commands import register_commands


def create_client():
    intents = discord.Intents.default()
    intents.message_content = True

    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)
    register_commands(tree, client)

    @client.event
    async def on_ready():
        await tree.sync()
        print(f"Bot connected as {client.user}")
        print("Slash commands synced")
        print("Web site: http://127.0.0.1:5000")

    return client
