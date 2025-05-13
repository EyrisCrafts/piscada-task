from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
import discord
import nats
import alert_pb2
from nats.aio.client import Client as NatsClient
from nats.aio.msg import Msg
from discord import Client as DiscordClient, Intents

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

nats_client: NatsClient = None
is_already_initialized = False
discord_channel = None

intents = Intents.default()
discord_client = DiscordClient(intents=intents)

@discord_client.event
async def on_ready():
    global is_already_initialized, discord_channel, nats_client
    print("Discord bot is ready")

    if is_already_initialized:
        return

    discord_channel = discord.utils.get(discord_client.get_all_channels(), name="general")

    async def handle_alert_message(msg: Msg):
        # decoded_message = msg.data.decode()
        try:
            alert = alert_pb2.Alert()
            alert.ParseFromString(msg.data)
            message_to_send = f"{alert.alert_id} {alert.message}"
            print("Sending message ", message_to_send)
            if discord_channel:
                await discord_channel.send(message_to_send)
        except: 
            print("Error parsing Alert")

    # Now nats_client is guaranteed to be initialized
    await nats_client.subscribe("alerts", cb=handle_alert_message)

    is_already_initialized = True

async def main():
    global nats_client
    nats_client = await nats.connect(NATS_URL)
    await discord_client.start(DISCORD_BOT_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())