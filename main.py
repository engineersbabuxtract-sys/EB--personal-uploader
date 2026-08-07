# main.py - Clean, modular rewrite
import os
import re
import sys
import json
import time
import asyncio
import logging
import subprocess
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import aiohttp
import aiofiles
import requests
import cloudscraper
import m3u8
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait
from pyromod import listen
from aiohttp import web

from vars import API_ID, API_HASH, BOT_TOKEN
from utils import progress_bar, hrb
import core as helper

# ===================== CONFIGURATION =====================
@dataclass
class Config:
    """Bot configuration"""
    PHOTO_URL: str = "https://i.postimg.cc/7LkVbrjm/yt.jpg"
    CP_PHOTO: str = "https://i.postimg.cc/x81h56j7/cpdrm.webp"
    APPX_PHOTO: str = "https://i.postimg.cc/Y0tt8SX3/appzip.webp"
    BOT_NAME: str = "𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚"
    CHANNEL_ID: str = "-1002257755789"
    COOKIES_FILE: str = os.getenv("COOKIES_FILE_PATH", "youtube_cookies.txt")
    WEBHOOK: bool = os.getenv("WEBHOOK", False)
    PORT: int = int(os.getenv("PORT", 8080))
    
    # Default credentials
    DEFAULT_CREDIT: str = "𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™"
    DEFAULT_TOKEN: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzYxNTE3MzAuMTI2LCJkYXRhIjp7Il9pZCI6IjYzMDRjMmY3Yzc5NjBlMDAxODAwNDQ4NyIsInVzZXJuYW1lIjoiNzc2MTAxNzc3MCIsImZpcnN0TmFtZSI6IkplZXYgbmFyYXlhbiIsImxhc3ROYW1lIjoic2FoIiwib3JnYW5pemF0aW9uIjp7Il9pZCI6IjVlYjM5M2VlOTVmYWI3NDY4YTc5ZDE4OSIsIndlYnNpdGUiOiJwaHlzaWNzd2FsbGFoLmNvbSIsIm5hbWUiOiJQaHlzaWNzd2FsbGFoIn0sImVtYWlsIjoiV1dXLkpFRVZOQVJBWUFOU0FIQEdNQUlMLkNPTSIsInJvbGVzIjpbIjViMjdiZDk2NTg0MmY5NTBhNzc4YzZlZiJdLCJjb3VudHJ5R3JvdXAiOiJJTiIsInR5cGUiOiJVU0VSIn0sImlhdCI6MTczNTU0NjkzMH0.iImf90mFu_cI-xINBv4t0jVz-rWK1zeXOIwIFvkrS0M"


config = Config()

# ===================== LOGGING =====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ===================== BOT INITIALIZATION =====================
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ===================== UTILITY CLASSES =====================
class Resolution:
    """Resolution mapping"""
    MAP = {
        "144": "144x256",
        "240": "240x426",
        "360": "360x640",
        "480": "480x854",
        "720": "720x1280",
        "1080": "1080x1920"
    }
    
    @classmethod
    def get(cls, value: str) -> str:
        return cls.MAP.get(value, "UN")


