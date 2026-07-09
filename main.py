# ===================================================================
# main.py - BaixarYou - Downloader Universal (VERSÃO MELHORADA)
# ===================================================================
# SUPORTA: YouTube, TikTok, Instagram, Twitter, Facebook, Vimeo, SoundCloud
# MELHORIAS: Validação de URL, Configurações, Testes, Limpar Histórico
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
# CLASSE: Config
# ===================================================================
class Config:
    """Gerenciador de configurações do usuário"""
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
    """
    Valida URL e retorna (is_valid, platform, error_message)
    """
    if not url or not url.strip():
        return False, None, "URL está vazia"
    
    url = url.strip()
    
    # Padrões de validação para cada plataforma
    patterns = {
        'YouTube': [
            r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'^https?://(?:www\.)?youtu\.be/[\w-]+',
            r'^https?://(?:www\.)?youtube\.com/playlist\?list=[\w-]+',
            r'^https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
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
    
    # Verifica se a URL corresponde a algum padrão
    for platform, regex_list in patterns.items():
        for regex in regex_list:
            if re.match(regex, url, re.IGNORECASE):
                return True, platform, None
    
    # Se não encontrou, faz uma validação genérica
    if re.match(r'^https?://[^\s]+$', url):
        return True, "Site Suportado", None
    
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
    
    def _get_ydl_options(self, quality: str, is_playlist: bool) -> dict:
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
            'retries': 5,
            'fragment_retries': 5,
            'skip_unavailable_fragments': True,
            'progress_hooks': [self._progress_hook],
            'verbose': False,
        }
        
        # COOKIES - APENAS SE O ARQUIVO EXISTIR
        if COOKIE_FILE.exists():
            ydl_opts['cookiefile'] = str(COOKIE_FILE)
        
        # HEADERS
        ydl_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        # ÁUDIO
        if quality == "audio":
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        
        return ydl_opts
    
    def _download_video(self, url: str, quality: str, is_playlist: bool):
        title = "Unknown"
        platform = self._detect_platform(url)
        
        # TRATAMENTO ESPECIAL PARA INSTAGRAM (evita 429)
        if platform == "Instagram":
            elapsed = time.time() - self._last_instagram_attempt
            if elapsed < 5:
                wait_time = 5 - elapsed
                self.status_callback(f"⏳ Aguardando {wait_time:.1f}s para evitar bloqueio...")
                time.sleep(wait_time)
            self._last_instagram_attempt = time.time()
        
        try:
            ydl_opts = self._get_ydl_options(quality, is_playlist)
            
            self.status_callback(f"🌐 Conectando a {platform}...")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'entries' in info:
                    entries = info.get('entries', [])
                    total = len(entries)
                    title = info.get('title', 'Playlist')
                    self.status_callback(f"📋 Playlist: {title} ({total} vídeos)")
                    ydl.download([url])
                    self.status_callback(f"✅ Playlist baixada: {title}")
                    self.history.add_download(url, title, platform, "SUCCESS")
                    self._show_success(f"Playlist baixada!\n{total} vídeos salvos em:\n{SAVE_DIR}")
                else:
                    title = info.get('title', 'Unknown')
                    self.status_callback(f"🎬 Baixando: {title[:50]}...")
                    ydl.download([url])
                    self.status_callback(f"✅ Download concluído: {title[:50]}")
                    self.history.add_download(url, title, platform, "SUCCESS")
                    self._show_success(f"Vídeo baixado com sucesso!\n\n📹 {title}\n📁 {SAVE_DIR}")
                    
        except DownloadError as e:
            error_msg = str(e)
            
            # TRATAMENTO ESPECÍFICO PARA ERROS DO INSTAGRAM
            if "429" in error_msg or "Too Many Requests" in error_msg:
                error_msg = "❌ Instagram bloqueou temporariamente (429). Aguarde 5 minutos e tente novamente."
                self.status_callback(f"⏳ {error_msg}")
                self._show_error(error_msg)
            elif "empty media response" in error_msg or "login" in error_msg.lower():
                error_msg = "❌ Instagram exige autenticação. Use cookies.txt (veja dicas abaixo)"
                self.status_callback(f"⚠️ {error_msg}")
                self._show_error(error_msg)
            else:
                self.status_callback(f"❌ {error_msg[:150]}")
                self._show_error(error_msg[:300])
            
            logger.error(f"DownloadError: {url} - {e}")
            self.history.add_download(url, title, platform, "FAILED", str(e))
            
        except ExtractorError as e:
            error_msg = f"URL não suportada: {str(e)[:150]}"
            self.status_callback(f"❌ {error_msg}")
            logger.error(f"ExtractorError: {url} - {e}")
            self.history.add_download(url, title, platform, "FAILED", str(e))
            self._show_error(error_msg)
            
        except Exception as e:
            error_msg = f"Erro: {str(e)[:150]}"
            self.status_callback(f"❌ {error_msg}")
            logger.error(f"Unexpected error: {url} - {e}")
            self.history.add_download(url, title, platform, "FAILED", str(e))
            self._show_error(error_msg)
            
        finally:
            if self._app:
                self._app.after(0, self._app.reset_progress_bar)
    
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
        self.geometry("720x680")
        self.resizable(True, True)
        
        # CARREGA CONFIGURAÇÕES
        self.config = Config()
        self.history = DownloadHistory()
        
        # Usa o diretório salvo da configuração
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
                        text=f"🍪 {cookie_count} cookies - Instagram OK",
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
                text="✅ Pronto para baixar (YouTube, TikTok, Twitter, etc)",
                text_color="green"
            )
            self.cookie_label.configure(
                text="🍪 cookies.txt não encontrado (necessário para Instagram)",
                text_color="orange"
            )
    
    def create_widgets(self):
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=15)
        
        ctk.CTkLabel(header_frame, text="📥 BaixarYou", 
                    font=("Arial", 28, "bold")).pack()
        
        ctk.CTkLabel(header_frame, text="Baixe vídeos de YouTube, Instagram, TikTok, Twitter e mais",
                    font=("Arial", 11), text_color="gray").pack()
        
        # Main
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # URL
        ctk.CTkLabel(main_frame, text="🔗 URL do vídeo:", font=("Arial", 13, "bold")).pack(anchor="w", pady=(10,0))
        
        self.url_entry = ctk.CTkEntry(main_frame, width=700, height=45, 
                                      placeholder_text="Cole a URL aqui... (YouTube, Instagram, TikTok, Twitter, Vimeo)")
        self.url_entry.pack(pady=5, fill="x")
        
        # Botão para validar URL
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
            text="💡 Dicas:",
            font=("Arial", 10, "bold"),
            text_color="gray"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            dica_frame,
            text="• Instagram: use cookies.txt (exporte com extensão 'Get cookies.txt LOCALLY')",
            font=("Arial", 9),
            text_color="gray"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            dica_frame,
            text="• YouTube/TikTok/Twitter: funcionam sem cookies",
            font=("Arial", 9),
            text_color="gray"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            dica_frame,
            text="• Se o Instagram der erro 429, aguarde 5 minutos",
            font=("Arial", 9),
            text_color="gray"
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
        
        # Botão Limpar Histórico
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
    
    def _validate_url(self):
        """Valida a URL inserida e mostra o resultado"""
        url = self.url_entry.get().strip()
        is_valid, platform, error = validate_url(url)
        
        if not is_valid:
            self.url_status_label.configure(
                text=f"❌ {error}",
                text_color="red"
            )
        else:
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
        
        # VALIDAÇÃO DE URL
        is_valid, platform, error = validate_url(url)
        if not is_valid:
            messagebox.showwarning("URL Inválida", f"❌ {error}\n\n"
                                   "Verifique se a URL está correta e completa.\n"
                                   "Exemplo: https://www.youtube.com/watch?v=abc123")
            return
        
        if self.downloading:
            messagebox.showinfo("Aviso", "Um download já está em andamento.")
            return
        
        # Mostra a plataforma detectada
        self.status_label.configure(text=f"📡 Plataforma detectada: {platform}")
        
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
        
        # SALVA CONFIGURAÇÃO DA QUALIDADE
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