# core.py - Core helper functions (minimal, keeps original functionality)
import os
import time
import asyncio
import subprocess
from pyrogram import Client
from pyrogram.types import Message


def duration(filename):
    """Get video duration using ffprobe"""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
         "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout)


def old_download(url, file_name, chunk_size=1024 * 10):
    """Download file using requests"""
    import requests
    if os.path.exists(file_name):
        os.remove(file_name)
    r = requests.get(url, allow_redirects=True, stream=True)
    with open(file_name, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                fd.write(chunk)
    return file_name


async def download_video(url, cmd, name):
    """Download video using yt-dlp"""
    download_cmd = f'{cmd} -R infinite --fragment-retries 25 --socket-timeout 50 --external-downloader aria2c --downloader-args "aria2c: -x 16 -j 32" --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"'
    print(download_cmd)
    subprocess.run(download_cmd, shell=True)
    
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


async def download(url, name):
    """Download file asynchronously"""
    import aiohttp
    import aiofiles
    ka = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(ka, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return ka


async def send_vid(bot: Client, m: Message, cc, filename, thumb, name, prog):
    """Send video with thumbnail"""
    subprocess.run(f'ffmpeg -i "{filename}" -ss 00:00:12 -vframes 1 "{filename}.jpg"', shell=True)
    await prog.delete(True)
    reply = await m.reply_text(f"**⥣ Uploading...** » `{name}`")
    
    try:
        if thumb == "no":
            thumbnail = f"{filename}.jpg"
        else:
            thumbnail = thumb
    except Exception as e:
        await m.reply_text(str(e))
        return

    dur = int(duration(filename))
    start_time = time.time()

    try:
        await m.reply_video(
            filename, caption=cc, supports_streaming=True,
            height=720, width=1280, thumb=thumbnail, duration=dur,
            progress=progress_bar, progress_args=(reply, start_time)
        )
    except Exception:
        await m.reply_document(
            filename, caption=cc,
            progress=progress_bar, progress_args=(reply, start_time)
        )

    os.remove(filename)
    os.remove(f"{filename}.jpg")
    await reply.delete(True)


# Import progress_bar from utils
from utils import progress_bar
