# ===================================================================
# main.py - BaixarYou com Barra de Progresso Funcional
# ===================================================================
# DESCRIÇÃO: Baixador universal de vídeos/áudio com interface gráfica
# PLATAFORMAS SUPORTADAS: YouTube, TikTok, Instagram, Twitter/X, 
#                         Facebook, Vimeo, SoundCloud, Twitch, Reddit
# REQUISITOS: Python 3.7+, yt-dlp, customtkinter, ffmpeg (opcional)
# ===================================================================

import json  # Salvar histórico em formato JSON
import logging  # Registrar logs para debug
# ===================================================================
# 1. IMPORTAÇÕES
# ===================================================================
import os  # Operações com sistema de arquivos
import subprocess  # Executar comandos no sistema (abrir pasta)
import sys  # Acessar argumentos e informações do sistema
import threading  # Executar downloads em paralelo (não travar a UI)
from datetime import datetime  # Timestamps no histórico
from pathlib import Path  # Manipulação moderna de caminhos de arquivos
from tkinter import (filedialog,  # Diálogos do sistema (pastas, alerts)
                     messagebox)
from typing import Dict  # Type hints para dicionários

import customtkinter as ctk  # Interface gráfica moderna e escura
import yt_dlp  # Motor principal de download (suporta várias plataformas)
from yt_dlp.utils import (DownloadError,  # Tipos de erro específicos
                          ExtractorError)

# ===================================================================
# 2. CONFIGURAÇÕES GLOBAIS
# ===================================================================

def get_base_dir() -> Path:
    """
    Retorna o diretório base onde o programa está rodando.
    
    IMPORTANTE: Detecta se está rodando como executável .exe (pyinstaller)
    ou como script .py. Isso garante que os arquivos sejam salvos no
    lugar certo em ambos os casos.
    
    Retorna:
        Path: Caminho absoluto do diretório do programa
    """
    if getattr(sys, 'frozen', False):
        # Está rodando como .exe (pyinstaller)
        return Path(sys.executable).parent
    # Está rodando como script .py
    return Path(__file__).parent

# Diretório base do programa
BASE_DIR = get_base_dir()

# ===================================================================
# 2.1 PASTA DE DOWNLOADS
# ===================================================================
# Pasta onde os vídeos serão salvos (cria se não existir)
SAVE_DIR = BASE_DIR / "Downloads"
SAVE_DIR.mkdir(exist_ok=True)

# ===================================================================
# 2.2 PASTA DE LOGS
# ===================================================================
# Pasta onde os arquivos de log serão salvos (para debug)
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ===================================================================
# 2.3 ARQUIVO DE HISTÓRICO
# ===================================================================
# Arquivo JSON que guarda o histórico de todos os downloads
HISTORY_FILE = BASE_DIR / "download_history.json"

# ===================================================================
# 2.4 ARQUIVO DE COOKIES (PARA INSTAGRAM E OUTROS SITES RESTRITIVOS)
# ===================================================================
# Arquivo de cookies exportado do navegador (formato Netscape)
COOKIE_FILE = BASE_DIR / "cookies.txt"

# ===================================================================
# 2.5 CONFIGURAÇÃO DE LOGGING
# ===================================================================
# Configura o sistema de logs: salva em arquivo e mostra no console
logging.basicConfig(
    level=logging.INFO,                                    # Nível de detalhamento
    format='%(asctime)s - %(levelname)s - %(message)s',    # Formato da mensagem
    handlers=[
        logging.FileHandler(LOG_DIR / "downloader.log", encoding='utf-8'),  # Salva em arquivo
    ]
)
logger = logging.getLogger(__name__)  # Cria um logger para este módulo

# ===================================================================
# 2.6 CONFIGURAÇÃO DA INTERFACE (customtkinter)
# ===================================================================
ctk.set_appearance_mode("dark")        # Tema escuro (mais bonito)
ctk.set_default_color_theme("green")   # Cor principal (verde)

