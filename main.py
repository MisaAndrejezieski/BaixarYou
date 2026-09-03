# ===================================================================
# main.py - BaixarYou - Downloader Universal (VERSÃO DIAGNÓSTICO)
# ===================================================================
# SUPORTA: YouTube, TikTok, Instagram, Twitter, Facebook, Vimeo, SoundCloud
# CORREÇÕES: Erro 403 Forbidden, múltiplas estratégias de download
# CORREÇÃO: Aceita URLs de embed do YouTube
# VERSÃO: 2.2 - Diagnóstico avançado e mais estratégias
# ===================================================================

import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError

# ===================================================================
# CONFIGURAÇÕES
# ===================================================================

def get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent

BASE_DIR = get_base_dir()
SAVE_DIR = BASE_DIR / "Downloads"
SAVE_DIR.mkdir(exist_ok=True)

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

HISTORY_FILE = BASE_DIR / "download_history.json"
COOKIE_FILE = BASE_DIR / "cookies.txt"
CONFIG_FILE = BASE_DIR / "config.json"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "downloader.log", encoding='utf-8'),
    ]
)
logger = logging.getLogger(__name__)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# ===================================================================
# FUNÇÕES PARA CORRIGIR URLS DO YOUTUBE
# ===================================================================

def extract_video_id_from_url(url: str) -> str:
    """Extrai o ID do vídeo de vários formatos de URL do YouTube"""
    url_clean = url.split('?')[0].split('&')[0]
    
    patterns = [
        r'youtube\.com/watch\?v=([\w-]+)',
        r'youtu\.be/([\w-]+)',
        r'youtube\.com/embed/([\w-]+)',
        r'youtube\.com/v/([\w-]+)',
        r'youtube\.com/shorts/([\w-]+)',
        r'youtube\.com/live/([\w-]+)',
        r'youtube\.com/([a-zA-Z0-9_-]{11})(?:[?/]|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def fix_youtube_url(url: str) -> str:
    """Converte URLs de embed para URLs normais do YouTube"""
    video_id = extract_video_id_from_url(url)
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

# ===================================================================
# FUNÇÃO PARA TESTAR CONEXÃO COM YOUTUBE
# ===================================================================

def test_youtube_connection() -> dict:
    """Testa a conexão com o YouTube e retorna o resultado"""
    import socket
    import urllib.request
    
    result = {
        'success': False,
        'message': '',
        'details': {}
    }
    
    try:
        # Testa DNS
        socket.gethostbyname('www.youtube.com')
        result['details']['dns'] = 'OK'
    except Exception as e:
        result['details']['dns'] = f'Falha: {str(e)}'
        result['message'] = 'Falha no DNS do YouTube'
        return result
    
    try:
        # Testa HTTP
        req = urllib.request.Request(
            'https://www.youtube.com',
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            result['details']['http'] = f'OK (Status: {response.status})'
            result['success'] = True
            result['message'] = 'Conexão com YouTube OK'
    except Exception as e:
        result['details']['http'] = f'Falha: {str(e)}'
        result['message'] = f'Falha ao conectar ao YouTube: {str(e)}'
    
    return result

# ===================================================================
# CLASSE: Config
# ===================================================================
class Config:
    def __init__(self):
        self.config_file = CONFIG_FILE
        self.config = self.load()
    
    def load(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            'save_dir': str(SAVE_DIR),
            'last_quality': 'best (recomendado)',
            'dark_mode': True,
            'max_history': 100,
            'auto_open_folder': False,
            'instagram_wait_seconds': 5
        }
    
    def save(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        self.save()

# ===================================================================
# FUNÇÃO: validate_url
# ===================================================================
def validate_url(url: str) -> tuple:
    if not url or not url.strip():
        return False, None, "URL está vazia"
    
    url = url.strip()
    
    if 'youtube.com' in url or 'youtu.be' in url:
        fixed_url = fix_youtube_url(url)
        if fixed_url != url:
            url = fixed_url
    
    patterns = {
        'YouTube': [
            r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'^https?://(?:www\.)?youtu\.be/[\w-]+',
            r'^https?://(?:www\.)?youtube\.com/playlist\?list=[\w-]+',
            r'^https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
            r'^https?://(?:www\.)?youtube\.com/embed/[\w-]+',
            r'^https?://(?:www\.)?youtube\.com/v/[\w-]+',
            r'^https?://(?:www\.)?youtube\.com/live/[\w-]+',
        ],
        'Instagram': [
            r'^https?://(?:www\.)?instagram\.com/p/[\w-]+/?',
            r'^https?://(?:www\.)?instagram\.com/reel/[\w-]+/?',
            r'^https?://(?:www\.)?instagram\.com/tv/[\w-]+/?',
            r'^https?://(?:www\.)?instagram\.com/stories/[\w-]+/\d+',
        ],
        'TikTok': [
            r'^https?://(?:www\.)?tiktok\.com/@[\w.]+/video/\d+',
            r'^https?://(?:www\.)?tiktok\.com/[\w-]+',
            r'^https?://(?:www\.)?vm\.tiktok\.com/[\w-]+',
        ],
        'Twitter/X': [
            r'^https?://(?:www\.)?twitter\.com/\w+/status/\d+',
            r'^https?://(?:www\.)?x\.com/\w+/status/\d+',
        ],
        'Facebook': [
            r'^https?://(?:www\.)?facebook\.com/[\w.]+/videos/\d+/',
            r'^https?://(?:www\.)?fb\.com/[\w.]+/videos/\d+/',
            r'^https?://(?:www\.)?facebook\.com/watch/\?v=\d+',
        ],
        'Vimeo': [
            r'^https?://(?:www\.)?vimeo\.com/\d+',
            r'^https?://(?:www\.)?vimeo\.com/channels/[\w-]+/\d+',
        ],
        'SoundCloud': [
            r'^https?://(?:www\.)?soundcloud\.com/[\w-]+/[\w-]+',
            r'^https?://(?:www\.)?soundcloud\.com/[\w-]+/sets/[\w-]+',
        ],
        'Twitch': [
            r'^https?://(?:www\.)?twitch\.tv/videos/\d+',
            r'^https?://(?:www\.)?twitch\.tv/\w+/clip/[\w-]+',
        ],
        'Reddit': [
            r'^https?://(?:www\.)?reddit\.com/r/\w+/comments/[\w-]+',
            r'^https?://(?:www\.)?reddit\.com/\w+/comments/[\w-]+',
        ],
    }
    
    for platform, regex_list in patterns.items():
        for regex in regex_list:
            if re.match(regex, url, re.IGNORECASE):
                return True, platform, url
    
    if re.match(r'^https?://[^\s]+$', url):
        return True, "Site Suportado", url
    
    return False, None, "URL inválida ou não suportada"

# ===================================================================
# CLASSE: DownloadHistory
# ===================================================================
class DownloadHistory:
    def __init__(self):
        self.history_file = HISTORY_FILE
        self.history = self.load_history()
    
    def load_history(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def add_download(self, url: str, title: str, platform: str, status: str, error: str = ""):
        self.history.append({
            'url': url,
            'title': title,
            'platform': platform,
            'status': status,
            'error': error,
            'save_dir': str(SAVE_DIR),
            'timestamp': datetime.now().isoformat()
        })
        self.save_history()
    
    def save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def clear(self):
        self.history = []
        self.save_history()

# ===================================================================
# CLASSE: DownloadWorker
# ===================================================================
class DownloadWorker:
    def __init__(self, status_callback, progress_callback, history: DownloadHistory):
        self.status_callback = status_callback
        self.progress_callback = progress_callback
        self.history = history
        self._app = None
        self._last_instagram_attempt = 0
        
    def start_download(self, url: str, quality: str = "best", is_playlist: bool = False):
        thread = threading.Thread(
            target=self._download_video,
            args=(url, quality, is_playlist),
            daemon=True
        )
        thread.start()
        return thread
    
    def _progress_hook(self, d):
        try:
            if d['status'] == 'downloading':
                percent = 0
                if 'total_bytes' in d and d['total_bytes'] > 0:
                    percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                elif 'total_bytes_estimate' in d:
                    percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                
                speed = d.get('speed', 0)
                if speed and speed > 0:
                    if speed > 1024 * 1024:
                        speed_str = f"{speed / 1024 / 1024:.1f} MB/s"
                    elif speed > 1024:
                        speed_str = f"{speed / 1024:.1f} KB/s"
                    else:
                        speed_str = f"{speed:.0f} B/s"
                else:
                    speed_str = "calculando..."
                
                if self._app:
                    self._app.after(0, lambda p=percent, s=speed_str: self._app.update_progress_bar(p, s))
                    
            elif d['status'] == 'finished':
                if self._app:
                    self._app.after(0, lambda: self._app.update_progress_bar(100, "Finalizando..."))
                    
        except Exception:
            pass
    
    def _download_with_ydl(self, url: str, quality: str, is_playlist: bool, strategy_name: str, client: str, use_cookies: str) -> tuple:
        """Tenta baixar com uma estratégia específica"""
        format_map = {
            "best": "bestvideo+bestaudio/best",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "audio": "bestaudio/best",
        }
        
        format_spec = format_map.get(quality, "bestvideo+bestaudio/best")
        
        ydl_opts = {
            'outtmpl': str(SAVE_DIR / '%(title)s_%(id)s.%(ext)s'),
            'format': format_spec,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'extract_flat': is_playlist,
            'retries': 15,
            'fragment_retries': 15,
            'skip_unavailable_fragments': True,
            'progress_hooks': [self._progress_hook],
            'verbose': False,
            'throttledratelimit': 1000000,
            'sleep_interval': 3,
            'max_sleep_interval': 10,
            'sleep_interval_requests': 2,
        }
        
        # CONFIGURAÇÕES PARA YOUTUBE
        ydl_opts['extractor_args'] = {
            'youtube': {
                'skip': ['dash', 'hls'],
                'player_client': [client],
                'player_skip': ['configs', 'webpage'],
            }
        }
        
        # CONFIGURA COOKIES
        if use_cookies == 'browser':
            try:
                ydl_opts['cookiesfrombrowser'] = ('chrome',)
                self.status_callback(f"🍪 Usando cookies do Chrome")
            except:
                pass
        elif use_cookies == 'file' and COOKIE_FILE.exists():
            ydl_opts['cookiefile'] = str(COOKIE_FILE)
            self.status_callback(f"🍪 Usando cookies.txt")
        elif use_cookies == 'firefox':
            try:
                ydl_opts['cookiesfrombrowser'] = ('firefox',)
                self.status_callback(f"🍪 Usando cookies do Firefox")
            except:
                pass
        
        # HEADERS
        ydl_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Sec-Ch-Ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
        }
        
        # ÁUDIO
        if quality == "audio":
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        
        self.status_callback(f"🔄 Tentando: {strategy_name}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                raise Exception("Não foi possível obter informações do vídeo")
            
            if 'entries' in info:
                entries = info.get('entries', [])
                total = len(entries)
                title = info.get('title', 'Playlist')
                
                if total == 0:
                    raise Exception("Playlist vazia")
                
                ydl.download([url])
                return 'playlist', title, total
            else:
                title = info.get('title', 'Unknown')
                ydl.download([url])
                return 'video', title, None
    
    def _download_video(self, url: str, quality: str, is_playlist: bool):
        title = "Unknown"
        
        # CORRIGE URL DO YOUTUBE
        if 'youtube.com' in url or 'youtu.be' in url:
            fixed_url = fix_youtube_url(url)
            if fixed_url != url:
                self.status_callback(f"🔄 URL corrigida: {fixed_url[:60]}...")
                url = fixed_url
        
        platform = self._detect_platform(url)
        
        # TESTA CONEXÃO COM YOUTUBE
        if platform == "YouTube":
            self.status_callback("🔍 Testando conexão com YouTube...")
            test_result = test_youtube_connection()
            if not test_result['success']:
                self.status_callback(f"⚠️ {test_result['message']}")
                self._show_error(
                    f"❌ Problema de conexão com YouTube!\n\n"
                    f"{test_result['message']}\n\n"
                    f"💡 Verifique:\n"
                    f"• Sua conexão com a internet\n"
                    f"• Firewall/antivírus\n"
                    f"• VPN/proxy\n"
                    f"• Tente reiniciar o roteador"
                )
                return
        
        # TRATAMENTO INSTAGRAM
        if platform == "Instagram":
            elapsed = time.time() - self._last_instagram_attempt
            if elapsed < 5:
                wait_time = 5 - elapsed
                self.status_callback(f"⏳ Aguardando {wait_time:.1f}s...")
                time.sleep(wait_time)
            self._last_instagram_attempt = time.time()
        
        # ESTRATÉGIAS DE DOWNLOAD - MAIS COMPLETAS
        strategies = [
            # Com cookies do navegador
            ('Chrome + Web', 'web', 'browser'),
            ('Chrome + Android', 'android', 'browser'),
            ('Chrome + iOS', 'ios', 'browser'),
            ('Firefox + Web', 'web', 'firefox'),
            # Com cookies.txt
            ('cookies.txt + Web', 'web', 'file'),
            ('cookies.txt + Android', 'android', 'file'),
            ('cookies.txt + iOS', 'ios', 'file'),
            # Sem cookies
            ('Sem cookies + Web', 'web', 'none'),
            ('Sem cookies + Android', 'android', 'none'),
            ('Sem cookies + iOS', 'ios', 'none'),
        ]
        
        last_error = None
        
        for strategy_name, client, use_cookies in strategies:
            try:
                result_type, title, count = self._download_with_ydl(
                    url, quality, is_playlist, strategy_name, client, use_cookies
                )
                
                if result_type == 'playlist':
                    self.status_callback(f"✅ Playlist baixada: {title} ({count} vídeos)")
                    self.history.add_download(url, title, platform, "SUCCESS")
                    self._show_success(f"Playlist baixada!\n{count} vídeos salvos em:\n{SAVE_DIR}")
                    return
                else:
                    self.status_callback(f"✅ Download concluído: {title[:50]}")
                    self.history.add_download(url, title, platform, "SUCCESS")
                    self._show_success(f"Vídeo baixado com sucesso!\n\n📹 {title}\n📁 {SAVE_DIR}")
                    return
                    
            except (DownloadError, ExtractorError) as e:
                error_msg = str(e)
                last_error = e
                
                # Erros críticos que param a tentativa
                if "Sign in to confirm" in error_msg or "bot" in error_msg.lower():
                    self._show_error(
                        f"❌ YouTube pede verificação humana.\n\n"
                        f"💡 SOLUÇÃO URGENTE:\n"
                        f"1. Abra o YouTube no navegador\n"
                        f"2. Faça login na sua conta Google\n"
                        f"3. Acesse o vídeo manualmente\n"
                        f"4. Aguarde 5 minutos\n"
                        f"5. Exporte um novo cookies.txt\n"
                        f"6. Tente novamente"
                    )
                    return
                
                if "403" in error_msg or "Forbidden" in error_msg:
                    self.status_callback(f"⚠️ Estratégia falhou (403), tentando próxima...")
                    continue
                
                # Instagram
                if "429" in error_msg:
                    self._show_error("❌ Instagram bloqueou (429). Aguarde 5 minutos.")
                    self.history.add_download(url, title, platform, "FAILED", str(e))
                    return
                    
                self.status_callback(f"⚠️ Erro: {error_msg[:80]}... tentando próxima")
                continue
                
            except Exception as e:
                last_error = e
                self.status_callback(f"⚠️ Erro: {str(e)[:80]}... tentando próxima")
                continue
        
        # TODAS ESTRATÉGIAS FALHARAM
        error_detail = str(last_error) if last_error else "Desconhecido"
        self.status_callback("❌ Todas as estratégias falharam.")
        
        # MENSAGEM DE ERRO DETALHADA
        if "Sign in to confirm" in error_detail or "bot" in error_detail.lower():
            error_msg = (
                f"❌ YouTube está pedindo verificação humana.\n\n"
                f"🔥 SOLUÇÃO DEFINITIVA:\n\n"
                f"1️⃣ Abra o YouTube no Chrome\n"
                f"2️⃣ Faça login na sua conta\n"
                f"3️⃣ Assista ao vídeo por alguns segundos\n"
                f"4️⃣ Instale a extensão 'Get cookies.txt LOCALLY'\n"
                f"5️⃣ Exporte o cookies.txt\n"
                f"6️⃣ Cole na pasta do programa\n"
                f"7️⃣ Tente novamente\n\n"
                f"⚠️ O YouTube bloqueia downloads de contas não autenticadas!"
            )
        elif "403" in error_detail:
            error_msg = (
                f"❌ YouTube bloqueou o download (403).\n\n"
                f"🔥 SOLUÇÃO:\n\n"
                f"1️⃣ Atualize o yt-dlp:\n"
                f"   pip install --upgrade yt-dlp\n\n"
                f"2️⃣ Exporte cookies atualizados:\n"
                f"   • Extensão 'Get cookies.txt LOCALLY'\n"
                f"   • Faça login no YouTube\n"
                f"   • Exporte para a pasta do programa\n\n"
                f"3️⃣ Aguarde 10 minutos e tente novamente\n\n"
                f"4️⃣ Se ainda falhar, tente com uma VPN"
            )
        else:
            error_msg = (
                f"❌ Falha ao baixar o vídeo.\n\n"
                f"📋 Último erro: {error_detail[:200]}\n\n"
                f"🔥 SOLUÇÕES:\n\n"
                f"1️⃣ Atualize o yt-dlp:\n"
                f"   pip install --upgrade yt-dlp\n\n"
                f"2️⃣ Instale a extensão 'Get cookies.txt LOCALLY'\n"
                f"   • Faça login no YouTube\n"
                f"   • Exporte o cookies.txt\n"
                f"   • Cole na pasta do programa\n\n"
                f"3️⃣ Teste sua conexão:\n"
                f"   • Desative VPN/proxy\n"
                f"   • Desative firewall temporariamente\n"
                f"   • Use outra rede (ex: Wi-Fi diferente)\n\n"
                f"4️⃣ Aguarde 10-15 minutos e tente novamente"
            )
        
        self._show_error(error_msg)
        self.history.add_download(url, title, platform, "FAILED", str(last_error))
    
    def _detect_platform(self, url: str) -> str:
        url_lower = url.lower()
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return "YouTube"
        if 'tiktok.com' in url_lower:
            return "TikTok"
        if 'instagram.com' in url_lower:
            return "Instagram"
        if 'twitter.com' in url_lower or 'x.com' in url_lower:
            return "Twitter/X"
        if 'facebook.com' in url_lower or 'fb.com' in url_lower:
            return "Facebook"
        if 'vimeo.com' in url_lower:
            return "Vimeo"
        if 'soundcloud.com' in url_lower:
            return "SoundCloud"
        if 'twitch.tv' in url_lower:
            return "Twitch"
        if 'reddit.com' in url_lower:
            return "Reddit"
        return "Site Suportado"
    
    def _show_success(self, message: str):
        if self._app:
            self._app.after(0, lambda: messagebox.showinfo("✅ Sucesso", message))
    
    def _show_error(self, message: str):
        if self._app:
            self._app.after(0, lambda: messagebox.showerror("❌ Erro", message))

# ===================================================================
# CLASSE: BaixarYouApp - INTERFACE GRÁFICA
# ===================================================================
class BaixarYouApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("📥 BaixarYou - Downloader Universal")
        self.geometry("720x800")
        self.resizable(True, True)
        
        self.config = Config()
        self.history = DownloadHistory()
        
        global SAVE_DIR
        saved_dir = self.config.get('save_dir')
        if saved_dir and Path(saved_dir).exists():
            SAVE_DIR = Path(saved_dir)
        
        self.worker = DownloadWorker(
            status_callback=self._update_status,
            progress_callback=self._update_progress,
            history=self.history
        )
        self.worker._app = self
        
        self.current_download = None
        self.downloading = False
        self.corrected_url = None
        
        self.create_widgets()
        self._check_cookie_status()
    
    def _check_cookie_status(self):
        if COOKIE_FILE.exists():
            try:
                with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    cookie_count = sum(1 for line in lines if line.strip() and not line.startswith('#'))
                    self.status_label.configure(
                        text=f"✅ cookies.txt carregado ({cookie_count} cookies)",
                        text_color="green"
                    )
                    self.cookie_label.configure(
                        text=f"🍪 {cookie_count} cookies - YouTube/Instagram OK",
                        text_color="green"
                    )
            except:
                self.status_label.configure(
                    text="⚠️ cookies.txt corrompido",
                    text_color="orange"
                )
                self.cookie_label.configure(
                    text="🍪 cookies.txt corrompido",
                    text_color="orange"
                )
        else:
            self.status_label.configure(
                text="⚠️ cookies.txt não encontrado - YouTube pode bloquear",
                text_color="orange"
            )
            self.cookie_label.configure(
                text="🍪 Exporte cookies com 'Get cookies.txt LOCALLY'",
                text_color="orange"
            )
    
    def create_widgets(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=15)
        
        ctk.CTkLabel(header_frame, text="📥 BaixarYou", 
                    font=("Arial", 28, "bold")).pack()
        
        ctk.CTkLabel(header_frame, text="Baixe vídeos de YouTube, Instagram, TikTok, Twitter e mais",
                    font=("Arial", 11), text_color="gray").pack()
        
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # URL
        ctk.CTkLabel(main_frame, text="🔗 URL do vídeo:", font=("Arial", 13, "bold")).pack(anchor="w", pady=(10,0))
        
        self.url_entry = ctk.CTkEntry(main_frame, width=700, height=45, 
                                      placeholder_text="Cole a URL aqui... (YouTube, Instagram, TikTok, Twitter, Vimeo)")
        self.url_entry.pack(pady=5, fill="x")
        
        url_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        url_frame.pack(fill="x", pady=(0, 10))
        
        self.validate_btn = ctk.CTkButton(
            url_frame,
            text="🔍 Validar URL",
            command=self._validate_url,
            width=150,
            height=30,
            font=("Arial", 11),
            fg_color="#1565C0",
            hover_color="#0D47A1"
        )
        self.validate_btn.pack(side="left")
        
        self.url_status_label = ctk.CTkLabel(
            url_frame,
            text="",
            font=("Arial", 11)
        )
        self.url_status_label.pack(side="left", padx=15)
        
        # Botão testar conexão
        self.test_btn = ctk.CTkButton(
            url_frame,
            text="🌐 Testar Conexão",
            command=self._test_connection,
            width=150,
            height=30,
            font=("Arial", 11),
            fg_color="#F57C00",
            hover_color="#E65100"
        )
        self.test_btn.pack(side="left", padx=5)
        
        # Opções
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(options_frame, text="Qualidade:", font=("Arial", 12)).pack(side="left", padx=10)
        
        self.quality_var = ctk.StringVar(value=self.config.get('last_quality', 'best (recomendado)'))
        quality_menu = ctk.CTkOptionMenu(
            options_frame, 
            values=["best (recomendado)", "1080p", "720p", "480p", "Apenas Áudio (MP3)"],
            variable=self.quality_var,
            width=200
        )
        quality_menu.pack(side="left", padx=10)
        
        self.playlist_var = ctk.BooleanVar(value=False)
        playlist_check = ctk.CTkCheckBox(
            options_frame, 
            text="📋 Playlist (baixar todos)",
            variable=self.playlist_var
        )
        playlist_check.pack(side="left", padx=20)
        
        # Botão Download
        self.download_btn = ctk.CTkButton(
            main_frame, 
            text="⬇️ BAIXAR VÍDEO",
            command=self.start_download,
            width=300, 
            height=50,
            font=("Arial", 16, "bold"),
            fg_color="#2e7d32",
            hover_color="#1b5e20"
        )
        self.download_btn.pack(pady=15)
        
        # Progresso
        progress_frame = ctk.CTkFrame(main_frame)
        progress_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(progress_frame, text="📊 Progresso:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10)
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=500, height=20)
        self.progress_bar.pack(pady=5, padx=10, fill="x")
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(progress_frame, text="0% - Aguardando...", font=("Arial", 11))
        self.progress_label.pack(anchor="w", padx=10, pady=5)
        
        # Status
        status_frame = ctk.CTkFrame(main_frame)
        status_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(status_frame, text="Status:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10)
        
        self.status_label = ctk.CTkLabel(
            status_frame, 
            text="✅ Pronto para baixar",
            font=("Arial", 12),
            text_color="green"
        )
        self.status_label.pack(anchor="w", padx=10, pady=5)
        
        self.cookie_label = ctk.CTkLabel(
            status_frame,
            text="🍪 Verificando cookies.txt...",
            font=("Arial", 10),
            text_color="gray"
        )
        self.cookie_label.pack(anchor="w", padx=10, pady=2)
        
        # Dicas
        dica_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        dica_frame.pack(anchor="w", padx=10, pady=5, fill="x")
        
        ctk.CTkLabel(
            dica_frame,
            text="⚠️ IMPORTANTE - YouTube está bloqueando downloads!",
            font=("Arial", 10, "bold"),
            text_color="red"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            dica_frame,
            text="➡️ Use cookies.txt (extensão 'Get cookies.txt LOCALLY')",
            font=("Arial", 9),
            text_color="orange"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            dica_frame,
            text="➡️ Faça login no YouTube antes de exportar os cookies",
            font=("Arial", 9),
            text_color="orange"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            dica_frame,
            text="➡️ Se falhar, aguarde 10-15 minutos e tente novamente",
            font=("Arial", 9),
            text_color="orange"
        ).pack(anchor="w")
        
        # Botões auxiliares
        ctk.CTkFrame(main_frame, height=2, fg_color="gray").pack(fill="x", pady=10)
        
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", pady=5)
        
        self.pasta_btn = ctk.CTkButton(
            buttons_frame, 
            text="📂 Abrir Pasta",
            command=self.abrir_pasta,
            width=150
        )
        self.pasta_btn.pack(side="left", padx=5)
        
        self.mudar_pasta_btn = ctk.CTkButton(
            buttons_frame, 
            text="🗂️ Mudar Pasta",
            command=self.mudar_pasta,
            width=150
        )
        self.mudar_pasta_btn.pack(side="left", padx=5)
        
        self.historico_btn = ctk.CTkButton(
            buttons_frame, 
            text="📜 Histórico",
            command=self.ver_historico,
            width=150
        )
        self.historico_btn.pack(side="left", padx=5)
        
        self.limpar_historico_btn = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Limpar Histórico",
            command=self.limpar_historico,
            width=150,
            fg_color="#c62828",
            hover_color="#b71c1c"
        )
        self.limpar_historico_btn.pack(side="left", padx=5)
        
        self.label_pasta = ctk.CTkLabel(
            main_frame, 
            text=f"📁 Pasta: {SAVE_DIR}",
            font=("Arial", 11),
            text_color="gray"
        )
        self.label_pasta.pack(pady=10)
    
    def _test_connection(self):
        """Testa a conexão com o YouTube"""
        self.status_label.configure(text="🔍 Testando conexão...", text_color="blue")
        self.update()
        
        result = test_youtube_connection()
        
        if result['success']:
            messagebox.showinfo(
                "✅ Conexão OK",
                f"Conexão com YouTube funcionando!\n\n"
                f"DNS: {result['details'].get('dns', 'OK')}\n"
                f"HTTP: {result['details'].get('http', 'OK')}"
            )
            self.status_label.configure(text="✅ Conexão com YouTube OK", text_color="green")
        else:
            messagebox.showerror(
                "❌ Falha na Conexão",
                f"Falha ao conectar ao YouTube!\n\n"
                f"{result['message']}\n\n"
                f"Detalhes:\n"
                f"DNS: {result['details'].get('dns', 'N/A')}\n"
                f"HTTP: {result['details'].get('http', 'N/A')}\n\n"
                f"💡 Verifique:\n"
                f"• Sua conexão com a internet\n"
                f"• Firewall/antivírus\n"
                f"• VPN/proxy"
            )
            self.status_label.configure(text="❌ Falha na conexão", text_color="red")
    
    def _validate_url(self):
        url = self.url_entry.get().strip()
        is_valid, platform, corrected_url = validate_url(url)
        
        if not is_valid:
            self.url_status_label.configure(
                text=f"❌ {platform}",
                text_color="red"
            )
            self.corrected_url = None
        else:
            if corrected_url and corrected_url != url:
                self.corrected_url = corrected_url
                self.url_status_label.configure(
                    text=f"✅ URL corrigida: {corrected_url[:60]}...",
                    text_color="green"
                )
            else:
                self.corrected_url = url
                self.url_status_label.configure(
                    text=f"✅ URL válida - Plataforma: {platform}",
                    text_color="green"
                )
    
    def update_progress_bar(self, percent: float, speed: str):
        try:
            percent_value = min(100, max(0, float(percent))) / 100
            self.progress_bar.set(percent_value)
            percent_int = int(percent_value * 100)
            self.progress_label.configure(text=f"{percent_int}% - {speed}")
            self.update_idletasks()
        except:
            pass
    
    def reset_progress_bar(self):
        self.progress_bar.set(0)
        self.progress_label.configure(text="0% - Concluído!")
        self.after(2000, lambda: self.progress_label.configure(text="0% - Aguardando..."))
    
    def _update_status(self, message: str):
        def update():
            self.status_label.configure(text=message)
            if "✅" in message:
                self.status_label.configure(text_color="green")
            elif "❌" in message:
                self.status_label.configure(text_color="red")
            else:
                self.status_label.configure(text_color="blue")
        self.after(0, update)
    
    def _update_progress(self, message: str):
        def update():
            self.progress_label.configure(text=message)
        self.after(0, update)
    
    def start_download(self):
        url = self.url_entry.get().strip()
        
        is_valid, platform, corrected_url = validate_url(url)
        if not is_valid:
            messagebox.showwarning("URL Inválida", f"❌ {platform}\n\n"
                                   "Verifique se a URL está correta.\n"
                                   "Exemplo: https://www.youtube.com/watch?v=abc123")
            return
        
        if corrected_url and corrected_url != url:
            url = corrected_url
            self.url_entry.delete(0, 'end')
            self.url_entry.insert(0, url)
            self.status_label.configure(text=f"🔄 URL corrigida")
        
        if self.downloading:
            messagebox.showinfo("Aviso", "Um download já está em andamento.")
            return
        
        self.status_label.configure(text=f"📡 Plataforma: {platform}")
        
        self.progress_bar.set(0)
        self.progress_label.configure(text="0% - Iniciando...")
        
        quality_label = self.quality_var.get()
        quality_map = {
            "best (recomendado)": "best",
            "1080p": "1080p",
            "720p": "720p",
            "480p": "480p",
            "Apenas Áudio (MP3)": "audio"
        }
        quality = quality_map.get(quality_label, "best")
        is_playlist = self.playlist_var.get()
        
        self.config.set('last_quality', quality_label)
        
        self.downloading = True
        self.download_btn.configure(state="disabled", text="⏳ BAIXANDO...")
        
        self.current_download = self.worker.start_download(url, quality, is_playlist)
        self._monitor_download()
    
    def _monitor_download(self):
        if self.current_download and self.current_download.is_alive():
            self.after(500, self._monitor_download)
        else:
            self.downloading = False
            self.download_btn.configure(state="normal", text="⬇️ BAIXAR VÍDEO")
    
    def mudar_pasta(self):
        global SAVE_DIR
        pasta = filedialog.askdirectory(title="Escolha a pasta", initialdir=str(SAVE_DIR))
        if pasta:
            SAVE_DIR = Path(pasta)
            self.label_pasta.configure(text=f"📁 Pasta: {SAVE_DIR}")
            self.config.set('save_dir', str(SAVE_DIR))
            messagebox.showinfo("Pasta Alterada", f"Downloads salvos em:\n{SAVE_DIR}")
    
    def abrir_pasta(self):
        try:
            if os.name == "nt":
                os.startfile(str(SAVE_DIR))
            else:
                subprocess.run(["xdg-open", str(SAVE_DIR)])
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")
    
    def ver_historico(self):
        if not self.history.history:
            messagebox.showinfo("Histórico", "Nenhum download realizado ainda.")
            return
        
        history_window = ctk.CTkToplevel(self)
        history_window.title("📜 Histórico de Downloads")
        history_window.geometry("700x550")
        
        main_frame = ctk.CTkFrame(history_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        text_box = ctk.CTkTextbox(main_frame, font=("Consolas", 10))
        text_box.pack(fill="both", expand=True, pady=(0, 10))
        
        for item in self.history.history[-20:]:
            status_icon = "✅" if item['status'] == "SUCCESS" else "❌"
            text_box.insert("end", f"{status_icon} [{item['platform']}] {item['title'][:60]}\n")
            text_box.insert("end", f"   📅 {item['timestamp'][:19]}\n")
            text_box.insert("end", f"   🔗 {item['url'][:80]}\n")
            text_box.insert("end", "-" * 60 + "\n")
        
        text_box.configure(state="disabled")
        
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(fill="x")
        
        def limpar_historico_janela():
            if messagebox.askyesno("Confirmar", "Deseja realmente limpar todo o histórico?"):
                self.history.clear()
                text_box.configure(state="normal")
                text_box.delete("1.0", "end")
                text_box.insert("end", "🗑️ Histórico limpo com sucesso!")
                text_box.configure(state="disabled")
                messagebox.showinfo("Histórico", "Histórico limpo!")
        
        ctk.CTkButton(btn_frame, text="🗑️ Limpar Histórico", 
                      command=limpar_historico_janela, fg_color="#c62828").pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Fechar", 
                      command=history_window.destroy).pack(side="right", padx=5)
    
    def limpar_historico(self):
        if not self.history.history:
            messagebox.showinfo("Histórico", "Nenhum download no histórico.")
            return
        
        if messagebox.askyesno("Confirmar", "Deseja realmente limpar todo o histórico de downloads?"):
            self.history.clear()
            messagebox.showinfo("Histórico", "Histórico limpo com sucesso!")

# ===================================================================
# PONTO DE ENTRADA
# ===================================================================
if __name__ == "__main__":
    app = BaixarYouApp()
    app.mainloop()