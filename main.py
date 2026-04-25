# main.py - BaixarYou Universal
# Suporta YouTube, TikTok, Instagram, Twitter, Vimeo, Facebook, SoundCloud e 1800+ sites

import os
import subprocess
import sys
import threading
import time
import json
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional, Dict, Any

import customtkinter as ctk
import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError

# ==============================
# CONFIGURAÇÃO
# ==============================

def get_base_dir() -> Path:
    """Retorna o diretório base do executável ou script"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent

BASE_DIR = get_base_dir()
SAVE_DIR = BASE_DIR / "Downloads"
SAVE_DIR.mkdir(exist_ok=True)

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Arquivo de histórico
HISTORY_FILE = BASE_DIR / "download_history.json"

# Configuração de logging
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

# ==============================
# CLASSES AUXILIARES
# ==============================

class DownloadHistory:
    """Gerencia o histórico de downloads"""
    
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


class DownloadWorker:
    """Worker responsável por executar downloads"""
    
    def __init__(self, status_callback, progress_callback, history: DownloadHistory):
        self.status_callback = status_callback
        self.progress_callback = progress_callback
        self.history = history
        self.running = True
        
    def start_download(self, url: str, quality: str = "best", is_playlist: bool = False):
        """Inicia o download em uma thread separada"""
        thread = threading.Thread(
            target=self._download_video,
            args=(url, quality, is_playlist),
            daemon=True
        )
        thread.start()
        return thread
    
    def _download_video(self, url: str, quality: str, is_playlist: bool):
        """Executa o download com yt-dlp"""
        title = "Unknown"
        platform = self._detect_platform(url)
        
        try:
            # Configuração universal - funciona em todos os sites
            ydl_opts = self._get_ydl_options(quality, is_playlist)
            
            self.status_callback(f"🌐 Conectando a {platform}...")
            self.status_callback(f"📥 Preparando download: {url[:80]}...")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extrai informações primeiro para mostrar o título
                info = ydl.extract_info(url, download=False)
                
                if 'entries' in info:
                    # É uma playlist
                    entries = info.get('entries', [])
                    total = len(entries)
                    title = info.get('title', 'Playlist')
                    self.status_callback(f"📋 Playlist encontrada: {title} ({total} vídeos)")
                    
                    # Baixa a playlist
                    ydl.download([url])
                    
                    self.status_callback(f"✅ Playlist baixada: {title}")
                    self.history.add_download(url, title, platform, "SUCCESS")
                    self._show_success(f"Playlist baixada!\n{total} vídeos salvos em:\n{SAVE_DIR}")
                else:
                    # É vídeo único
                    title = info.get('title', 'Unknown')
                    duration = info.get('duration', 0)
                    duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "N/A"
                    
                    self.status_callback(f"🎬 Vídeo: {title}")
                    self.status_callback(f"⏱️ Duração: {duration_str}")
                    
                    # Baixa o vídeo
                    ydl.download([url])
                    
                    self.status_callback(f"✅ Download concluído: {title}")
                    self.history.add_download(url, title, platform, "SUCCESS")
                    self._show_success(f"Vídeo baixado com sucesso!\n\n📹 {title}\n📁 {SAVE_DIR}")
                    
        except DownloadError as e:
            error_msg = f"Erro de download: {str(e)[:150]}"
            self.status_callback(f"❌ {error_msg}")
            logger.error(f"DownloadError: {url} - {e}")
            self.history.add_download(url, title, platform, "FAILED", str(e))
            self._show_error(error_msg)
            
        except ExtractorError as e:
            error_msg = f"URL não suportada ou inválida: {str(e)[:150]}"
            self.status_callback(f"❌ {error_msg}")
            logger.error(f"ExtractorError: {url} - {e}")
            self.history.add_download(url, title, platform, "FAILED", str(e))
            self._show_error(error_msg)
            
        except Exception as e:
            error_msg = f"Erro inesperado: {str(e)[:150]}"
            self.status_callback(f"❌ {error_msg}")
            logger.error(f"Unexpected error: {url} - {e}")
            self.history.add_download(url, title, platform, "FAILED", str(e))
            self._show_error(error_msg)
    
    def _get_ydl_options(self, quality: str, is_playlist: bool) -> Dict:
        """Retorna as opções do yt-dlp configuradas para máximo de compatibilidade"""
        
        # Mapeamento de qualidade
        format_map = {
            "best": "bestvideo+bestaudio/best",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "audio": "bestaudio/best",
        }
        
        format_spec = format_map.get(quality, "bestvideo+bestaudio/best")
        
        # Opções base universais
        ydl_opts = {
            'outtmpl': str(SAVE_DIR / '%(title)s_%(id)s.%(ext)s'),
            'format': format_spec,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,  # Não para em erros isolados
            'extract_flat': is_playlist,  # Otimização para playlists
            'retries': 5,  # Número de tentativas
            'fragment_retries': 5,  # Tentativas para DASH/fragmentos
            'skip_unavailable_fragments': True,
            'keepvideo': False,  # Não mantém arquivos temporários
        }
        
        # Headers para simular navegador (importante para muitos sites)
        ydl_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        }
        
        # Para áudio, adiciona pós-processamento
        if quality == "audio":
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        
        # Descomente se tiver problemas com certificados SSL
        # ydl_opts['nocheckcertificate'] = True
        
        return ydl_opts
    
    def _detect_platform(self, url: str) -> str:
        """Detecta a plataforma pela URL"""
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
        if 'dailymotion.com' in url_lower:
            return "DailyMotion"
        if 'bilibili.com' in url_lower:
            return "Bilibili"
        return "Site Suportado"
    
    def _show_success(self, message: str):
        """Mostra mensagem de sucesso (pode ser sobrescrito)"""
        if hasattr(self, '_app'):
            self._app.after(0, lambda: messagebox.showinfo("✅ Sucesso", message))
    
    def _show_error(self, message: str):
        """Mostra mensagem de erro (pode ser sobrescrito)"""
        if hasattr(self, '_app'):
            self._app.after(0, lambda: messagebox.showerror("❌ Erro", message))


class BaixarYouApp(ctk.CTk):
    """Aplicação principal"""
    
    def __init__(self):
        super().__init__()
        
        self.title("📥 BaixarYou Universal - Baixe de Qualquer Plataforma")
        self.geometry("800x700")
        self.resizable(True, True)
        
        # Inicializa histórico
        self.history = DownloadHistory()
        
        # Inicializa worker
        self.worker = DownloadWorker(
            status_callback=self._update_status,
            progress_callback=self._update_progress,
            history=self.history
        )
        # Passa referência da app para o worker
        self.worker._app = self
        
        self.current_download = None
        self.downloading = False
        
        self.create_widgets()
        
    def create_widgets(self):
        """Cria todos os widgets da interface"""
        
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=15)
        
        ctk.CTkLabel(header_frame, text="📥 BaixarYou Universal", 
                    font=("Arial", 28, "bold")).pack()
        
        ctk.CTkLabel(header_frame, text="Baixe vídeos e áudios de YouTube, TikTok, Instagram, Twitter, Vimeo e mais 1800+ sites",
                    font=("Arial", 11), text_color="gray").pack()
        
        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Entrada da URL
        ctk.CTkLabel(main_frame, text="🔗 URL do vídeo ou playlist:", font=("Arial", 13, "bold")).pack(anchor="w", pady=(10,0))
        
        self.url_entry = ctk.CTkEntry(main_frame, width=700, height=45, 
                                      placeholder_text="Cole a URL aqui... (YouTube, TikTok, Instagram, Twitter, Vimeo, etc)")
        self.url_entry.pack(pady=5, fill="x")
        
        # Frame de opções
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=10)
        
        # Qualidade
        ctk.CTkLabel(options_frame, text="Qualidade:", font=("Arial", 12)).pack(side="left", padx=10)
        self.quality_var = ctk.StringVar(value="best")
        quality_menu = ctk.CTkOptionMenu(
            options_frame, 
            values=["best (recomendado)", "1080p", "720p", "480p", "Apenas Áudio (MP3)"],
            variable=self.quality_var,
            width=200
        )
        quality_menu.pack(side="left", padx=10)
        
        # Playlist toggle
        self.playlist_var = ctk.BooleanVar(value=False)
        playlist_check = ctk.CTkCheckBox(
            options_frame, 
            text="📋 É uma playlist (baixar todos os vídeos)",
            variable=self.playlist_var
        )
        playlist_check.pack(side="left", padx=20)
        
        # Botão de download
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
        
        # Frame de status
        status_frame = ctk.CTkFrame(main_frame)
        status_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(status_frame, text="📊 Status:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10)
        
        self.status_label = ctk.CTkLabel(
            status_frame, 
            text="✅ Pronto para baixar",
            font=("Arial", 12),
            text_color="green"
        )
        self.status_label.pack(anchor="w", padx=10, pady=5)
        
        self.progress_label = ctk.CTkLabel(
            status_frame, 
            text="",
            font=("Arial", 11),
            text_color="blue"
        )
        self.progress_label.pack(anchor="w", padx=10, pady=5)
        
        # Separador
        ctk.CTkFrame(main_frame, height=2, fg_color="gray").pack(fill="x", pady=10)
        
        # Frame de botões de pasta
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", pady=5)
        
        self.pasta_btn = ctk.CTkButton(
            buttons_frame, 
            text="📂 Abrir Pasta de Downloads",
            command=self.abrir_pasta,
            width=200
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
            text="📜 Ver Histórico",
            command=self.ver_historico,
            width=150
        )
        self.historico_btn.pack(side="left", padx=5)
        
        # Label da pasta atual
        self.label_pasta = ctk.CTkLabel(
            main_frame, 
            text=f"📁 Pasta atual: {SAVE_DIR}",
            font=("Arial", 11),
            text_color="gray"
        )
        self.label_pasta.pack(pady=10)
        
        # Dicas
        tips_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        tips_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(tips_frame, text="💡 Dicas:", font=("Arial", 11, "bold")).pack(anchor="w")
        ctk.CTkLabel(tips_frame, text="• URLs do Instagram podem precisar de login (use cookies)", 
                    font=("Arial", 10), text_color="gray").pack(anchor="w")
        ctk.CTkLabel(tips_frame, text="• Para áudio MP3, selecione a opção 'Apenas Áudio'", 
                    font=("Arial", 10), text_color="gray").pack(anchor="w")
        ctk.CTkLabel(tips_frame, text="• Playlists do YouTube são suportadas (marque a opção acima)", 
                    font=("Arial", 10), text_color="gray").pack(anchor="w")
    
    def start_download(self):
        """Inicia o processo de download"""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showwarning("Aviso", "Digite ou cole uma URL válida")
            return
        
        if self.downloading:
            messagebox.showinfo("Aviso", "Um download já está em andamento. Aguarde ou use a fila.")
            return
        
        quality_label = self.quality_var.get()
        quality_map = {
            "best (recomendado)": "best",
            "1080p": "1080p",
            "720p": "720p",
            "480p": "480p",
            "Apenás Áudio (MP3)": "audio"
        }
        quality = quality_map.get(quality_label, "best")
        
        is_playlist = self.playlist_var.get()
        
        self.downloading = True
        self.download_btn.configure(state="disabled", text="⏳ BAIXANDO...")
        
        self.current_download = self.worker.start_download(url, quality, is_playlist)
        
        # Monitora quando o download terminar
        self._monitor_download()
    
    def _monitor_download(self):
        """Monitora se o download já terminou"""
        if self.current_download and self.current_download.is_alive():
            self.after(500, self._monitor_download)
        else:
            self.downloading = False
            self.download_btn.configure(state="normal", text="⬇️ BAIXAR VÍDEO")
    
    def _update_status(self, message: str):
        """Atualiza a label de status"""
        def update():
            self.status_label.configure(text=message)
            # Muda cor baseado na mensagem
            if "✅" in message:
                self.status_label.configure(text_color="green")
            elif "❌" in message:
                self.status_label.configure(text_color="red")
            elif "📥" in message or "🌐" in message:
                self.status_label.configure(text_color="blue")
            else:
                self.status_label.configure(text_color="orange")
        self.after(0, update)
    
    def _update_progress(self, message: str):
        """Atualiza a label de progresso"""
        def update():
            self.progress_label.configure(text=message)
        self.after(0, update)
    
    def mudar_pasta(self):
        """Muda a pasta de download"""
        global SAVE_DIR
        pasta = filedialog.askdirectory(title="Escolha a pasta para salvar os vídeos", initialdir=str(SAVE_DIR))
        if pasta:
            SAVE_DIR = Path(pasta)
            self.label_pasta.configure(text=f"📁 Pasta atual: {SAVE_DIR}")
            messagebox.showinfo("Pasta Alterada", f"Downloads agora serão salvos em:\n{SAVE_DIR}")
    
    def abrir_pasta(self):
        """Abre a pasta de downloads no explorer"""
        try:
            if os.name == "nt":
                os.startfile(str(SAVE_DIR))
            else:
                subprocess.run(["xdg-open", str(SAVE_DIR)])
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")
    
    def ver_historico(self):
        """Mostra o histórico de downloads"""
        if not self.history.history:
            messagebox.showinfo("Histórico", "Nenhum download realizado ainda.")
            return
        
        # Cria janela de histórico
        history_window = ctk.CTkToplevel(self)
        history_window.title("📜 Histórico de Downloads")
        history_window.geometry("700x500")
        
        # Listbox para mostrar histórico
        text_box = ctk.CTkTextbox(history_window, font=("Consolas", 10))
        text_box.pack(fill="both", expand=True, padx=10, pady=10)
        
        for item in self.history.history[-20:]:  # Mostra últimos 20
            status_icon = "✅" if item['status'] == "SUCCESS" else "❌"
            text_box.insert("end", f"{status_icon} [{item['platform']}] {item['title'][:60]}\n")
            text_box.insert("end", f"   📅 {item['timestamp'][:19]}\n")
            text_box.insert("end", f"   🔗 {item['url'][:80]}\n")
            text_box.insert("end", "-" * 60 + "\n")
        
        text_box.configure(state="disabled")


# ==============================
# PONTO DE ENTRADA
# ==============================

if __name__ == "__main__":
    app = BaixarYouApp()
    app.mainloop()