# ===================================================================
# 3. CLASSE: DownloadHistory
# ===================================================================
# GERENCIAMENTO DO HISTÓRICO DE DOWNLOADS
# ===================================================================
class DownloadHistory:
    """
    Gerencia o histórico de downloads em um arquivo JSON.
    
    Funcionalidades:
        - Carregar histórico do arquivo
        - Adicionar nova entrada ao histórico
        - Salvar histórico no arquivo
    """
    
    def __init__(self):
        """Inicializa o histórico carregando do arquivo"""
        self.history_file = HISTORY_FILE
        self.history = self.load_history()  # Carrega histórico existente
    
    def load_history(self):
        """
        Carrega o histórico do arquivo JSON.
        
        Se o arquivo não existir ou estiver corrompido, retorna uma lista vazia.
        """
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                # Se der erro (arquivo corrompido), retorna lista vazia
                return []
        return []  # Arquivo não existe
    
    def add_download(self, url: str, title: str, platform: str, status: str, error: str = ""):
        """
        Adiciona uma nova entrada ao histórico.
        
        Parâmetros:
            url (str): URL do vídeo baixado
            title (str): Título do vídeo
            platform (str): Plataforma de origem (YouTube, Instagram, etc)
            status (str): "SUCCESS" ou "FAILED"
            error (str): Mensagem de erro (se houver)
        """
        self.history.append({
            'url': url,
            'title': title,
            'platform': platform,
            'status': status,
            'error': error,
            'save_dir': str(SAVE_DIR),
            'timestamp': datetime.now().isoformat()  # Data e hora em formato ISO
        })
        self.save_history()  # Salva imediatamente
    
    def save_history(self):
        """
        Salva o histórico atual no arquivo JSON.
        """
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except:
            pass  # Se falhar, apenas ignora (não crítico)