class URLProcessor:
    """Process and transform URLs for different platforms"""
    
    @staticmethod
    def clean_url(url: str) -> str:
        """Clean and prepare URL"""
        url = url.replace("file/d/", "uc?export=download&id=")
        url = url.replace("www.youtube-nocookie.com/embed", "youtu.be")
        url = url.replace("?modestbranding=1", "")
        url = url.replace("/view?usp=sharing", "")
        return url
    
    @staticmethod
    def get_yt_format(resolution: str) -> str:
        """Get yt-dlp format string"""
        return f"b[height<={resolution}][ext=mp4]/bv[height<={resolution}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
    
    @staticmethod
    def get_default_format(resolution: str) -> str:
        """Get default format string"""
        return f"b[height<={resolution}]/bv[height<={resolution}]+ba/b/bv+ba"
    
    @classmethod
    def process(cls, url: str, resolution: str, token: str = None) -> Tuple[str, str]:
        """
        Process URL based on platform and return (processed_url, format_string)
        """
        original_url = url
        url = cls.clean_url(url)
        
        # Classplus DRM
        if "classplusapp.com/drm/" in url:
            url = 'https://dragoapi.vercel.app/classplus?link=' + url
            # mpd, keys = helper.get_mps_and_keys(url)  # Requires implementation
            # return mpd, f"b[height<={resolution}]"
            
        # Classplus video
        if any(domain in url for domain in [
            "videos.classplusapp", "tencdn.classplusapp", "webvideos.classplusapp.com",
            "media-cdn-alisg.classplusapp.com", "media-cdn-a.classplusapp",
            "media-cdn.classplusapp", "alisg-cdn-a.classplusapp"
        ]):
            try:
                response = requests.get(
                    f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}',
                    headers={'x-access-token': 'eyJjb3Vyc2VJZCI6IjQ1NjY4NyIsInR1dG9ySWQiOm51bGwsIm9yZ0lkIjo0ODA2MTksImNhdGVnb3J5SWQiOm51bGx9r'}
                )
                url = response.json()['url']
            except Exception as e:
                logger.error(f"Classplus processing error: {e}")
        
        # Utkarsh app
        if "apps-s3-jw-prod.utkarshapp.com" in url:
            if 'enc_plain_mp4' in url:
                url = url.replace(url.split("/")[-1], Resolution.get(resolution) + '.mp4')
            elif '.m3u8' in url:
                try:
                    m3u8_data = m3u8.loads(requests.get(url).text)
                    if m3u8_data.data.get('playlists'):
                        q = m3u8_data.data['playlists'][1]['uri'].split("/")[0]
                        x = url.split("/")[5]
                        x = url.replace(x, "")
                        url = m3u8_data.data['playlists'][1]['uri'].replace(q + "/", x)
                except Exception as e:
                    logger.error(f"M3U8 processing error: {e}")
        
        # PW Live
        if "sec-prod-mediacdn.pw.live" in url:
            vid_id = url.split("sec-prod-mediacdn.pw.live/")[1].split("/")[0]
            url = f"https://pwplayer-0e2dbbdc0989.herokuapp.com/player?url=https://d1d34p8vz63oiq.cloudfront.net/{vid_id}/master.mpd?token={token}"
        
        # YouTube embed
        if '?list' in url:
            video_id = url.split("/embed/")[1].split("?")[0]
            url = f"https://www.youtube.com/embed/{video_id}"
        
        # BitGravity to Akamai
        if 'bitgravity.com' in url:
            parts = url.split('/')
            if len(parts) > 6:
                url = f"https://kgs-v2.akamaized.net/{parts[3]}/{parts[4]}/{parts[5]}/{parts[6]}"
        
        # KGS PDF
        if '/do' in url:
            pdf_id = url.split("/")[-1].split(".pdf")[0]
            url = f"https://kgs-v2.akamaized.net/kgs/do/pdfs/{pdf_id}.pdf"
        
        # Cloudflare workers
        if 'workers.dev' in url:
            vid_id = url.split("cloudfront.net/")[1].split("/")[0]
            url = f"https://madxapi-d0cbf6ac738c.herokuapp.com/{vid_id}/master.m3u8?token={token}"
        
        # Psi Offers
        if 'psitoffers.store' in url:
            vid_id = url.split("vid=")[1].split("&")[0]
            url = f"https://madxapi-d0cbf6ac738c.herokuapp.com/{vid_id}/master.m3u8?token={token}"
        
        # PW Player
        if "d1d34p8vz63oiq" in url or "sec1.pw.live" in url:
            vid_id = url.split('/')[-2]
            url = f"https://pwplayer-38c1ae95b681.herokuapp.com/pw?url={url}&token={token}"
        
        # Allen Plus / Vimeo
        if "allenplus" in url or "player.vimeo" in url:
            if "controller/videoplay" in url:
                video_code = url.split("videocode=")[1].split("&videohash=")[0]
                url0 = f"https://player.vimeo.com/video/{video_code}"
                url = f"https://master-api-v3.vercel.app/allenplus-vimeo?url={url0}&authorization=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzkxOTMzNDE5NSIsInRnX3VzZXJuYW1lIjoi4p61IFtvZmZsaW5lXSIsImlhdCI6MTczODY5MjA3N30.SXzZ1MZcvMp5sGESj0hBKSghhxJ3k1GTWoBUbivUe1I"
            else:
                url = f"https://master-api-v3.vercel.app/allenplus-vimeo?url={url}&authorization=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzkxOTMzNDE5NSIsInRnX3VzZXJuYW1lIjoi4p61IFtvZmZsaW5lXSIsImlhdCI6MTczODY5MjA3N30.SXzZ1MZcvMp5sGESj0hBKSghhxJ3k1GTWoBUbivUe1I"
        
        # Amazon AWS
        if 'amazonaws.com' in url:
            url = f"https://master-api-v3.vercel.app/adda-mp4-m3u8?url={url}&quality={resolution}&token={token}"
        
        # Brightcove
        if "edge.api.brightcove.com" in url:
            bcov = 'bcov_auth=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3MjQyMzg3OTEsImNvbiI6eyJpc0FkbWluIjpmYWxzZSwiYXVzZXIiOiJVMFZ6TkdGU2NuQlZjR3h5TkZwV09FYzBURGxOZHowOSIsImlkIjoiZEUxbmNuZFBNblJqVEROVmFWTlFWbXhRTkhoS2R6MDkiLCJmaXJzdF9uYW1lIjoiYVcxV05ITjVSemR6Vm10ak1WUlBSRkF5ZVNzM1VUMDkiLCJlbWFpbCI6Ik5Ga3hNVWhxUXpRNFJ6VlhiR0ppWTJoUk0wMVdNR0pVTlU5clJXSkRWbXRMTTBSU2FHRnhURTFTUlQwPSIsInBob25lIjoiVUhVMFZrOWFTbmQ1ZVcwd1pqUTViRzVSYVc5aGR6MDkiLCJhdmF0YXIiOiJLM1ZzY1M4elMwcDBRbmxrYms4M1JEbHZla05pVVQwOSIsInJlZmVycmFsX2NvZGUiOiJOalZFYzBkM1IyNTBSM3B3VUZWbVRtbHFRVXAwVVQwOSIsImRldmljZV90eXBlIjoiYW5kcm9pZCIsImRldmljZV92ZXJzaW9uIjoiUShBbmRyb2lkIDEwLjApIiwiZGV2aWNlX21vZGVsIjoiU2Ftc3VuZyBTTS1TOTE4QiIsInJlbW90ZV9hZGRyIjoiNTQuMjI2LjI1NS4xNjMsIDU0LjIyNi4yNTUuMTYzIn19.snDdd-PbaoC42OUhn5SJaEGxq0VzfdzO49WTmYgTx8ra_Lz66GySZykpd2SxIZCnrKR6-R10F5sUSrKATv1CDk9ruj_ltCjEkcRq8mAqAytDcEBp72-W0Z7DtGi8LdnY7Vd9Kpaf499P-y3-godolS_7ixClcYOnWxe2nSVD5C9c5HkyisrHTvf6NFAuQC_FD3TzByldbPVKK0ag1UnHRavX8MtttjshnRhv5gJs5DQWj4Ir_dkMcJ4JaVZO3z8j0OxVLjnmuaRBujT-1pavsr1CCzjTbAcBvdjUfvzEhObWfA1-Vl5Y4bUgRHhl1U-0hne4-5fF0aouyu71Y6W0eg'
            url = url.split("bcov_auth")[0] + bcov
        
        # AppX PDF
        if "appx" in url and "pdf" in url:
            url = f"https://dragoapi.vercel.app/pdf/{url}"
        
        # AppX ZIP
        if ".zip" in url:
            url = f"https://video.pablocoder.eu.org/appx-zip?url={url}"
        
        # AppX recordings (FFmpeg direct)
        if "appx-recordings-mcdn.akamai.net.in/drm/" in url or "arvind" in url:
            return url, None  # Will use FFmpeg directly
        
        # Visionias
        if "visionias" in url:
            return url, None  # Handled separately
        
        # Determine format
        if "youtu" in url:
            fmt = cls.get_yt_format(resolution)
        else:
            fmt = cls.get_default_format(resolution)
        
        return url, fmt


