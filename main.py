# ===================================================================
# main.py - BaixarYou VERSÃO FINAL DEFINITIVA
# ===================================================================
# USA SUBPROCESS PARA CHAMAR O YT-DLP DIRETAMENTE
# ===================================================================

import json
import logging
import os
import re
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

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

# ===================================================================
# CLASSE: DownloadWorker - USA SUBPROCESS
# ===================================================================
class DownloadWorker:
    def __init__(self, status_callback, progress_callback, history: DownloadHistory):
        self.status_callback = status_callback
        self.progress_callback = progress_callback
        self.history = history
        self._app = None
        self.process = None
        
    def start_download(self, url: str, quality: str = "best", is_playlist: bool = False):
        thread = threading.Thread(
            target=self._download_video,
            args=(url, quality, is_playlist),
            daemon=True
        )
        thread.start()
        return thread
    
    def _download_video(self, url: str, quality: str, is_playlist: bool):
        """Usa subprocess para chamar o yt-dlp"""
        
        platform = self._detect_platform(url)
        title = "Unknown"
        
        try:
            self.status_callback(f"🌐 Conectando a {platform}...")
            
            # ==============================================================
            # CONSTRÓI O COMANDO
            # ==============================================================
            cmd = [
                "yt-dlp",
                "--no-warnings",
                "--ignore-errors",
                "--retries", "10",
                "--fragment-retries", "10",
            ]
            
            # Adiciona cookies se existir
            if COOKIE_FILE.exists():
                cmd.extend(["--cookies", str(COOKIE_FILE)])
                self.status_callback(f"🍪 Usando cookies.txt")
            
            # Qualidade
            quality_map = {
                "best": "-f bestvideo+bestaudio/best",
                "1080p": "-f bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                "720p": "-f bestvideo[height<=720]+bestaudio/best[height<=720]",
                "480p": "-f bestvideo[height<=480]+bestaudio/best[height<=480]",
                "audio": "-f bestaudio/best --extract-audio --audio-format mp3 --audio-quality 192K",
            }
            
            quality_cmd = quality_map.get(quality, "-f bestvideo+bestaudio/best")
            if quality_cmd:
                cmd.extend(quality_cmd.split())
            
            # Playlist
            if is_playlist:
                cmd.append("--yes-playlist")
            else:
                cmd.append("--no-playlist")
            
            # Saída
            cmd.extend(["-o", str(SAVE_DIR / "%(title)s_%(id)s.%(ext)s")])
            
            # URL
            cmd.append(url)
            
            # ==============================================================
            # EXECUTA O COMANDO
            # ==============================================================
            self.status_callback(f"⏳ Baixando...")
            
            # Executa e captura a saída
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            # Verifica se deu erro
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                if "empty media response" in str(error_msg) or "login" in str(error_msg).lower():
                    error_msg = "❌ Instagram exige login! Use cookies.txt"
                raise Exception(error_msg[:200])
            
            # Tenta extrair o título da saída
            title_match = re.search(r'\[download\] Destination: .*?\\(.+?)\.', result.stdout)
            if title_match:
                title = title_match.group(1)
            else:
                title = "Vídeo"
            
            # Sucesso
            self.status_callback(f"✅ Download concluído: {title[:50]}")
            self.history.add_download(url, title, platform, "SUCCESS")
            self._show_success(f"Vídeo baixado com sucesso!\n\n📹 {title}\n📁 {SAVE_DIR}")
            
        except subprocess.TimeoutExpired:
            error_msg = "⏰ Tempo limite excedido"
            self.status_callback(f"❌ {error_msg}")
            self.history.add_download(url, title, platform, "FAILED", error_msg)
            self._show_error(error_msg)
            
        except Exception as e:
            error_msg = str(e)[:200]
            self.status_callback(f"❌ {error_msg}")
            logger.error(f"Error: {url} - {e}")
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
# CLASSE: BaixarYouApp
# ===================================================================
class BaixarYouApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("📥 BaixarYou - Downloader Universal")
        self.geometry("700x680")
        self.resizable(True, True)
        
        self.history = DownloadHistory()
        
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
                text="⚠️ SEM cookies.txt - Instagram NÃO funciona!",
                text_color="red"
            )
            self.cookie_label.configure(
                text="🍪 cookies.txt não encontrado",
                text_color="red"
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
                                      placeholder_text="Cole a URL aqui...")
        self.url_entry.pack(pady=5, fill="x")
        
        # Opções
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(options_frame, text="Qualidade:", font=("Arial", 12)).pack(side="left", padx=10)
        
        self.quality_var = ctk.StringVar(value="best (recomendado)")
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
            text="📋 Playlist",
            variable=self.playlist_var
        )
        playlist_check.pack(side="left", padx=20)
        
        # Botão
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
            text="💡 Como exportar cookies para o Instagram:",
            font=("Arial", 10, "bold"),
            text_color="gray"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            dica_frame,
            text="1. Instale 'Get cookies.txt LOCALLY' no Edge/Chrome",
            font=("Arial", 9),
            text_color="gray"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            dica_frame,
            text="2. Faça login no Instagram, clique na extensão e exporte",
            font=("Arial", 9),
            text_color="gray"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            dica_frame,
            text="3. Salve como 'cookies.txt' na pasta do BaixarYou",
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
        
        self.label_pasta = ctk.CTkLabel(
            main_frame, 
            text=f"📁 Pasta: {SAVE_DIR}",
            font=("Arial", 11),
            text_color="gray"
        )
        self.label_pasta.pack(pady=10)
    
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
        
        if not url:
            messagebox.showwarning("Aviso", "Digite ou cole uma URL válida")
            return
        
        if self.downloading:
            messagebox.showinfo("Aviso", "Um download já está em andamento.")
            return
        
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
        history_window.geometry("700x500")
        
        text_box = ctk.CTkTextbox(history_window, font=("Consolas", 10))
        text_box.pack(fill="both", expand=True, padx=10, pady=10)
        
        for item in self.history.history[-20:]:
            status_icon = "✅" if item['status'] == "SUCCESS" else "❌"
            text_box.insert("end", f"{status_icon} [{item['platform']}] {item['title'][:60]}\n")
            text_box.insert("end", f"   📅 {item['timestamp'][:19]}\n")
            text_box.insert("end", f"   🔗 {item['url'][:80]}\n")
            text_box.insert("end", "-" * 60 + "\n")
        
        text_box.configure(state="disabled")

# ===================================================================
# PONTO DE ENTRADA
# ===================================================================
if __name__ == "__main__":
    app = BaixarYouApp()
    app.mainloop()