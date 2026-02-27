import os
import re
import logging
import threading
import customtkinter as ctk
from tkinter import messagebox
import yt_dlp

# Configuração de diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "Salvar")
FFMPEG_DIR = os.path.join(BASE_DIR, "ffmpeg-master-latest-win64-gpl-shared/bin")

# Configurar aparência misa
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuração de logging
        logging.basicConfig(
            filename=os.path.join(BASE_DIR, 'download_errors.log'),
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        self.title("Instagram Downloader by Misa Andrejezieski")
        self.geometry("800x600")
        self.minsize(800, 600)
        self.downloading = False
        
        # Configurar layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.create_widgets()
        self.check_environment()

    def create_widgets(self):
        # Container principal
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Cabeçalho
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        ctk.CTkLabel(
            self.header_frame,
            text="Instagram Downloader",
            font=("Arial", 28, "bold")
        ).grid(row=0, column=0, pady=5)
        
        ctk.CTkLabel(
            self.header_frame,
            text="Cole a URL do post, reel ou story do Instagram",
            font=("Arial", 12),
            text_color=("gray50")
        ).grid(row=1, column=0)
        
        # Entrada de URL
        self.url_entry = ctk.CTkEntry(
            self.main_frame,
            placeholder_text="Ex: https://www.instagram.com/p/CxY7JqGRkHZ/",
            width=500,
            height=40,
            font=("Arial", 12)
        )
        self.url_entry.grid(row=1, column=0, pady=20)
        
        # Botão de download
        self.download_btn = ctk.CTkButton(
            self.main_frame,
            text="Baixar Agora",
            command=self.start_download,
            width=200,
            height=45,
            font=("Arial", 14, "bold"),
            fg_color="#E1306C",
            hover_color="#C71F5E"
        )
        self.download_btn.grid(row=2, column=0, pady=10)
        
        # Progresso
        self.progress_bar = ctk.CTkProgressBar(
            self.main_frame,
            mode="determinate",
            height=15,
            width=400,
            fg_color="#2B2B2B",
            progress_color="#E1306C"
        )
        
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=("Arial", 12),
            text_color=("gray60")
        )
        
        # Animação de loading
        self.loading_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=("Arial", 24)
        )

    def check_environment(self):
        """Verifica diretórios e dependências"""
        try:
            # Criar diretório de downloads
            os.makedirs(SAVE_DIR, exist_ok=True)
            
            # Verificar FFmpeg
            ffmpeg_path = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
            ffprobe_path = os.path.join(FFMPEG_DIR, "ffprobe.exe")
            
            if not all([os.path.exists(p) for p in [ffmpeg_path, ffprobe_path]]):
                messagebox.showerror(
                    "Erro de Configuração",
                    f"FFmpeg não encontrado em:\n{FFMPEG_DIR}\n"
                    "Verifique se:\n"
                    "1. A pasta ffmpeg-master-latest-win64-gpl-shared está extraída\n"
                    "2. Os arquivos estão na subpasta bin\n"
                    "3. Não renomeou nenhuma pasta ou arquivo"
                )
                self.destroy()
                
        except Exception as e:
            logging.error(f"Erro na configuração inicial: {str(e)}")
            messagebox.showerror("Erro Fatal", f"Falha na configuração: {str(e)}")
            self.destroy()

    def validate_url(self, url):
        """Valida formato da URL do Instagram"""
        pattern = r'^https?://(www\.)?instagram\.com/(p|reel|stories)/[a-zA-Z0-9_-]+/?'
        return re.match(pattern, url) is not None

    def start_download(self):
        """Inicia o processo de download em thread separada"""
        url = self.url_entry.get().strip()
        
        if not self.validate_url(url):
            messagebox.showwarning(
                "URL Inválida",
                "Formato de URL incorreto!\n"
                "Exemplos válidos:\n"
                "- Posts: https://www.instagram.com/p/...\n"
                "- Reels: https://www.instagram.com/reel/...\n"
                "- Stories: https://www.instagram.com/stories/..."
            )
            return
            
        if self.downloading:
            messagebox.showwarning("Atenção", "Já existe um download em andamento!")
            return
            
        self.downloading = True
        self.show_progress(True)
        
        threading.Thread(
            target=self.download_video,
            args=(url,),
            daemon=True
        ).start()

    def download_video(self, url):
        """Executa o download usando yt-dlp"""
        try:
            ydl_opts = {
                'outtmpl': os.path.join(SAVE_DIR, '%(title)s.%(ext)s'),
                'ffmpeg_location': FFMPEG_DIR,
                'progress_hooks': [self.update_progress],
                'noplaylist': True,
                'quiet': True,
                'format': 'best',
                'concurrent_fragment_downloads': 5,
                'retries': 10,
                'fragment_retries': 10,
                'http_chunk_size': 1048576,
                'extractor_args': {'instagram': {'skip_auth': True}},
                'logger': logging.getLogger(),
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
            self.show_success(info)
            
        except Exception as e:
            logging.error(f"Erro no download: {str(e)}")
            self.show_error(str(e))
        finally:
            self.downloading = False
            self.show_progress(False)

    def update_progress(self, d):
        """Atualiza a interface com o progresso do download"""
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').strip()
            speed = d.get('_speed_str', 'N/A').strip()
            eta = d.get('_eta_str', 'N/A').strip()
            
            try:
                progress = float(percent.replace('%','')) / 100
                self.progress_bar.set(progress)
            except:
                pass
            
            self.status_label.configure(
                text=f"Progresso: {percent} | Velocidade: {speed} | Tempo restante: {eta}"
            )
            self.animate_loading()

    def show_progress(self, show=True):
        """Mostra/oculta elementos de progresso"""
        if show:
            self.progress_bar.grid(row=3, column=0, pady=15)
            self.status_label.grid(row=4, column=0)
            self.loading_label.grid(row=5, column=0, pady=10)
            self.download_btn.configure(state="disabled")
            self.animate_loading()
        else:
            self.progress_bar.grid_forget()
            self.status_label.grid_forget()
            self.loading_label.grid_forget()
            self.download_btn.configure(state="normal")

    def animate_loading(self, frame=0):
        """Animação de loading personalizada"""
        if self.downloading:
            symbols = ['⣾','⣽','⣻','⢿','⡿','⣟','⣯','⣷']
            self.loading_label.configure(text=symbols[frame % 8])
            self.after(100, lambda: self.animate_loading(frame + 1))

    def show_success(self, info):
        """Exibe mensagem de sucesso"""
        filename = os.path.basename(info['requested_downloads'][0]['filepath'])
        messagebox.showinfo(
            "Download Concluído!",
            f"Arquivo salvo em:\n{os.path.join(SAVE_DIR, filename)}"
        )
        self.url_entry.delete(0, 'end')

    def show_error(self, error_msg):
        """Exibe mensagens de erro amigáveis"""
        error_mapping = {
            'Private content': 'Conteúdo privado - Não é possível baixar',
            'Login Required': 'Necessário login - Conteúdo restrito',
            'Unsupported URL': 'URL não suportada ou inválida',
            'HTTP Error 403': 'Acesso bloqueado pelo Instagram',
            'FFmpeg': 'Erro na conversão do arquivo',
            'File already exists': 'Arquivo já existe na pasta de destino'
        }
        
        for key, msg in error_mapping.items():
            if key in error_msg:
                final_msg = msg
                break
        else:
            final_msg = f"Erro desconhecido: {error_msg[:150]}..."
        
        messagebox.showerror("Erro no Download", final_msg)

if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.mainloop()
    