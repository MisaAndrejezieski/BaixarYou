# main.py - Versão Sênior
import asyncio
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from queue import Queue
from threading import Thread
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
SAVE_DIR.mkdir(exist_ok=True)  # Cria pasta Downloads se não existir

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Configuração de logging estruturado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "downloader.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")


@dataclass
class DownloadJob:
    """Representa um trabalho de download na fila"""
    url: str
    format_type: str = "mp4"  # mp4, webm, mp3
    quality: str = "best"     # best, 1080, 720, audio
    output_template: str = "%(title)s_%(id)s.%(ext)s"
    retries: int = 3
    priority: int = 5  # 1-10, menor = mais prioridade


class DownloadWorker:
    """Worker responsável por executar downloads (thread separada)"""
    
    def __init__(self, queue: Queue, status_callback, progress_callback):
        self.queue = queue
        self.status_callback = status_callback
        self.progress_callback = progress_callback
        self.running = True
        self.current_job: Optional[DownloadJob] = None
        
    def start(self):
        Thread(target=self._worker_loop, daemon=True).start()
        
    def _worker_loop(self):
        while self.running:
            try:
                job = self.queue.get(timeout=1)
                self.current_job = job
                self._download_with_retry(job)
                self.queue.task_done()
            except:
                pass
                
    def _download_with_retry(self, job: DownloadJob):
        """Baixa com retry e backoff exponencial"""
        for attempt in range(job.retries):
            try:
                self.status_callback(f"🔄 Tentativa {attempt + 1}/{job.retries}: {job.url}")
                self._download_video(job)
                self.status_callback(f"✅ Download concluído: {job.url}")
                return
            except Exception as e:
                wait_time = 2 ** attempt  # 1, 2, 4 segundos
                self.status_callback(f"❌ Erro: {str(e)[:100]}. Tentando novamente em {wait_time}s...")
                time.sleep(wait_time)
                
        self.status_callback(f"💀 Falha após {job.retries} tentativas: {job.url}")
        logger.error(f"Download failed after {job.retries} attempts: {job.url}")
                
    def _download_video(self, job: DownloadJob):
        """Executa o download com yt-dlp e progresso"""
        
        # Mapeia qualidade para formato yt-dlp
        format_map = {
            "best": "best[ext=mp4]",
            "1080": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
            "720": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
            "audio": "bestaudio/best",
        }
        
        ydl_opts = {
            'outtmpl': str(SAVE_DIR / job.output_template),
            'format': format_map.get(job.quality, format_map["best"]),
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self._progress_hook],
            'retries': 0,  # Nós mesmos gerenciamos o retry
            'ignoreerrors': False,
            'extract_flat': False,
        }
        
        # Se for áudio, converte pra MP3
        if job.quality == "audio" or job.format_type == "mp3":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': str(SAVE_DIR / '%(title)s_%(id)s.%(ext)s'),
            })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(job.url, download=True)
                logger.info(f"Baixado: {info.get('title', 'Unknown')} - {job.url}")
            except DownloadError as e:
                raise Exception(f"Falha no download: {str(e)}")
            except ExtractorError as e:
                raise Exception(f"Site não suportado ou URL inválida: {str(e)}")
                
    def _progress_hook(self, d):
        """Callback de progresso do yt-dlp"""
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').strip()
            speed = d.get('_speed_str', 'N/A')
            self.progress_callback(f"📥 {percent} @ {speed}")
        elif d['status'] == 'finished':
            self.progress_callback("📦 Processando...")