# ===================================================================
# 4. CLASSE: DownloadWorker
# ===================================================================
# EXECUÇÃO DE DOWNLOADS EM THREAD SEPARADA
# ===================================================================
class DownloadWorker:
    """
    Worker responsável por executar downloads em uma thread separada.
    
    Isso evita que a interface gráfica congele durante o download.
    
    Funcionalidades:
        - Iniciar download em thread separada
        - Atualizar barra de progresso via callbacks
        - Detectar plataforma automaticamente
        - Tratar erros específicos do yt-dlp
    """
    
    def __init__(self, status_callback, progress_callback, history: DownloadHistory):
        """
        Inicializa o worker com callbacks para atualizar a UI.
        
        Parâmetros:
            status_callback: Função para atualizar a label de status
            progress_callback: Função para atualizar a label de progresso
            history: Objeto DownloadHistory para registrar downloads
        """
        self.status_callback = status_callback   # Callback para status
        self.progress_callback = progress_callback  # Callback para progresso
        self.history = history                   # Histórico de downloads
        self.running = True                      # Flag de controle
        self._app = None                         # Referência à aplicação (para UI)
        
    def start_download(self, url: str, quality: str = "best", is_playlist: bool = False):
        """
        Inicia o download em uma thread separada.
        
        Parâmetros:
            url (str): URL do vídeo/playlist
            quality (str): Qualidade desejada (best, 1080p, 720p, 480p, audio)
            is_playlist (bool): True se for uma playlist
            
        Retorna:
            threading.Thread: A thread do download
        """
        # Cria e inicia a thread
        thread = threading.Thread(
            target=self._download_video,        # Função a ser executada
            args=(url, quality, is_playlist),   # Argumentos da função
            daemon=True                         # Fecha automaticamente ao sair
        )
        thread.start()
        return thread
    
    def _progress_hook(self, d):
        """
        Callback de progresso do yt-dlp.
        
        Este método é chamado automaticamente pelo yt-dlp durante o download.
        Calcula o percentual e a velocidade, e atualiza a UI via callbacks.
        
        Parâmetros:
            d (dict): Dicionário com informações do progresso
        """
        try:
            if d['status'] == 'downloading':
                # ============ CALCULA PERCENTUAL ============
                percent = 0
                if 'total_bytes' in d and d['total_bytes'] > 0:
                    # Temos o tamanho total exato
                    percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                elif 'total_bytes_estimate' in d:
                    # Temos uma estimativa do tamanho total
                    percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                
                # ============ CALCULA VELOCIDADE ============
                speed = d.get('speed', 0)
                if speed and speed > 0:
                    if speed > 1024 * 1024:
                        speed_str = f"{speed / 1024 / 1024:.1f} MB/s"  # Megabytes por segundo
                    elif speed > 1024:
                        speed_str = f"{speed / 1024:.1f} KB/s"         # Kilobytes por segundo
                    else:
                        speed_str = f"{speed:.0f} B/s"                 # Bytes por segundo
                else:
                    speed_str = "calculando..."
                
                # ============ ATUALIZA UI ============
                # Usa after(0) para atualizar a UI de forma segura (thread-safe)
                if self._app:
                    self._app.after(0, lambda p=percent, s=speed_str: self._app.update_progress_bar(p, s))
                    
            elif d['status'] == 'finished':
                # Download concluído
                if self._app:
                    self._app.after(0, lambda: self._app.update_progress_bar(100, "Finalizando..."))
                    
        except Exception as e:
            # Não deixa erro no progress hook quebrar o download
            pass
    
    def _get_ydl_options(self, quality: str, is_playlist: bool) -> Dict:
        """
        Retorna as opções de configuração para o yt-dlp.
        
        ==============================================================
        🍪 COOKIES - USO EXCLUSIVO DO ARQUIVO cookies.txt
        ==============================================================
        O programa USA APENAS o arquivo cookies.txt manual.
        NÃO tenta extrair do Edge/Chrome/Firefox para evitar erros.
        
        O arquivo cookies.txt deve estar na pasta do programa e ter
        o formato Netscape (exportado por extensões de navegador).
        ==============================================================
        
        Parâmetros:
            quality (str): Qualidade desejada
            is_playlist (bool): True se for playlist
            
        Retorna:
            Dict: Opções para o yt-dlp
        """
        
        # ============ MAPEAMENTO DE QUALIDADE ============
        format_map = {
            "best": "bestvideo+bestaudio/best",                         # Melhor qualidade disponível
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",  # Máx 1080p
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",     # Máx 720p
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",     # Máx 480p
            "audio": "bestaudio/best",                                   # Apenas áudio
        }
        
        format_spec = format_map.get(quality, "bestvideo+bestaudio/best")
        
        # ============ VERIFICA SE O ARQUIVO COOKIES EXISTE ============
        cookie_file_exists = COOKIE_FILE.exists()
        if cookie_file_exists:
            logger.info(f"✅ Arquivo de cookies encontrado: {COOKIE_FILE}")
        else:
            logger.warning(f"⚠️ Arquivo de cookies NÃO encontrado: {COOKIE_FILE}")
        
        # ============ CONFIGURAÇÕES PRINCIPAIS ============
        ydl_opts = {
            # ----- Onde salvar -----
            'outtmpl': str(SAVE_DIR / '%(title)s_%(id)s.%(ext)s'),  # Padrão: título_id.extensão
            
            # ----- Qualidade -----
            'format': format_spec,
            
            # ----- Comportamento -----
            'quiet': False,              # Exibe informações no console
            'no_warnings': True,         # Oculta avisos
            'ignoreerrors': True,        # Continua mesmo com erros em playlists
            'extract_flat': is_playlist, # Para playlists, extrai informações sem baixar
            
            # ----- Tentativas de retry -----
            'retries': 10,               # Número de tentativas em caso de falha
            'fragment_retries': 10,      # Tentativas para fragmentos (vídeos longos)
            'skip_unavailable_fragments': True,  # Pula fragmentos indisponíveis
            
            # ----- Progresso -----
            'progress_hooks': [self._progress_hook],  # Callback de progresso
            'verbose': False,            # Não exibe logs detalhados
            
            # ==============================================================
            # 🍪 COOKIES - APENAS ARQUIVO (SEM EDGE/CHROME/FIREFOX)
            # ==============================================================
            # FORÇA o uso do arquivo cookies.txt
            # NÃO tenta extrair do navegador (evita os erros)
            'cookiefile': str(COOKIE_FILE) if cookie_file_exists else None,
            # ==============================================================
        }
        
        # Remove opções None (cookiefile se não existir)
        if ydl_opts['cookiefile'] is None:
            del ydl_opts['cookiefile']
        
        # ============ HEADERS HTTP MELHORADOS ============
        # Esses headers fazem o Instagram pensar que é um navegador real
        ydl_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://www.instagram.com/',
            'Origin': 'https://www.instagram.com',
        }
        
        # ============ CONFIGURAÇÕES ESPECÍFICAS PARA ÁUDIO ============
        if quality == "audio":
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',   # Usa ffmpeg para extrair áudio
                'preferredcodec': 'mp3',        # Converte para MP3
                'preferredquality': '192',      # Bitrate de 192 kbps
            }]
        
        return ydl_opts
    
    def _download_video(self, url: str, quality: str, is_playlist: bool):
        """
        Executa o download usando yt-dlp.
        
        Esta é a função principal que faz o download. É executada em uma thread
        separada para não travar a interface.
        
        Parâmetros:
            url (str): URL do vídeo
            quality (str): Qualidade desejada
            is_playlist (bool): True se for playlist
        """
        title = "Unknown"
        platform = self._detect_platform(url)  # Detecta a plataforma pela URL
        
        try:
            # ============ PREPARA OPÇÕES ============
            ydl_opts = self._get_ydl_options(quality, is_playlist)
            
            self.status_callback(f"🌐 Conectando a {platform}...")
            
            # ============ CRIA O OBJETO YT-DLP ============
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                
                # Extrai informações sem baixar (para mostrar título)
                info = ydl.extract_info(url, download=False)
                
                # ============ VERIFICA SE É PLAYLIST ============
                if 'entries' in info:
                    # É uma playlist
                    entries = info.get('entries', [])
                    total = len(entries)
                    title = info.get('title', 'Playlist')
                    self.status_callback(f"📋 Playlist: {title} ({total} vídeos)")
                    
                    # Baixa a playlist completa
                    ydl.download([url])
                    
                    # ============ SUCESSO (PLAYLIST) ============
                    self.status_callback(f"✅ Playlist baixada: {title}")
                    self.history.add_download(url, title, platform, "SUCCESS")
                    self._show_success(f"Playlist baixada!\n{total} vídeos salvos em:\n{SAVE_DIR}")
                    
                else:
                    # ============ É UM VÍDEO ÚNICO ============
                    title = info.get('title', 'Unknown')
                    self.status_callback(f"🎬 Baixando: {title[:50]}...")
                    
                    # Baixa o vídeo
                    ydl.download([url])
                    
                    # ============ SUCESSO (VÍDEO) ============
                    self.status_callback(f"✅ Download concluído: {title[:50]}")
                    self.history.add_download(url, title, platform, "SUCCESS")
                    self._show_success(f"Vídeo baixado com sucesso!\n\n📹 {title}\n📁 {SAVE_DIR}")
                    
        # ============ TRATAMENTO DE ERROS ============
        except DownloadError as e:
            # Erro específico do yt-dlp (falha no download)
            error_msg = f"Erro de download: {str(e)[:150]}"
            self.status_callback(f"❌ {error_msg}")
            logger.error(f"DownloadError: {url} - {e}")
            self.history.add_download(url, title, platform, "FAILED", str(e))
            self._show_error(error_msg)
            
        except ExtractorError as e:
            # Erro de extração (URL não suportada ou inválida)
            error_msg = f"URL não suportada: {str(e)[:150]}"
            self.status_callback(f"❌ {error_msg}")
            logger.error(f"ExtractorError: {url} - {e}")
            self.history.add_download(url, title, platform, "FAILED", str(e))
            self._show_error(error_msg)
            
        except Exception as e:
            # Qualquer outro erro inesperado
            error_msg = f"Erro: {str(e)[:150]}"
            self.status_callback(f"❌ {error_msg}")
            logger.error(f"Unexpected error: {url} - {e}")
            self.history.add_download(url, title, platform, "FAILED", str(e))
            self._show_error(error_msg)
            
        finally:
            # ============ RESETA A BARRA DE PROGRESSO ============
            if self._app:
                self._app.after(0, self._app.reset_progress_bar)
    
    def _detect_platform(self, url: str) -> str:
        """
        Detecta a plataforma de origem pela URL.
        
        Parâmetros:
            url (str): URL do vídeo
            
        Retorna:
            str: Nome da plataforma detectada
        """
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
        """
        Exibe uma mensagem de sucesso em uma caixa de diálogo.
        
        Usa after(0) para garantir que seja executado na thread principal da UI.
        """
        if self._app:
            self._app.after(0, lambda: messagebox.showinfo("✅ Sucesso", message))
    
    def _show_error(self, message: str):
        """
        Exibe uma mensagem de erro em uma caixa de diálogo.
        
        Usa after(0) para garantir que seja executado na thread principal da UI.
        """
        if self._app:
            self._app.after(0, lambda: messagebox.showerror("❌ Erro", message))