class CaptionBuilder:
    """Build captions for different media types"""
    
    @staticmethod
    def video_caption(index: int, title: str, resolution: str, batch: str, credit: str, 
                      url: str = None, bot_name: str = None) -> str:
        bot_name = bot_name or config.BOT_NAME
        if url:
            return f"""**🎞️ VID_ID: {str(index).zfill(3)}.

📝 Title: {title} {bot_name}.mkv

📚 Batch Name: {batch}

**🔗 Video Link - <a href="{url}">__Click Here to Watch Video__</a>

📥 Extracted By : {credit}

**━━━━━✦{bot_name}✦━━━━━**"""
        
        return f"""**🎞️ VID_ID: {str(index).zfill(3)}.

📝 Title: {title} {bot_name} {resolution}.mkv

📚 Batch Name: {batch}

📥 Extracted By : {credit}

**━━━━━✦{bot_name}✦━━━━━**"""
    
    @staticmethod
    def pdf_caption(index: int, title: str, batch: str, credit: str, bot_name: str = None) -> str:
        bot_name = bot_name or config.BOT_NAME
        return f"""**📁 PDF_ID: {str(index).zfill(3)}.

📝 Title: {title} {bot_name}.pdf

📚 Batch Name: {batch}

📥 Extracted By : {credit}

**━━━━━✦{bot_name}✦━━━━━**"""
    
    @staticmethod
    def image_caption(index: int, title: str, ext: str, batch: str, credit: str) -> str:
        return f"""**🖼️ IMG_ID: {str(index).zfill(3)}.

📝 Title: {title} {config.BOT_NAME}.{ext}

📚 Batch Name: {batch}

📥 Extracted By : {credit}

**━━━━━✦{config.BOT_NAME}✦━━━━━**"""
    
    @staticmethod
    def audio_caption(index: int, title: str, ext: str, batch: str, credit: str) -> str:
        return f"""**🎵 MP3_ID: {str(index).zfill(3)}.

📝 Title: {title} {config.BOT_NAME}.{ext}

📚 Batch Name: {batch}

📥 Extracted By : {credit}

**━━━━━✦{config.BOT_NAME}✦━━━━━**"""
    
    @staticmethod
    def zip_caption(index: int, title: str, batch: str, credit: str) -> str:
        return f"""**💾 ZIP_ID: {str(index).zfill(3)}.

📝 Title: {title} {config.BOT_NAME}.zip

📚 Batch Name: {batch}

📥 Extracted By : {credit}

**━━━━━✦{config.BOT_NAME}✦━━━━━**"""


