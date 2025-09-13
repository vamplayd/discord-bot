import discord
from discord.ext import tasks, commands
from googleapiclient.discovery import build
import os



# ------------------------------
# Environment Variables
# ------------------------------
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = os.getenv("CHANNEL_ID")
channel_id_env = os.getenv("DISCORD_CHANNEL_ID")

# Ensure environment variables are set
if DISCORD_TOKEN is None:
    raise ValueError("DISCORD_TOKEN not set in environment variables")
if YOUTUBE_API_KEY is None:
    raise ValueError("YOUTUBE_API_KEY not set in environment variables")
if YOUTUBE_CHANNEL_ID is None:
    raise ValueError("CHANNEL_ID not set in environment variables")
if channel_id_env is None:
    raise ValueError("DISCORD_CHANNEL_ID not set in environment variables")

DISCORD_CHANNEL_ID = int(channel_id_env)

# ------------------------------
# Discord Bot Setup
# ------------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------------------
# YouTube API Client
# ------------------------------
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# Track the last posted video
last_video_id = None

def get_latest_video():
    """Fetch the latest video from the YouTube channel."""
    request = youtube.search().list(
        part="snippet",
        channelId=YOUTUBE_CHANNEL_ID,
        maxResults=1,
        order="date"
    )
    response = request.execute()
    video = response['items'][0]
    video_id = video['id']['videoId']
    video_title = video['snippet']['title']
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    return video_id, video_title, video_url

# ------------------------------
# Task to Check New Video
# ------------------------------
@tasks.loop(minutes=5)
async def check_new_video():
    global last_video_id
    video_id, video_title, video_url = get_latest_video()

    if video_id != last_video_id:
        last_video_id = video_id
        channel = bot.get_channel(DISCORD_CHANNEL_ID)

        # Ensure the channel is a text channel
        if isinstance(channel, discord.TextChannel):
            # Send custom message
            await channel.send(f"@everyone VampBlox uploaded!\n{video_url}")
            
        else:
            print("The channel is not a text channel!")

# ------------------------------
# Bot Events
# ------------------------------
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    check_new_video.start()

# ------------------------------
# Run Bot
# ------------------------------

bot.run(DISCORD_TOKEN)
