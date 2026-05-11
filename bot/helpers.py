import discord

from state import state


async def safe_defer(interaction):
    try:
        if not interaction.response.is_done():
            await interaction.response.defer()
    except discord.NotFound:
        print("Interaction already expired")


async def safe_send(interaction, message):
    try:
        if interaction.response.is_done():
            await interaction.followup.send(message)
        else:
            await interaction.response.send_message(message)
    except discord.NotFound:
        print("Cannot send response: interaction expired")


async def connect_to_voice(interaction: discord.Interaction):
    if not interaction.user.voice:
        await safe_send(interaction, "Ти не в голосовому каналі")
        return None

    channel = interaction.user.voice.channel
    state.last_voice_channel = channel

    voice_client = interaction.guild.voice_client
    if voice_client:
        await voice_client.move_to(channel)
    else:
        voice_client = await channel.connect()

    return voice_client