class VideoDownloaderApp(ctk.CTk):
    """Aplicação principal com fila de downloads"""
    
    def __init__(self):
        super().__init__()
        self.title("📥 BaixarYou Pro - Downloader Sênior")
        self.geometry("750x650")
        self.resizable(True, True)
        
        # Estado da aplicação
        self.download_queue: Queue = Queue()
        self.worker = DownloadWorker(
            queue=self.download_queue,
            status_callback=self._update_status,
            progress_callback=self._update_progress
        )
        self.worker.start()
        
        self.job_counter = 0
        self.active_jobs = {}
        
        self.create_widgets()
        self._check_queue_status()
        
    def create_widgets(self):
        """Cria todos os widgets da interface"""
        
        # Header
        ctk.CTkLabel(self, text="BaixarYou Pro", font=("Arial", 28, "bold")).pack(pady=15)
        
        # Frame de URL e opções
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Entrada URL
        ctk.CTkLabel(main_frame, text="URL do vídeo/playlist:", font=("Arial", 13)).pack(anchor="w", pady=(10,0))
        self.url_entry = ctk.CTkEntry(main_frame, width=600, height=40, placeholder_text="https://youtube.com/watch?v=...")
        self.url_entry.pack(pady=5, fill="x")
        
        # Opções de qualidade
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(options_frame, text="Qualidade:", font=("Arial", 12)).pack(side="left", padx=10)
        self.quality_var = ctk.StringVar(value="best")
        quality_menu = ctk.CTkOptionMenu(options_frame, values=["best (recomendado)", "1080p", "720p", "Apenas Áudio (MP3)"], 
                                        variable=self.quality_var, width=200)
        quality_menu.pack(side="left", padx=10)
        
        # Mapeamento para configuração
        self.quality_map = {
            "best (recomendado)": "best",
            "1080p": "1080", 
            "720p": "720",
            "Apenas Áudio (MP3)": "audio"
        }
        
        # Botão download
        self.download_btn = ctk.CTkButton(main_frame, text="➕ Adicionar à Fila", command=self.add_to_queue,
                                         width=200, height=40, font=("Arial", 14, "bold"))
        self.download_btn.pack(pady=10)
        
        # Playlist toggle
        self.playlist_var = ctk.BooleanVar(value=False)
        playlist_check = ctk.CTkCheckBox(main_frame, text="É uma playlist (baixar todos os vídeos)", 
                                        variable=self.playlist_var)
        playlist_check.pack(pady=5)
        
        # Status e progresso
        status_frame = ctk.CTkFrame(main_frame)
        status_frame.pack(fill="x", pady=10)
        
        self.status_label = ctk.CTkLabel(status_frame, text="✅ Pronto", font=("Arial", 11), text_color="green")
        self.status_label.pack(anchor="w", padx=10, pady=5)
        
        self.progress_label = ctk.CTkLabel(status_frame, text="", font=("Arial", 11))
        self.progress_label.pack(anchor="w", padx=10, pady=5)
        
        # Lista de downloads ativos
        ctk.CTkLabel(main_frame, text="Fila de Downloads:", font=("Arial", 13, "bold")).pack(anchor="w", pady=(10,0))
        
        self.queue_listbox = ctk.CTkTextbox(main_frame, height=150, font=("Consolas", 10))
        self.queue_listbox.pack(fill="x", pady=5)
        
        # Botões de pasta
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", pady=10)
        
        self.abrir_pasta_btn = ctk.CTkButton(buttons_frame, text="📂 Abrir Pasta", command=self.abrir_pasta,
                                            width=150, height=35)
        self.abrir_pasta_btn.pack(side="left", padx=5)
        
        self.mudar_pasta_btn = ctk.CTkButton(buttons_frame, text="🗂️ Mudar Pasta", command=self.mudar_pasta,
                                            width=150, height=35)
        self.mudar_pasta_btn.pack(side="left", padx=5)
        
        self.limpar_fila_btn = ctk.CTkButton(buttons_frame, text="🗑️ Limpar Fila", command=self.limpar_fila,
                                            width=150, height=35, fg_color="orange")
        self.limpar_fila_btn.pack(side="left", padx=5)
        
        # Label da pasta atual
        self.label_pasta = ctk.CTkLabel(main_frame, text=f"📁 Pasta atual: {SAVE_DIR}",
                                       font=("Arial", 11), text_color="gray")
        self.label_pasta.pack(pady=10)
        
    def add_to_queue(self):
        """Adiciona URL à fila de download"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Aviso", "Digite ou cole uma URL válida.")
            return
            
        quality_label = self.quality_var.get()
        quality = self.quality_map.get(quality_label, "best")
        
        if self.playlist_var.get():
            # Para playlists, usamos um job especial
            self._process_playlist(url, quality)
        else:
            # Job único
            job = DownloadJob(url=url, quality=quality)
            self.download_queue.put(job)
            self.job_counter += 1
            self._update_queue_display(f"▶️ Job #{self.job_counter}: {url[:60]}...\n")
            self.status_label.configure(text=f"✅ Adicionado à fila (total: {self.download_queue.qsize()})", text_color="blue")
            
        self.url_entry.delete(0, "end")
        
    def _process_playlist(self, playlist_url: str, quality: str):
        """Processa playlist e adiciona todos os vídeos individuais"""
        try:
            ydl_opts = {'quiet': True, 'extract_flat': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                
            if 'entries' in info:
                total = len(info['entries'])
                self.status_label.configure(text=f"📋 Processando playlist com {total} vídeos...", text_color="orange")
                
                for entry in info['entries']:
                    if entry:
                        job = DownloadJob(url=entry['url'], quality=quality)
                        self.download_queue.put(job)
                        self.job_counter += 1
                        self._update_queue_display(f"📼 {entry.get('title', 'Unknown')[:50]}...\n")
                        
                self.status_label.configure(text=f"✅ Playlist processada! {total} vídeos na fila", text_color="green")
            else:
                messagebox.showerror("Erro", "URL não parece ser uma playlist válida")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao processar playlist:\n{str(e)[:200]}")
            logger.error(f"Playlist error: {e}")
            
    def _update_queue_display(self, text: str):
        """Atualiza o display da fila"""
        current = self.queue_listbox.get("0.0", "end").strip()
        self.queue_listbox.delete("0.0", "end")
        self.queue_listbox.insert("0.0", text + current)
        if self.queue_listbox.index('end-1c') > 1000:  # Limita tamanho
            self.queue_listbox.delete("end-2 lines", "end-1c")
            
    def _update_status(self, message: str):
        """Callback de status do worker"""
        self.status_label.configure(text=message, text_color="orange" if "🔄" in message else "green")
        logger.info(message)
        
    def _update_progress(self, message: str):
        """Callback de progresso"""
        self.progress_label.configure(text=message)
        
    def _check_queue_status(self):
        """Verifica periodicamente o status da fila"""
        if hasattr(self, 'download_queue') and self.download_queue:
            qsize = self.download_queue.qsize()
            if qsize > 0:
                self.status_label.configure(text=f"📥 Em andamento... {qsize} na fila", text_color="blue")
        self.after(1000, self._check_queue_status)  # Check a cada 1s
        
    def mudar_pasta(self):
        """Muda a pasta de download"""
        global SAVE_DIR
        pasta = filedialog.askdirectory(title="Escolha a pasta para salvar os vídeos", initialdir=SAVE_DIR)
        if pasta:
            SAVE_DIR = Path(pasta)
            self.label_pasta.configure(text=f"📁 Pasta atual: {SAVE_DIR}")
            messagebox.showinfo("Pasta Alterada", f"Downloads agora serão salvos em:\n{SAVE_DIR}")
            
    def limpar_fila(self):
        """Limpa a fila de downloads"""
        if messagebox.askyesno("Confirmar", "Tem certeza que deseja limpar TODOS os downloads pendentes?"):
            while not self.download_queue.empty():
                try:
                    self.download_queue.get_nowait()
                except:
                    pass
            self.queue_listbox.delete("0.0", "end")
            self.status_label.configure(text="🗑️ Fila limpa", text_color="red")
            
    def abrir_pasta(self):
        """Abre a pasta de downloads no explorer"""
        try:
            if os.name == "nt":
                os.startfile(str(SAVE_DIR))
            else:
                subprocess.run(["xdg-open", str(SAVE_DIR)])
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")
            
    def on_closing(self):
        """Limpeza ao fechar"""
        if messagebox.askokcancel("Sair", "Downloads em andamento serão perdidos. Deseja sair?"):
            self.worker.running = False
            self.destroy()


if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()