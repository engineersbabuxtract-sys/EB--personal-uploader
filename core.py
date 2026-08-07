# core.py - Core helper functions
import os
import time
import asyncio
import subprocess
import logging
from pyrogram import Client
from pyrogram.types import Message
from utils import progress_bar

logger = logging.getLogger(__name__)

def duration(filename):
    """Get video duration using ffprobe"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
             "default=noprint_wrappers=1:nokey=1", filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10
        )
        return float(result.stdout)
    except Exception as e:
        logger.error(f"Duration error: {e}")
        return 0

async def download(url, name):
    """Download file asynchronously"""
    try:
        import aiohttp
        import aiofiles
        ka = f'{name}.pdf'
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(ka, mode='wb')
                    await f.write(await resp.read())
                    await f.close()
                else:
                    raise Exception(f"Download failed: {resp.status}")
        return ka
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise

async def download_video(url, cmd, name):
    """Download video using yt-dlp"""
    try:
        if not cmd:
            cmd = f'yt-dlp -f "bestvideo+bestaudio" "{url}" -o "{name}.mp4"'
        
        download_cmd = f'{cmd} -R infinite --fragment-retries 25 --socket-timeout 50 --external-downloader aria2c --downloader-args "aria2c: -x 16 -j 32" --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"'
        
        logger.info(f"Running: {download_cmd}")
        subprocess.run(download_cmd, shell=True, timeout=600)
        
        # Find the downloaded file
        possible_names = [
            name,
            f"{name}.webm",
            f"{name}.mkv",
            f"{name}.mp4",
            f"{name}.mp4.webm"
        ]
        for fname in possible_names:
            if os.path.isfile(fname):
                return fname
        
        return name
    except Exception as e:
        logger.error(f"Video download error: {e}")
        raise

async def send_vid(bot: Client, m: Message, cc, filename, thumb, name, prog):
    """Send video with thumbnail"""
    try:
        # Generate thumbnail
        subprocess.run(f'ffmpeg -i "{filename}" -ss 00:00:12 -vframes 1 "{filename}.jpg"', shell=True, timeout=10)
        await prog.delete(True)
        reply = await m.reply_text(f"**⥣ Uploading...** » `{name}`")
        
        thumbnail = thumb if thumb != "no" else f"{filename}.jpg"
        dur = int(duration(filename))
        start_time = time.time()

        try:
            await m.reply_video(
                filename, caption=cc, supports_streaming=True,
                height=720, width=1280, thumb=thumbnail, duration=dur,
                progress=progress_bar, progress_args=(reply, start_time)
            )
        except Exception as e:
            logger.error(f"Video send error: {e}")
            await m.reply_document(
                filename, caption=cc,
                progress=progress_bar, progress_args=(reply, start_time)
            )

        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)
        if os.path.exists(f"{filename}.jpg"):
            os.remove(f"{filename}.jpg")
        await reply.delete(True)
    except Exception as e:
        logger.error(f"Send video error: {e}")
        raise
