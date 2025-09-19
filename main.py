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

# ------------------------------
# Save/load last video
# ------------------------------
LAST_VIDEO_FILE = "last_video.txt"

def save_last_video(video_id):
    try:
        with open(LAST_VIDEO_FILE, "w") as f:
            f.write(video_id)
    except Exception as e:
        print(f"Error saving last video: {e}")

def load_last_video():
    if os.path.exists(LAST_VIDEO_FILE):
        with open(LAST_VIDEO_FILE, "r") as f:
            return f.read().strip()
    return None

last_video_id = load_last_video()

# ------------------------------
# Fetch latest video
# ------------------------------
def get_latest_video():
    try:
        request = youtube.search().list(
            part="snippet",
            channelId=YOUTUBE_CHANNEL_ID,
            maxResults=1,
            order="date",
            type="video"  # ensure only videos, not playlists/shorts
        )
        response = request.execute()
        video = response['items'][0]
        video_id = video['id']['videoId']
        video_title = video['snippet']['title']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        return video_id, video_title, video_url
    except Exception as e:
        print(f"Error fetching video: {e}")
        return None, None, None

# ------------------------------
# Task to Check New Video
# ------------------------------
@tasks.loop(minutes=5)
async def check_new_video():
    global last_video_id
    try:
        video_id, video_title, video_url = get_latest_video()
        if video_id and video_id != last_video_id:
            last_video_id = video_id
            save_last_video(video_id)  # ✅ persist the new video
            channel = bot.get_channel(DISCORD_CHANNEL_ID)

            if isinstance(channel, discord.TextChannel):
                await channel.send(f"@everyone The main channel 404Crepes uploaded something!\n{video_url}")
            else:
                print("The channel is not a text channel!")
    except Exception as e:
        print(f"Error in check_new_video loop: {e}")

@check_new_video.before_loop
async def before_check():
    await bot.wait_until_ready()

# ------------------------------
# Bot Events
# ------------------------------
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    if not check_new_video.is_running():
        check_new_video.start()

# ------------------------------
# Run Bot
# ------------------------------
bot.run(DISCORD_TOKEN)