class URLType(Enum):
    """URL type classification"""
    PDF = "pdf"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    ZIP = "zip"
    YOUTUBE = "youtube"
    DRIVE = "drive"
    CLASS_PLUS = "classplus"
    UNKNOWN = "unknown"


class URLClassifier:
    """Classify URLs by type"""
    
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
    AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a"}
    VIDEO_DOMAINS = {"youtu", "youtube", "youtu.be"}
    DRIVE_DOMAINS = {"drive", "drive.google.com"}
    CLASS_PLUS_DOMAINS = {"classplusapp.com", "classplusapp"}
    
    @classmethod
    def classify(cls, url: str) -> URLType:
        url_lower = url.lower()
        
        # YouTube
        if any(domain in url_lower for domain in cls.VIDEO_DOMAINS):
            return URLType.YOUTUBE
        
        # Drive
        if any(domain in url_lower for domain in cls.DRIVE_DOMAINS):
            return URLType.DRIVE
        
        # PDF
        if ".pdf" in url_lower:
            return URLType.PDF
        
        # ZIP
        if ".zip" in url_lower:
            return URLType.ZIP
        
        # ClassPlus
        if any(domain in url_lower for domain in cls.CLASS_PLUS_DOMAINS):
            return URLType.CLASS_PLUS
        
        # Images
        if any(ext in url_lower for ext in cls.IMAGE_EXTENSIONS):
            return URLType.IMAGE
        
        # Audio
        if any(ext in url_lower for ext in cls.AUDIO_EXTENSIONS):
            return URLType.AUDIO
        
        return URLType.VIDEO

