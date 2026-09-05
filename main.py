# ===================================================================
# BaixarYou - Downloader de Vídeos do YouTube
# ===================================================================
# Versão Definitiva - Baixa vídeos completos (com áudio)
# ===================================================================

import os
import re
import subprocess
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
import yt_dlp

# ===================================================================
# CONFIGURAÇÕES
# ===================================================================

BASE_DIR = Path(__file__).parent
SAVE_DIR = BASE_DIR / "Downloads"
SAVE_DIR.mkdir(exist_ok=True)

COOKIE_FILE = BASE_DIR / "cookies.txt"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# ===================================================================
# FUNÇÃO PARA CORRIGIR URL
# ===================================================================

def fix_youtube_url(url: str) -> str:
    """Converte qualquer URL do YouTube para o formato padrão"""
    url = url.strip()
    
    patterns = [
        r'youtube\.com/watch\?v=([\w-]+)',
        r'youtu\.be/([\w-]+)',
        r'youtube\.com/embed/([\w-]+)',
        r'youtube\.com/v/([\w-]+)',
        r'youtube\.com/shorts/([\w-]+)',
        r'youtube\.com/([a-zA-Z0-9_-]{11})(?:[?/]|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"
    
    return url

# ===================================================================
# FUNÇÃO PARA VERIFICAR FFMPEG
# ===================================================================

def check_ffmpeg() -> bool:
    """Verifica se o ffmpeg está instalado"""
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        return True
    except:
        return False

# ===================================================================
# FUNÇÃO PARA OBTER INFORMAÇÕES DO VÍDEO
# ===================================================================

def get_video_info(url):
    """Obtém informações do vídeo sem baixar"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
        }
        if COOKIE_FILE.exists():
            ydl_opts['cookiefile'] = str(COOKIE_FILE)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception:
        return None

# ===================================================================
# CLASSE PRINCIPAL
# ===================================================================

class BaixarYouApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("📥 BaixarYou")
        self.geometry("650x520")
        self.resizable(False, False)
        
        self.downloading = False
        self.has_ffmpeg = check_ffmpeg()
        
        self.create_widgets()
        self.check_cookies()
        self.check_ffmpeg_status()
    
    def create_widgets(self):
        # TÍTULO
        title = ctk.CTkLabel(
            self, 
            text="📥 BaixarYou",
            font=("Arial", 32, "bold")
        )
        title.pack(pady=15)
        
        subtitle = ctk.CTkLabel(
            self,
            text="Baixe vídeos do YouTube",
            font=("Arial", 12),
            text_color="gray"
        )
        subtitle.pack(pady=(0, 15))
        
        # FRAME PRINCIPAL
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        # URL
        ctk.CTkLabel(
            main_frame,
            text="🔗 URL do vídeo:",
            font=("Arial", 13, "bold")
        ).pack(anchor="w", pady=(10, 5))
        
        self.url_entry = ctk.CTkEntry(
            main_frame,
            height=45,
            placeholder_text="Cole a URL do YouTube aqui..."
        )
        self.url_entry.pack(fill="x", pady=(0, 10))
        self.url_entry.bind('<Return>', lambda e: self.start_download())
        
        # QUALIDADE
        quality_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        quality_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            quality_frame,
            text="Qualidade:",
            font=("Arial", 12)
        ).pack(side="left", padx=(0, 10))
        
        qualities = ["Melhor (MP4)", "Apenás Áudio (MP3)"]
        self.quality_var = ctk.StringVar(value=qualities[0])
        quality_menu = ctk.CTkOptionMenu(
            quality_frame,
            values=qualities,
            variable=self.quality_var,
            width=180
        )
        quality_menu.pack(side="left")
        
        # PASTA
        pasta_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        pasta_frame.pack(fill="x", pady=10)
        
        self.pasta_label = ctk.CTkLabel(
            pasta_frame,
            text=f"📁 {SAVE_DIR}",
            font=("Arial", 11),
            text_color="gray"
        )
        self.pasta_label.pack(side="left")
        
        ctk.CTkButton(
            pasta_frame,
            text="Alterar",
            width=80,
            height=30,
            command=self.mudar_pasta
        ).pack(side="right")
        
        # STATUS FFMPEG
        self.ffmpeg_label = ctk.CTkLabel(
            main_frame,
            text="",
            font=("Arial", 10)
        )
        self.ffmpeg_label.pack(pady=(5, 0))
        
        # BOTÃO DOWNLOAD
        self.download_btn = ctk.CTkButton(
            main_frame,
            text="⬇️ BAIXAR",
            command=self.start_download,
            height=50,
            font=("Arial", 16, "bold"),
            fg_color="#2e7d32",
            hover_color="#1b5e20"
        )
        self.download_btn.pack(fill="x", pady=15)
        
        # PROGRESSO
        self.progress_bar = ctk.CTkProgressBar(main_frame, height=15)
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            main_frame,
            text="Aguardando...",
            font=("Arial", 11)
        )
        self.progress_label.pack(pady=5)
        
        # STATUS
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="✅ Pronto",
            font=("Arial", 12),
            text_color="green"
        )
        self.status_label.pack(pady=5)
    
    def check_ffmpeg_status(self):
        """Mostra status do ffmpeg"""
        if self.has_ffmpeg:
            self.ffmpeg_label.configure(
                text="✅ FFmpeg instalado",
                text_color="green"
            )
        else:
            self.ffmpeg_label.configure(
                text="⚠️ FFmpeg não instalado - Baixando em qualidade padrão",
                text_color="orange"
            )
    
    def check_cookies(self):
        """Verifica se o arquivo de cookies existe"""
        if COOKIE_FILE.exists():
            self.status_label.configure(
                text="✅ Cookies carregados",
                text_color="green"
            )
        else:
            self.status_label.configure(
                text="ℹ️ Sem cookies",
                text_color="orange"
            )
    
    def mudar_pasta(self):
        """Altera a pasta de download"""
        global SAVE_DIR
        pasta = filedialog.askdirectory(title="Escolha a pasta", initialdir=str(SAVE_DIR))
        if pasta:
            SAVE_DIR = Path(pasta)
            self.pasta_label.configure(text=f"📁 {SAVE_DIR}")
            self.status_label.configure(text=f"📁 Pasta alterada", text_color="green")
    
    def update_progress(self, d):
        """Atualiza a barra de progresso"""
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
            
            self.progress_bar.set(percent / 100)
            self.progress_label.configure(text=f"{int(percent)}% - {speed_str}")
            
        elif d['status'] == 'finished':
            self.progress_bar.set(1)
            self.progress_label.configure(text="100% - Finalizando...")
    
    def start_download(self):
        """Inicia o download"""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showwarning("Aviso", "Digite uma URL!")
            return
        
        if self.downloading:
            messagebox.showinfo("Aviso", "Download em andamento...")
            return
        
        # Corrige a URL
        if 'youtube.com' in url or 'youtu.be' in url:
            url = fix_youtube_url(url)
            self.url_entry.delete(0, 'end')
            self.url_entry.insert(0, url)
        
        self.downloading = True
        self.download_btn.configure(state="disabled", text="⏳ BAIXANDO...")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Iniciando...")
        self.status_label.configure(text="🔄 Baixando...", text_color="blue")
        
        # Inicia o download em uma thread
        thread = threading.Thread(
            target=self.download_video,
            args=(url,),
            daemon=True
        )
        thread.start()
        
        # Monitora a thread
        self.monitor_download(thread)
    
    def monitor_download(self, thread):
        """Monitora o download em andamento"""
        if thread.is_alive():
            self.after(500, lambda: self.monitor_download(thread))
        else:
            self.downloading = False
            self.download_btn.configure(state="normal", text="⬇️ BAIXAR")
    
    def download_video(self, url):
        """Função que executa o download"""
        try:
            quality = self.quality_var.get()
            
            # ============================================================
            # CONFIGURAÇÃO DE FORMATO - SIMPLES E ROBUSTA
            # ============================================================
            
            if quality == "Apenás Áudio (MP3)":
                # Áudio MP3
                format_spec = "bestaudio/best"
                postprocessors = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                # Vídeo MP4 com áudio incluso
                # Usa "best" que sempre funciona
                format_spec = "best"
                postprocessors = []
            
            # ============================================================
            # CONFIGURAÇÕES DO YT-DLP
            # ============================================================
            
            ydl_opts = {
                'outtmpl': str(SAVE_DIR / '%(title)s.%(ext)s'),
                'format': format_spec,
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [self.update_progress],
                'retries': 10,
                'fragment_retries': 10,
                'ignoreerrors': True,
                'postprocessors': postprocessors,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                }
            }
            
            # Adiciona cookies se existir
            if COOKIE_FILE.exists():
                ydl_opts['cookiefile'] = str(COOKIE_FILE)
            
            # ============================================================
            # EXECUTA O DOWNLOAD
            # ============================================================
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Verifica se info não é None
                if info is None:
                    raise Exception("Não foi possível obter informações do vídeo.")
                
                titulo = info.get('title', 'Vídeo')
                
                self.status_label.configure(
                    text=f"✅ Download concluído: {titulo[:50]}",
                    text_color="green"
                )
                
                # Mensagem de sucesso
                msg = f"✅ Vídeo baixado com sucesso!\n\n📹 {titulo}\n📁 {SAVE_DIR}"
                messagebox.showinfo("Sucesso", msg)
                
        except Exception as e:
            error_msg = str(e)
            
            # Mensagens de erro amigáveis
            if "Video unavailable" in error_msg:
                mensagem = "❌ Vídeo indisponível ou removido."
            elif "Private video" in error_msg:
                mensagem = "❌ Este vídeo é privado."
            elif "Sign in to confirm" in error_msg or "verify" in error_msg.lower():
                mensagem = (
                    "❌ YouTube pede verificação.\n\n"
                    "💡 Soluções:\n"
                    "1. Use cookies.txt (faça login e exporte)\n"
                    "2. Tente outro vídeo\n"
                    "3. Aguarde alguns minutos e tente novamente"
                )
            elif "HTTP Error 403" in error_msg or "Forbidden" in error_msg:
                mensagem = (
                    "❌ Acesso bloqueado pelo YouTube.\n\n"
                    "💡 Soluções:\n"
                    "1. Use cookies.txt\n"
                    "2. Atualize o yt-dlp: pip install --upgrade yt-dlp\n"
                    "3. Aguarde alguns minutos"
                )
            elif "ffmpeg" in error_msg.lower():
                mensagem = "❌ FFmpeg necessário.\n\nBaixe e instale: https://ffmpeg.org/download.html"
            else:
                mensagem = f"❌ Erro ao baixar:\n\n{error_msg[:300]}"
            
            self.status_label.configure(text="❌ Falha no download", text_color="red")
            messagebox.showerror("Erro", mensagem)
        
        finally:
            self.downloading = False
            self.download_btn.configure(state="normal", text="⬇️ BAIXAR")

# ===================================================================
# EXECUTA O PROGRAMA
# ===================================================================

if __name__ == "__main__":
    app = BaixarYouApp()
    app.mainloop()