# ===================================================================
# 5. CLASSE: BaixarYouApp
# ===================================================================
# APLICAÇÃO PRINCIPAL (INTERFACE GRÁFICA)
# ===================================================================
class BaixarYouApp(ctk.CTk):
    """
    Aplicação principal com interface gráfica.
    
    Herda de ctk.CTk (CustomTkinter) para uma interface moderna.
    
    Componentes:
        - Campo de URL
        - Menu de qualidade
        - Checkbox de playlist
        - Botão de download
        - Barra de progresso
        - Label de status
        - Botões auxiliares (Abrir pasta, Mudar pasta, Histórico)
    """
    
    def __init__(self):
        """Inicializa a aplicação e cria os widgets"""
        super().__init__()
        
        # ============ CONFIGURAÇÕES DA JANELA ============
        self.title("📥 BaixarYou - Downloader Universal")
        self.geometry("700x620")  # Aumentado para caber informações de cookies
        self.resizable(True, True)
        
        # ============ INICIALIZA HISTÓRICO ============
        self.history = DownloadHistory()
        
        # ============ INICIALIZA WORKER ============
        self.worker = DownloadWorker(
            status_callback=self._update_status,
            progress_callback=self._update_progress,
            history=self.history
        )
        self.worker._app = self  # Referência circular para acessar a UI
        
        # ============ VARIÁVEIS DE CONTROLE ============
        self.current_download = None  # Thread do download atual
        self.downloading = False      # Flag para evitar múltiplos downloads
        
        # ============ CRIA OS WIDGETS ============
        self.create_widgets()
        
        # ============ VERIFICA ARQUIVO DE COOKIES ============
        self._check_cookie_status()
        
    def _check_cookie_status(self):
        """Verifica se o arquivo cookies.txt existe e exibe status"""
        if COOKIE_FILE.exists():
            self.status_label.configure(
                text="✅ Pronto para baixar (cookies.txt carregado)",
                text_color="green"
            )
            self.cookie_label.configure(
                text="🍪 cookies.txt encontrado - Instagram OK",
                text_color="green"
            )
        else:
            self.status_label.configure(
                text="⚠️ Sem cookies.txt - Instagram pode não funcionar",
                text_color="orange"
            )
            self.cookie_label.configure(
                text="🍪 cookies.txt NÃO encontrado - Baixe a extensão de cookies",
                text_color="orange"
            )
        
    def create_widgets(self):
        """
        Cria todos os widgets da interface gráfica.
        
        Organização:
            1. Header (título + subtítulo)
            2. Campo de URL
            3. Opções (qualidade + playlist)
            4. Botão de download
            5. Barra de progresso
            6. Status
            7. Botões auxiliares
            8. Pasta atual
        """
        
        # ==============================================================
        # 5.1 HEADER (TÍTULO E SUBTÍTULO)
        # ==============================================================
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=15)
        
        ctk.CTkLabel(header_frame, text="📥 BaixarYou", 
                    font=("Arial", 28, "bold")).pack()
        
        ctk.CTkLabel(header_frame, text="Baixe vídeos de YouTube, Instagram, TikTok, Twitter e mais",
                    font=("Arial", 11), text_color="gray").pack()
        
        # ==============================================================
        # 5.2 FRAME PRINCIPAL
        # ==============================================================
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # ==============================================================
        # 5.3 CAMPO DE URL
        # ==============================================================
        ctk.CTkLabel(main_frame, text="🔗 URL do vídeo:", font=("Arial", 13, "bold")).pack(anchor="w", pady=(10,0))
        
        self.url_entry = ctk.CTkEntry(main_frame, width=700, height=45, 
                                      placeholder_text="Cole a URL aqui... (YouTube, Instagram, TikTok, Twitter, Vimeo)")
        self.url_entry.pack(pady=5, fill="x")
        
        # ==============================================================
        # 5.4 FRAME DE OPÇÕES (QUALIDADE + PLAYLIST)
        # ==============================================================
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=10)
        
        # --- Label Qualidade ---
        ctk.CTkLabel(options_frame, text="Qualidade:", font=("Arial", 12)).pack(side="left", padx=10)
        
        # --- Menu de Qualidade ---
        self.quality_var = ctk.StringVar(value="best (recomendado)")
        quality_menu = ctk.CTkOptionMenu(
            options_frame, 
            values=["best (recomendado)", "1080p", "720p", "480p", "Apenas Áudio (MP3)"],
            variable=self.quality_var,
            width=200
        )
        quality_menu.pack(side="left", padx=10)
        
        # --- Checkbox de Playlist ---
        self.playlist_var = ctk.BooleanVar(value=False)
        playlist_check = ctk.CTkCheckBox(
            options_frame, 
            text="📋 Playlist (baixar todos)",
            variable=self.playlist_var
        )
        playlist_check.pack(side="left", padx=20)
        
        # ==============================================================
        # 5.5 BOTÃO DE DOWNLOAD
        # ==============================================================
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
        
        # ==============================================================
        # 5.6 BARRA DE PROGRESSO
        # ==============================================================
        progress_frame = ctk.CTkFrame(main_frame)
        progress_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(progress_frame, text="📊 Progresso:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10)
        
        # --- Barra de progresso visual ---
        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=500, height=20)
        self.progress_bar.pack(pady=5, padx=10, fill="x")
        self.progress_bar.set(0)  # Inicia em 0%
        
        # --- Label de percentual e velocidade ---
        self.progress_label = ctk.CTkLabel(progress_frame, text="0% - Aguardando...", font=("Arial", 11))
        self.progress_label.pack(anchor="w", padx=10, pady=5)
        
        # ==============================================================
        # 5.7 STATUS
        # ==============================================================
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
        
        # --- Informação do cookie ---
        self.cookie_label = ctk.CTkLabel(
            status_frame,
            text="🍪 Verificando cookies.txt...",
            font=("Arial", 10),
            text_color="gray"
        )
        self.cookie_label.pack(anchor="w", padx=10, pady=2)
        
        # --- Dica para exportar cookies ---
        dica_label = ctk.CTkLabel(
            status_frame,
            text="💡 Dica: Use extensão 'Get cookies.txt' no Edge/Chrome para exportar",
            font=("Arial", 9),
            text_color="gray"
        )
        dica_label.pack(anchor="w", padx=10, pady=2)
        
        # ==============================================================
        # 5.8 SEPARADOR
        # ==============================================================
        ctk.CTkFrame(main_frame, height=2, fg_color="gray").pack(fill="x", pady=10)
        
        # ==============================================================
        # 5.9 BOTÕES AUXILIARES
        # ==============================================================
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", pady=5)
        
        # --- Abrir Pasta ---
        self.pasta_btn = ctk.CTkButton(
            buttons_frame, 
            text="📂 Abrir Pasta",
            command=self.abrir_pasta,
            width=150
        )
        self.pasta_btn.pack(side="left", padx=5)
        
        # --- Mudar Pasta ---
        self.mudar_pasta_btn = ctk.CTkButton(
            buttons_frame, 
            text="🗂️ Mudar Pasta",
            command=self.mudar_pasta,
            width=150
        )
        self.mudar_pasta_btn.pack(side="left", padx=5)
        
        # --- Histórico ---
        self.historico_btn = ctk.CTkButton(
            buttons_frame, 
            text="📜 Histórico",
            command=self.ver_historico,
            width=150
        )
        self.historico_btn.pack(side="left", padx=5)
        
        # ==============================================================
        # 5.10 PASTA ATUAL
        # ==============================================================
        self.label_pasta = ctk.CTkLabel(
            main_frame, 
            text=f"📁 Pasta: {SAVE_DIR}",
            font=("Arial", 11),
            text_color="gray"
        )
        self.label_pasta.pack(pady=10)
    
    # ==============================================================
    # 5.11 MÉTODOS DE ATUALIZAÇÃO DA UI
    # ==============================================================
    
    def update_progress_bar(self, percent: float, speed: str):
        """
        Atualiza a barra de progresso e a label de velocidade.
        
        Parâmetros:
            percent (float): Percentual concluído (0-100)
            speed (str): Velocidade formatada (ex: "2.5 MB/s")
        """
        try:
            # Limita o percentual entre 0 e 100
            percent_value = min(100, max(0, float(percent))) / 100
            self.progress_bar.set(percent_value)
            
            # Formata o texto do percentual
            percent_int = int(percent_value * 100)
            self.progress_label.configure(text=f"{percent_int}% - {speed}")
            
            # Força atualização da interface
            self.update_idletasks()
        except Exception as e:
            pass  # Ignora erros para não quebrar o download
    
    def reset_progress_bar(self):
        """Reseta a barra de progresso após o download"""
        self.progress_bar.set(0)
        self.progress_label.configure(text="0% - Concluído!")
        self.after(2000, lambda: self.progress_label.configure(text="0% - Aguardando..."))
    
    def _update_status(self, message: str):
        """
        Atualiza a label de status (thread-safe).
        
        Parâmetros:
            message (str): Mensagem a ser exibida
        """
        def update():
            self.status_label.configure(text=message)
            # Muda a cor conforme o tipo de mensagem
            if "✅" in message:
                self.status_label.configure(text_color="green")
            elif "❌" in message:
                self.status_label.configure(text_color="red")
            else:
                self.status_label.configure(text_color="blue")
        self.after(0, update)
    
    def _update_progress(self, message: str):
        """
        Atualiza a label de progresso (thread-safe).
        
        Parâmetros:
            message (str): Mensagem a ser exibida
        """
        def update():
            self.progress_label.configure(text=message)
        self.after(0, update)
    
    # ==============================================================
    # 5.12 AÇÕES DOS BOTÕES
    # ==============================================================
    
    def start_download(self):
        """
        Inicia o processo de download.
        
        Verifica:
            1. Se a URL não está vazia
            2. Se não há outro download em andamento
        """
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showwarning("Aviso", "Digite ou cole uma URL válida")
            return
        
        if self.downloading:
            messagebox.showinfo("Aviso", "Um download já está em andamento.")
            return
        
        # Reseta a barra de progresso
        self.progress_bar.set(0)
        self.progress_label.configure(text="0% - Iniciando...")
        
        # Mapeia a qualidade selecionada para o formato do yt-dlp
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
        
        # Muda estado da UI
        self.downloading = True
        self.download_btn.configure(state="disabled", text="⏳ BAIXANDO...")
        
        # Inicia o download em thread separada
        self.current_download = self.worker.start_download(url, quality, is_playlist)
        
        # Inicia o monitoramento do download
        self._monitor_download()
    
    def _monitor_download(self):
        """
        Monitora se o download já terminou.
        
        Verifica periodicamente se a thread do download ainda está ativa.
        Quando termina, reativa os botões.
        """
        if self.current_download and self.current_download.is_alive():
            # Ainda está baixando - verifica novamente em 500ms
            self.after(500, self._monitor_download)
        else:
            # Download concluído - reativa a UI
            self.downloading = False
            self.download_btn.configure(state="normal", text="⬇️ BAIXAR VÍDEO")
    
    def mudar_pasta(self):
        """
        Abre um diálogo para mudar a pasta de downloads.
        
        Atualiza a variável global SAVE_DIR e a label da pasta.
        """
        global SAVE_DIR
        pasta = filedialog.askdirectory(
            title="Escolha a pasta para salvar os vídeos", 
            initialdir=str(SAVE_DIR)
        )
        if pasta:
            SAVE_DIR = Path(pasta)
            self.label_pasta.configure(text=f"📁 Pasta: {SAVE_DIR}")
            messagebox.showinfo("Pasta Alterada", f"Downloads salvos em:\n{SAVE_DIR}")
    
    def abrir_pasta(self):
        """
        Abre a pasta de downloads no explorador de arquivos.
        
        Funciona no Windows (start) e Linux/Mac (xdg-open).
        """
        try:
            if os.name == "nt":  # Windows
                os.startfile(str(SAVE_DIR))
            else:                # Linux/Mac
                subprocess.run(["xdg-open", str(SAVE_DIR)])
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")
    
    def ver_historico(self):
        """
        Exibe o histórico de downloads em uma janela separada.
        
        Mostra os últimos 20 downloads com informações:
            - Status (✅ sucesso / ❌ falha)
            - Plataforma
            - Título
            - Data/Hora
            - URL
        """
        if not self.history.history:
            messagebox.showinfo("Histórico", "Nenhum download realizado ainda.")
            return
        
        # Cria uma nova janela
        history_window = ctk.CTkToplevel(self)
        history_window.title("📜 Histórico de Downloads")
        history_window.geometry("700x500")
        
        # Caixa de texto para exibir o histórico
        text_box = ctk.CTkTextbox(history_window, font=("Consolas", 10))
        text_box.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Exibe os últimos 20 downloads
        for item in self.history.history[-20:]:
            status_icon = "✅" if item['status'] == "SUCCESS" else "❌"
            text_box.insert("end", f"{status_icon} [{item['platform']}] {item['title'][:60]}\n")
            text_box.insert("end", f"   📅 {item['timestamp'][:19]}\n")
            text_box.insert("end", f"   🔗 {item['url'][:80]}\n")
            text_box.insert("end", "-" * 60 + "\n")
        
        # Impede edição
        text_box.configure(state="disabled")

# ===================================================================
# 6. PONTO DE ENTRADA
# ===================================================================
if __name__ == "__main__":
    """
    Ponto de entrada do programa.
    
    Cria a aplicação e inicia o loop principal da interface gráfica.
    """
    app = BaixarYouApp()
    app.mainloop()  # Inicia o loop de eventos da GUI