# ===================== DOWNLOAD HANDLERS =====================
class DownloadHandler:
    """Handle different types of downloads"""
    
    def __init__(self, bot_client: Client):
        self.bot = bot_client
    
    async def download_and_send(self, url: str, title: str, index: int, batch: str, 
                                credit: str, resolution: str, token: str, thumb: str,
                                message: Message) -> bool:
        """
        Main download and send handler
        """
        url_type = URLClassifier.classify(url)
        name = self._generate_filename(title, index)
        
        # Process URL based on type
        processed_url, fmt = URLProcessor.process(url, resolution, token)
        
        # Determine download command
        cmd = self._build_command(processed_url or url, name, fmt, resolution, url_type)
        
        # Handle by type
        handlers = {
            URLType.DRIVE: self._handle_drive,
            URLType.PDF: self._handle_pdf,
            URLType.IMAGE: self._handle_image,
            URLType.AUDIO: self._handle_audio,
            URLType.ZIP: self._handle_zip,
            URLType.YOUTUBE: self._handle_youtube,
            URLType.CLASS_PLUS: self._handle_classplus,
            URLType.VIDEO: self._handle_video,
        }
        
        handler = handlers.get(url_type, self._handle_video)
        return await handler(processed_url or url, name, title, index, batch, credit, 
                           resolution, token, thumb, message, cmd)
    
    def _generate_filename(self, title: str, index: int) -> str:
        """Generate safe filename"""
        clean = title.replace("\t", "").replace(":", "").replace("/", "")
        clean = clean.replace("+", "").replace("#", "").replace("|", "")
        clean = clean.replace("@", "").replace("*", "").replace(".", "")
        clean = clean.replace("https", "").replace("http", "").strip()
        return f'{str(index).zfill(3)}) {clean[:60]} {config.BOT_NAME}'
    
    def _build_command(self, url: str, name: str, fmt: str, resolution: str, 
                       url_type: URLType) -> str:
        """Build yt-dlp command"""
        if url_type == URLType.YOUTUBE:
            return f'yt-dlp --cookies {config.COOKIES_FILE} -f "{fmt}" "{url}" -o "{name}".mp4'
        elif url_type == URLType.CLASS_PLUS:
            return f'yt-dlp -f "{fmt}" "{url}" -o "{name}.mp4"'
        elif ".ws" in url:
            return None  # HTML download handled separately
        else:
            # Check for special FFmpeg cases
            if "appx-recordings-mcdn.akamai.net.in/drm/" in url or "arvind" in url:
                return f'ffmpeg -i "{url}" -c copy -bsf:a aac_adtstoasc "{name}.mp4"'
            return f'yt-dlp -f "{fmt}" "{url}" -o "{name}.mp4"'
    
    async def _handle_drive(self, url: str, name: str, title: str, index: int, 
                           batch: str, credit: str, resolution: str, token: str,
                           thumb: str, message: Message, cmd: str) -> bool:
        """Handle Google Drive downloads"""
        try:
            ka = await helper.download(url, name)
            caption = CaptionBuilder.pdf_caption(index, title, batch, credit)
            await self.bot.send_document(chat_id=message.chat.id, document=ka, caption=caption)
            os.remove(ka)
            return True
        except FloodWait as e:
            await message.reply_text(str(e))
            time.sleep(e.x)
            return False
    
    async def _handle_pdf(self, url: str, name: str, title: str, index: int,
                         batch: str, credit: str, resolution: str, token: str,
                         thumb: str, message: Message, cmd: str) -> bool:
        """Handle PDF downloads"""
        try:
            # Try yt-dlp first
            if cmd:
                subprocess.run(cmd, shell=True)
                pdf_file = f'{name}.pdf'
                if os.path.exists(pdf_file):
                    caption = CaptionBuilder.pdf_caption(index, title, batch, credit)
                    await self.bot.send_document(chat_id=message.chat.id, document=pdf_file, caption=caption)
                    os.remove(pdf_file)
                    return True
            
            # Fallback to cloudscraper
            url = url.replace(" ", "%20")
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url)
            
            if response.status_code == 200:
                pdf_file = f'{name}.pdf'
                with open(pdf_file, 'wb') as f:
                    f.write(response.content)
                
                caption = CaptionBuilder.pdf_caption(index, title, batch, credit)
                await self.bot.send_document(chat_id=message.chat.id, document=pdf_file, caption=caption)
                os.remove(pdf_file)
                return True
            else:
                await message.reply_text(f"Failed to download PDF: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"PDF download error: {e}")
            await message.reply_text(f"PDF download error: {e}")
            return False
    
    async def _handle_image(self, url: str, name: str, title: str, index: int,
                           batch: str, credit: str, resolution: str, token: str,
                           thumb: str, message: Message, cmd: str) -> bool:
        """Handle image downloads"""
        try:
            ext = url.split('.')[-1].split('?')[0]
            cmd = f'yt-dlp -o "{name}.{ext}" "{url}"'
            subprocess.run(f"{cmd} -R 25 --fragment-retries 25", shell=True)
            
            caption = CaptionBuilder.image_caption(index, title, ext, batch, credit)
            await self.bot.send_document(chat_id=message.chat.id, document=f'{name}.{ext}', caption=caption)
            os.remove(f'{name}.{ext}')
            return True
        except Exception as e:
            logger.error(f"Image download error: {e}")
            await message.reply_text(f"Image download error: {e}")
            return False
    
    async def _handle_audio(self, url: str, name: str, title: str, index: int,
                           batch: str, credit: str, resolution: str, token: str,
                           thumb: str, message: Message, cmd: str) -> bool:
        """Handle audio downloads"""
        try:
            ext = url.split('.')[-1].split('?')[0]
            cmd = f'yt-dlp -x --audio-format {ext} -o "{name}.{ext}" "{url}"'
            subprocess.run(f"{cmd} -R 25 --fragment-retries 25", shell=True)
            
            caption = CaptionBuilder.audio_caption(index, title, ext, batch, credit)
            await self.bot.send_document(chat_id=message.chat.id, document=f'{name}.{ext}', caption=caption)
            os.remove(f'{name}.{ext}')
            return True
        except Exception as e:
            logger.error(f"Audio download error: {e}")
            await message.reply_text(f"Audio download error: {e}")
            return False
    
    async def _handle_zip(self, url: str, name: str, title: str, index: int,
                         batch: str, credit: str, resolution: str, token: str,
                         thumb: str, message: Message, cmd: str) -> bool:
        """Handle ZIP downloads - sends photo placeholder"""
        try:
            caption = CaptionBuilder.zip_caption(index, title, batch, credit)
            await self.bot.send_photo(chat_id=message.chat.id, photo=config.APPX_PHOTO, caption=caption)
            return True
        except Exception as e:
            logger.error(f"ZIP handling error: {e}")
            await message.reply_text(str(e))
            return False
    
    async def _handle_youtube(self, url: str, name: str, title: str, index: int,
                             batch: str, credit: str, resolution: str, token: str,
                             thumb: str, message: Message, cmd: str) -> bool:
        """Handle YouTube - sends photo placeholder"""
        try:
            caption = CaptionBuilder.video_caption(index, title, resolution, batch, credit, url=url)
            await self.bot.send_photo(chat_id=message.chat.id, photo=config.PHOTO_URL, caption=caption)
            return True
        except Exception as e:
            logger.error(f"YouTube handling error: {e}")
            await message.reply_text(str(e))
            return False
    
    async def _handle_classplus(self, url: str, name: str, title: str, index: int,
                               batch: str, credit: str, resolution: str, token: str,
                               thumb: str, message: Message, cmd: str) -> bool:
        """Handle ClassPlus DRM - sends photo placeholder"""
        try:
            caption = CaptionBuilder.video_caption(index, title, resolution, batch, credit, url=url)
            await self.bot.send_photo(chat_id=message.chat.id, photo=config.CP_PHOTO, caption=caption)
            return True
        except Exception as e:
            logger.error(f"ClassPlus handling error: {e}")
            await message.reply_text(str(e))
            return False
    
    async def _handle_video(self, url: str, name: str, title: str, index: int,
                           batch: str, credit: str, resolution: str, token: str,
                           thumb: str, message: Message, cmd: str) -> bool:
        """Handle video downloads"""
        try:
            # Show progress
            total_links = getattr(message, '_total_links', 0)
            show = f"""📥 Downloading »

📝 Title:- `{name}`

**🔗 Total URL »** ✨{total_links}✨

⌨ Quality » {resolution}

**🔗 URL »** `{url}`

**Bot Made By ✦ {config.BOT_NAME}**"""
            prog = await message.reply_text(show)
            
            # Download video
            res_file = await helper.download_video(url, cmd, name)
            
            # Send video
            await prog.delete(True)
            caption = CaptionBuilder.video_caption(index, title, resolution, batch, credit)
            await helper.send_vid(self.bot, message, caption, res_file, thumb, name, prog)
            return True
            
        except Exception as e:
            logger.error(f"Video download error: {e}")
            await message.reply_text(
                f"⌘ Downloading Interrupted ❌ \n\n⌘ Name » {name}\n⌘ Link » `{url}`"
            )
            return False

# ===================== BOT COMMANDS =====================
class BotCommands:
    """Bot command handlers"""
    
    def __init__(self, bot_client: Client):
        self.bot = bot_client
        self.download_handler = DownloadHandler(bot_client)
    
    async def start_command(self, client: Client, message: Message):
        """Handle /start command"""
        user = message.from_user.mention
        start_text = f"""🌟 Welcome {user}! 🌟

I am a powerful TXT Downloader Bot.
Send me a TXT file containing links and I'll download them for you.

**Bot Made BY {config.BOT_NAME}™👨🏻‍💻**
"""
        await message.reply_text(start_text)
    
    async def stop_command(self, client: Client, message: Message):
        """Handle /stop command"""
        await message.delete()
        await message.reply_text("**STOPPED** 🛑", True)
        os.execl(sys.executable, sys.executable, *sys.argv)
    
    async def process_txt_handler(self, client: Client, message: Message, credit: str = None):
        """
        Main TXT file processing handler
        """
        credit = credit or config.DEFAULT_CREDIT
        
        editable = await message.reply_text("**📁 Send me the TXT file and wait.**")
        input_msg: Message = await client.listen(editable.chat.id)
        
        # Download TXT file
        file_path = await input_msg.download()
        await input_msg.delete(True)
        
        # Parse TXT file
        file_name, _ = os.path.splitext(os.path.basename(file_path))
        links = self._parse_txt_file(file_path)
        os.remove(file_path)
        
        if not links:
            await message.reply_text("Invalid file input or no links found.")
            return
        
        # Get user preferences
        await editable.edit(f"Total links found: **{len(links)}**\n\nSend starting index (default: **1**):")
        start_input: Message = await client.listen(editable.chat.id)
        start_index = self._parse_int(start_input.text, 1)
        await start_input.delete(True)
        
        await editable.edit("**Enter Batch Name or send 'd' for filename:**")
        batch_input: Message = await client.listen(editable.chat.id)
        batch_name = file_name if batch_input.text == 'd' else batch_input.text
        await batch_input.delete(True)
        
        await editable.edit("**Enter resolution (e.g., 480, 720):**")
        res_input: Message = await client.listen(editable.chat.id)
        resolution = res_input.text
        await res_input.delete(True)
        
        await editable.edit("**Enter your credit name or send 'de' for default:**")
        credit_input: Message = await client.listen(editable.chat.id)
        if credit_input.text != 'de':
            credit = credit_input.text
        await credit_input.delete(True)
        
        await editable.edit("**Enter PW Token for MPD URL or send 'not' for default:**")
        token_input: Message = await client.listen(editable.chat.id)
        token = config.DEFAULT_TOKEN if token_input.text == 'not' else token_input.text
        await token_input.delete(True)
        
        await editable.edit("**Send thumbnail URL or 'no':**")
        thumb_input: Message = await client.listen(editable.chat.id)
        thumb = await self._process_thumb(thumb_input.text)
        await thumb_input.delete(True)
        await editable.delete()
        
        # Process links
        count = 1
        for i in range(start_index - 1, len(links)):
            link = links[i]
            # Store total for progress display
            message._total_links = len(links)
            
            url = "https://" + link[1] if "://" not in link[1] else link[1]
            title = link[0].replace("\t", "").strip()
            
            success = await self.download_handler.download_and_send(
                url, title, count, batch_name, credit, resolution, token, thumb, message
            )
            
            if success:
                count += 1
            await asyncio.sleep(1)
        
        await message.reply_text("**✅ Successfully Done!**")
    
    def _parse_txt_file(self, file_path: str) -> List[Tuple[str, str]]:
        """Parse TXT file and extract links"""
        links = []
        try:
            with open(file_path, "r") as f:
                content = f.read()
            
            for line in content.split("\n"):
                line = line.strip()
                if not line:
                    continue
                    
                if "://" in line:
                    # Check if line has a title before the URL
                    parts = line.split("://", 1)
                    if len(parts) == 2:
                        # If it starts with a number or has colon, it might be titled
                        if parts[0].strip() and not parts[0].strip().isdigit():
                            links.append((parts[0].strip(), parts[1].strip()))
                        else:
                            links.append((parts[1].strip(), parts[1].strip()))
                    else:
                        links.append((line, line))
                else:
                    links.append((line, line))
        except Exception as e:
            logger.error(f"Error parsing TXT: {e}")
            return []
        return links
    
    def _parse_int(self, value: str, default: int) -> int:
        """Parse integer safely"""
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    async def _process_thumb(self, thumb_input: str) -> str:
        """Process thumbnail URL"""
        if thumb_input == 'no':
            return "no"
        
        if thumb_input.startswith(("http://", "https://")):
            subprocess.getstatusoutput(f"wget '{thumb_input}' -O 'thumb.jpg'")
            return "thumb.jpg"
        
        return "no"

# ===================== WEB SERVER =====================
routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response({"status": "running", "bot": config.BOT_NAME})

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app

# ===================== BOT SETUP =====================
async def start_bot():
    await bot.start()
    logger.info("Bot started successfully")

async def stop_bot():
    await bot.stop()
    logger.info("Bot stopped")

async def main():
    # Register command handlers
    commands = BotCommands(bot)
    
    @bot.on_message(filters.command("start"))
    async def start_cmd(client, message):
        await commands.start_command(client, message)
    
    @bot.on_message(filters.command("stop"))
    async def stop_cmd(client, message):
        await commands.stop_command(client, message)
    
    @bot.on_message(filters.command(["Enger", "ghyig"]))
    async def enger_handler(client, message):
        await commands.process_txt_handler(client, message, config.DEFAULT_CREDIT)
    
    @bot.on_message(filters.command(["radha"]))
    async def radha_handler(client, message):
        await commands.process_txt_handler(client, message, "𝐀𝐍𝐊𝐈𝐓 𝐒𝐇𝐀𝐊𝐘𝐀™🇮🇳")
    
    @bot.on_message(filters.command(["anu"]))
    async def anu_handler(client, message):
        await commands.process_txt_handler(client, message, "𝐀𝐍𝐊𝐈𝐓 𝐒𝐇𝐀𝐊𝐘𝐀™🇮🇳")
    
    @bot.on_message(filters.command(["ankit1"]))
    async def ankit1_handler(client, message):
        await commands.process_txt_handler(client, message, "𝐀𝐍𝐊𝐈𝐓 𝐒𝐇𝐀𝐊𝐘𝐀™🇮🇳")
    
    @bot.on_message(filters.command(["alpha"]))
    async def alpha_handler(client, message):
        await commands.process_txt_handler(client, message, "𝐀𝐍𝐊𝐈𝐓 𝐒𝐇𝐀𝐊𝐘𝐀™🇮🇳")
    
    # Start web server if WEBHOOK is enabled
    if config.WEBHOOK:
        app_runner = web.AppRunner(await web_server())
        await app_runner.setup()
        site = web.TCPSite(app_runner, "0.0.0.0", config.PORT)
        await site.start()
        logger.info(f"Web server started on port {config.PORT}")
    
    # Start bot
    await start_bot()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        await stop_bot()

# ===================== ENTRY POINT =====================
if __name__ == "__main__":
    asyncio.run(main())
