# ===================================================================
# BaixarYou - Downloader de Vídeos do YouTube
# ===================================================================
# Versão: 1.3
#
# Histórico:
#   1.0 - Versão inicial funcional.
#   1.1 - Robustez: save_dir, logging, ignoreerrors.
#   1.2 - Correções de thread-safety e atualização de extractor:
#         - js_runtimes movido para nível superior do ydl_opts
#         - player_client atualizado (android removido)
#         - progress_hook thread-safe via self.after
#         - reset do botão centralizado no monitor_download
#   1.3 - Correção do formato de js_runtimes para a API Python:
#         - dict {runtime: {config}} em vez de list
#         - path explícito para o executável do Node
# ===================================================================

import logging
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

# Pasta padrão de downloads (criada automaticamente na primeira execução)
SAVE_DIR_DEFAULT = BASE_DIR / "Downloads"
SAVE_DIR_DEFAULT.mkdir(exist_ok=True)

# Pasta de logs (criada automaticamente)
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Arquivo de cookies (opcional — pra vídeos que exigem login)
COOKIE_FILE = BASE_DIR / "cookies.txt"

# Caminho do executável do Node.js. Usado no ydl_opts['js_runtimes'].
# Se mudar de lugar, atualize aqui.
NODEJS_PATH = r"D:\NodeJS\node.exe"

# ===================================================================
# LOGGING
# ===================================================================

logging.basicConfig(
    filename=LOG_DIR / "downloader.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger("BaixarYou")

# ===================================================================
# PALETA NEON (identidade visual)
# ===================================================================
BG_WINDOW    = "#0a0a0f"
BG_FRAME     = "#12121a"
BG_ENTRY     = "#1a1a24"
BORDER       = "#2a2a38"

NEON_GREEN   = "#00ff88"
NEON_GREEN_D = "#00cc6a"
NEON_MAGENTA = "#ff1e7c"
NEON_GOLD    = "#ffb020"
NEON_GOLD_D  = "#d8941a"
NEON_CYAN    = "#00e5ff"
TEXT_WHITE   = "#f0f0f5"
TEXT_GRAY    = "#8a8a9a"
TEXT_DIM     = "#5a5a6a"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# ===================================================================
# CAMINHOS FFMPEG (busca em cascata)
# ===================================================================
FFMPEG_CANDIDATES = [
    r"D:\ffmpeg-8.1-full_build\bin\ffmpeg.exe",
    r"D:\BaixarYou\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe",
    r"C:\ffmpeg\bin\ffmpeg.exe",
    r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    str(Path.home() / "ffmpeg" / "bin" / "ffmpeg.exe"),
    str(BASE_DIR / "ffmpeg" / "bin" / "ffmpeg.exe"),
]

# ===================================================================
# FUNÇÕES AUXILIARES
# ===================================================================

def fix_youtube_url(url: str) -> str:
    """Converte qualquer URL do YouTube para o formato padrão watch?v=ID.

    Aceita: youtube.com/watch?v=..., youtu.be/..., /shorts/, /embed/,
    /v/ e URL crua com ID de 11 caracteres.
    """
    url = url.strip()

    if '?' in url and 'watch?v=' in url:
        match = re.search(r'watch\?v=([\w-]+)', url)
        if match:
            return f"https://www.youtube.com/watch?v={match.group(1)}"

    patterns = [
        r'youtube\.com/watch\?v=([\w-]+)',
        r'youtu\.be/([\w-]+)',
        r'youtube\.com/shorts/([\w-]+)',
        r'youtube\.com/embed/([\w-]+)',
        r'youtube\.com/v/([\w-]+)',
        r'youtube\.com/([\w-]{11})(?:[?/]|$)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"

    return url


def find_ffmpeg() -> str | None:
    """Procura o FFmpeg no PATH ou em locais conhecidos.

    Retorna o caminho do executável (ou a string 'ffmpeg' se estiver no
    PATH) ou None se não encontrar.
    """
    # 1. Tenta pelo PATH do sistema
    try:
        subprocess.run(
            ['ffmpeg', '-version'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        logger.info("FFmpeg encontrado no PATH do sistema")
        return "ffmpeg"
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    # 2. Tenta caminhos conhecidos
    for candidate in FFMPEG_CANDIDATES:
        if Path(candidate).exists():
            logger.info(f"FFmpeg encontrado em: {candidate}")
            return candidate

    logger.warning("FFmpeg não encontrado em nenhum caminho conhecido")
    return None


def check_nodejs() -> bool:
    """Verifica se o Node.js está acessível (via PATH).

    Esta checagem serve só pra mostrar o status na UI. O yt-dlp usa o
    caminho explícito definido em NODEJS_PATH para o js_runtimes.
    """
    try:
        subprocess.run(
            ['node', '--version'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

# ===================================================================
# CLASSE PRINCIPAL
# ===================================================================

class BaixarYouApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("📥 BaixarYou")
        self.geometry("680x600")
        self.resizable(False, False)
        self.configure(fg_color=BG_WINDOW)

        # Estado interno
        self.downloading = False
        self.save_dir = SAVE_DIR_DEFAULT
        self.ffmpeg_path = find_ffmpeg()
        self.has_ffmpeg = self.ffmpeg_path is not None
        self.has_nodejs = check_nodejs()

        # Log de inicialização
        logger.info("=" * 60)
        logger.info("BaixarYou iniciado")
        logger.info(f"Pasta padrão: {self.save_dir}")
        logger.info(f"FFmpeg: {self.ffmpeg_path or 'NÃO ENCONTRADO'}")
        logger.info(f"Node.js (PATH): {'OK' if self.has_nodejs else 'NÃO ENCONTRADO'}")
        logger.info(f"Node.js (path explícito): {NODEJS_PATH}")
        logger.info(f"Cookies: {'OK' if COOKIE_FILE.exists() else 'ausente'}")
        logger.info("=" * 60)

        self.create_widgets()
        self.check_cookies()
        self.check_status()

    # ================================================================
    # CONSTRUÇÃO DA UI
    # ================================================================

    def create_widgets(self):
        """Monta toda a interface gráfica."""

        # ----- TÍTULO -----
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(pady=(25, 0))

        ctk.CTkLabel(
            title_frame,
            text="Baixar",
            font=("Arial", 38, "bold"),
            text_color=NEON_GREEN,
        ).pack(side="left")

        ctk.CTkLabel(
            title_frame,
            text="You",
            font=("Arial", 38, "bold"),
            text_color=NEON_MAGENTA,
        ).pack(side="left")

        ctk.CTkLabel(
            self,
            text="download de vídeos do YouTube",
            font=("Arial", 11),
            text_color=TEXT_GRAY,
        ).pack(pady=(0, 20))

        # ----- FRAME PRINCIPAL -----
        main_frame = ctk.CTkFrame(
            self,
            fg_color=BG_FRAME,
            corner_radius=16,
            border_width=1,
            border_color=BORDER,
        )
        main_frame.pack(fill="both", expand=True, padx=30, pady=(0, 10))

        # ----- CAMPO DE URL -----
        ctk.CTkLabel(
            main_frame,
            text="🔗  URL do vídeo",
            font=("Arial", 12, "bold"),
            text_color=TEXT_WHITE,
        ).pack(anchor="w", padx=25, pady=(20, 8))

        self.url_entry = ctk.CTkEntry(
            main_frame,
            height=45,
            placeholder_text="Cole a URL do YouTube aqui...",
            fg_color=BG_ENTRY,
            border_color=NEON_GREEN,
            border_width=1,
            text_color=TEXT_WHITE,
            placeholder_text_color=TEXT_DIM,
            corner_radius=8,
        )
        self.url_entry.pack(fill="x", padx=25, pady=(0, 15))
        self.url_entry.bind('<Return>', lambda e: self.start_download())

        # ----- SELETOR DE QUALIDADE -----
        quality_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        quality_frame.pack(fill="x", padx=25, pady=8)

        ctk.CTkLabel(
            quality_frame,
            text="Qualidade:",
            font=("Arial", 12),
            text_color=TEXT_WHITE,
        ).pack(side="left", padx=(0, 10))

        qualities = ["Melhor (MP4)", "720p (MP4)", "Apenás Áudio (MP3)"]
        self.quality_var = ctk.StringVar(value=qualities[0])

        quality_menu = ctk.CTkOptionMenu(
            quality_frame,
            values=qualities,
            variable=self.quality_var,
            width=200,
            height=32,
            fg_color=BG_ENTRY,
            button_color=NEON_GREEN,
            button_hover_color=NEON_GREEN_D,
            text_color=TEXT_WHITE,
            dropdown_fg_color=BG_FRAME,
            dropdown_text_color=TEXT_WHITE,
            dropdown_hover_color=NEON_GREEN_D,
            corner_radius=8,
        )
        quality_menu.pack(side="left")

        # ----- SELETOR DE PASTA -----
        pasta_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        pasta_frame.pack(fill="x", padx=25, pady=10)

        self.pasta_label = ctk.CTkLabel(
            pasta_frame,
            text=f"📁  {self.save_dir}",
            font=("Arial", 10),
            text_color=TEXT_GRAY,
        )
        self.pasta_label.pack(side="left")

        ctk.CTkButton(
            pasta_frame,
            text="Alterar",
            width=80,
            height=30,
            font=("Arial", 11, "bold"),
            fg_color="transparent",
            hover_color=BG_ENTRY,
            text_color=NEON_GOLD,
            border_width=1,
            border_color=NEON_GOLD,
            corner_radius=6,
            command=self.mudar_pasta,
        ).pack(side="right")

        # ----- STATUS FFMPEG / NODE -----
        self.status_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.status_frame.pack(fill="x", padx=25, pady=(5, 0))

        self.ffmpeg_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=("Arial", 10),
            text_color=TEXT_GRAY,
        )
        self.ffmpeg_label.pack(anchor="w")

        self.node_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=("Arial", 10),
            text_color=TEXT_GRAY,
        )
        self.node_label.pack(anchor="w")

        # ----- BOTÃO BAIXAR -----
        self.download_btn = ctk.CTkButton(
            main_frame,
            text="⬇️  BAIXAR",
            command=self.start_download,
            height=52,
            font=("Arial", 16, "bold"),
            fg_color=NEON_GREEN,
            hover_color=NEON_GREEN_D,
            text_color="#000000",
            corner_radius=10,
        )
        self.download_btn.pack(fill="x", padx=25, pady=(20, 15))

        # ----- BARRA DE PROGRESSO -----
        self.progress_bar = ctk.CTkProgressBar(
            main_frame,
            height=12,
            fg_color=BG_ENTRY,
            progress_color=NEON_GREEN,
            corner_radius=0,
        )
        self.progress_bar.pack(fill="x", padx=25, pady=5)
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            main_frame,
            text="Aguardando...",
            font=("Arial", 10),
            text_color=TEXT_GRAY,
        )
        self.progress_label.pack(pady=(2, 5))

        # ----- STATUS FINAL -----
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="✅ Pronto",
            font=("Arial", 11),
            text_color=NEON_GREEN,
        )
        self.status_label.pack(pady=(0, 15))

        # ----- RODAPÉ -----
        ctk.CTkLabel(
            self,
            text="💜  Desenvolvido por Misa  💜",
            font=("Arial", 10, "bold"),
            text_color=NEON_MAGENTA,
        ).pack(side="bottom", pady=(0, 12))

    # ================================================================
    # STATUS E CONFIGURAÇÕES
    # ================================================================

    def check_status(self):
        """Atualiza as labels de status do FFmpeg e Node.js."""
        if self.has_ffmpeg:
            self.ffmpeg_label.configure(
                text=f"✅  FFmpeg: {self.ffmpeg_path}",
                text_color=NEON_GREEN,
            )
        else:
            self.ffmpeg_label.configure(
                text="⚠️  FFmpeg: não instalado (qualidade limitada)",
                text_color=NEON_GOLD,
            )

        if self.has_nodejs:
            self.node_label.configure(
                text="✅  Node.js: instalado",
                text_color=NEON_GREEN,
            )
        else:
            self.node_label.configure(
                text="⚠️  Node.js: não instalado (pode ter problemas)",
                text_color=NEON_GOLD,
            )

    def check_cookies(self):
        """Verifica se o arquivo de cookies existe."""
        if COOKIE_FILE.exists():
            self.status_label.configure(
                text="✅  Cookies carregados",
                text_color=NEON_GREEN,
            )
        else:
            self.status_label.configure(
                text="ℹ️  Sem cookies",
                text_color=TEXT_GRAY,
            )

    def mudar_pasta(self):
        """Abre o diálogo pra escolher outra pasta de download."""
        pasta = filedialog.askdirectory(
            title="Escolha a pasta",
            initialdir=str(self.save_dir),
        )
        if pasta:
            self.save_dir = Path(pasta)
            self.pasta_label.configure(text=f"📁  {self.save_dir}")
            self.status_label.configure(
                text="📁  Pasta alterada",
                text_color=NEON_CYAN,
            )
            logger.info(f"Pasta de download alterada para: {self.save_dir}")

    # ================================================================
    # PROGRESSO
    # ================================================================
    # O yt-dlp chama o progress_hook a partir da thread de download.
    # Tkinter/customtkinter NÃO é thread-safe. Por isso empacotamos
    # a atualização da UI via self.after(0, ...), que executa o
    # callback na main thread.
    # ================================================================

    def update_progress(self, d):
        """Callback chamado pela thread do yt-dlp. Repassa pra main thread."""
        self.after(0, lambda: self._update_progress_ui(d))

    def _update_progress_ui(self, d):
        """Atualização real da barra de progresso. Roda na main thread."""
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
            self.progress_label.configure(
                text=f"{int(percent)}%  •  {speed_str}",
                text_color=NEON_GREEN,
            )

        elif d['status'] == 'finished':
            self.progress_bar.set(1)
            self.progress_label.configure(
                text="100%  •  Finalizando...",
                text_color=NEON_CYAN,
            )

    # ================================================================
    # FLUXO DE DOWNLOAD
    # ================================================================

    def start_download(self):
        """Valida a URL, ajusta a UI e dispara a thread de download."""
        url = self.url_entry.get().strip()

        if not url:
            messagebox.showwarning("Aviso", "Digite uma URL!")
            return

        if self.downloading:
            messagebox.showinfo("Aviso", "Download em andamento...")
            return

        # Normaliza URLs do YouTube
        if 'youtube.com' in url or 'youtu.be' in url:
            url = fix_youtube_url(url)
            self.url_entry.delete(0, 'end')
            self.url_entry.insert(0, url)

        # Atualiza UI para estado "baixando"
        self.downloading = True
        self.download_btn.configure(state="disabled", text="⏳  BAIXANDO...")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Iniciando...", text_color=NEON_CYAN)
        self.status_label.configure(text="🔄  Baixando...", text_color=NEON_CYAN)

        logger.info(f"Iniciando download: {url} | Qualidade: {self.quality_var.get()}")

        # Dispara a thread de download
        thread = threading.Thread(
            target=self.download_video,
            args=(url,),
            daemon=True,
        )
        thread.start()
        self.monitor_download(thread)

    def monitor_download(self, thread):
        """Verifica periodicamente se a thread de download terminou.

        Roda sempre na main thread (via self.after). Quando a thread
        morre, restaura o botão e limpa a barra de progresso.
        """
        if thread.is_alive():
            self.after(500, lambda: self.monitor_download(thread))
        else:
            self.downloading = False
            self.download_btn.configure(state="normal", text="⬇️  BAIXAR")
            self.progress_bar.set(0)
            self.progress_label.configure(text="Aguardando...", text_color=TEXT_GRAY)

    def download_video(self, url):
        """Executa o download. Roda em thread separada.

        Toda atualização de UI é empacotada via self.after(0, ...) para
        rodar na main thread — o Tkinter não é thread-safe.
        """
        try:
            quality = self.quality_var.get()

            # ------------------------------------------------
            # Define o format_spec e postprocessors conforme a qualidade
            # ------------------------------------------------
            if quality == "Apenás Áudio (MP3)":
                format_spec = "bestaudio/best"
                postprocessors = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
                merge_format = None
            else:
                if self.has_ffmpeg:
                    if quality == "Melhor (MP4)":
                        format_spec = "bestvideo+bestaudio/best"
                    else:  # 720p
                        format_spec = "bestvideo[height<=720]+bestaudio/best[height<=720]"

                    postprocessors = []
                    merge_format = "mp4"
                else:
                    # Sem FFmpeg: pega o melhor arquivo único em MP4
                    format_spec = "best[ext=mp4]"
                    postprocessors = []
                    merge_format = None

            # ------------------------------------------------
            # Opções do yt-dlp
            # ------------------------------------------------
            ydl_opts = {
                'outtmpl': str(self.save_dir / '%(title)s.%(ext)s'),
                'format': format_spec,
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [self.update_progress],
                'retries': 10,
                'fragment_retries': 10,
                'ignoreerrors': False,
                'postprocessors': postprocessors,

                # ------------------------------------------------
                # JS runtime (yt-dlp >= 2025.11).
                # Formato da API Python: dict {runtime: {config}}.
                # Node NÃO é ativado por padrão — precisa ser declarado.
                # O path explícito evita depender do PATH do sistema.
                # ------------------------------------------------
                'js_runtimes': {
                    'node': {
                        'path': NODEJS_PATH,
                    },
                },

                'extractor_args': {
                    'youtube': {
                        # android foi deprecado; web/ios/tv são os atuais.
                        'player_client': ['web', 'ios', 'tv'],
                    }
                },
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                }
            }

            # Ajustes condicionais
            if merge_format:
                ydl_opts['merge_output_format'] = merge_format

            if self.ffmpeg_path:
                ydl_opts['ffmpeg_location'] = self.ffmpeg_path

            if COOKIE_FILE.exists():
                ydl_opts['cookiefile'] = str(COOKIE_FILE)

            # ------------------------------------------------
            # Executa o download
            # ------------------------------------------------
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                if info is None:
                    raise Exception("Não foi possível obter informações do vídeo.")

                titulo = info.get('title', 'Vídeo')

                # UI: empacotado para a main thread
                self.after(0, lambda: self.status_label.configure(
                    text=f"✅  Concluído: {titulo[:50]}",
                    text_color=NEON_GREEN,
                ))
                self.after(0, lambda: self._on_success(titulo, quality))

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Falha no download [{url}]: {error_msg}")

            # Mapeia erros comuns para mensagens amigáveis
            if "Video unavailable" in error_msg:
                mensagem = "❌ Vídeo indisponível ou removido."
            elif "Private video" in error_msg:
                mensagem = "❌ Este vídeo é privado."
            elif "Sign in to confirm" in error_msg or "verify" in error_msg.lower():
                mensagem = (
                    "❌ YouTube pede verificação.\n\n"
                    "💡 Soluções:\n"
                    "1. Use cookies.txt (faça login e exporte)\n"
                    "2. Aguarde alguns minutos e tente novamente"
                )
            elif "HTTP Error 403" in error_msg or "Forbidden" in error_msg:
                mensagem = (
                    "❌ Acesso bloqueado pelo YouTube.\n\n"
                    "💡 Soluções:\n"
                    "1. Use cookies.txt\n"
                    "2. Atualize o yt-dlp: pip install --upgrade yt-dlp"
                )
            elif "Requested format" in error_msg:
                mensagem = (
                    "❌ Formato não disponível.\n\n"
                    "💡 Tente:\n"
                    "- Outro vídeo\n"
                    "- Opção '720p (MP4)'\n"
                    "- Opção 'Apenas Áudio (MP3)'"
                )
            elif "ffmpeg" in error_msg.lower():
                mensagem = "❌ FFmpeg necessário.\n\nInstale o FFmpeg para este formato."
            else:
                mensagem = f"❌ Erro ao baixar:\n\n{error_msg[:300]}"

            # UI: empacotado para a main thread
            self.after(0, lambda: self.status_label.configure(
                text="❌  Falha no download",
                text_color=NEON_MAGENTA,
            ))
            self.after(0, lambda: messagebox.showerror("Erro", mensagem))

        # NOTA: o reset do botão/barra fica em monitor_download, que roda
        # na main thread via after(). Não duplicar aqui.

    def _on_success(self, titulo, quality):
        """Feedback visual de sucesso. Roda na main thread."""
        self.url_entry.delete(0, 'end')
        self.url_entry.insert(0, "✅ Download concluído!")
        self.url_entry.after(3000, lambda: self.url_entry.delete(0, 'end'))

        msg = f"✅ Vídeo baixado com sucesso!\n\n📹 {titulo}\n📁 {self.save_dir}"

        if not self.has_ffmpeg and quality != "Apenás Áudio (MP3)":
            msg += "\n\n⚠️ Sem FFmpeg: baixado em qualidade limitada."

        logger.info(f"Download OK: {titulo} -> {self.save_dir}")
        messagebox.showinfo("Sucesso", msg)

# ===================================================================
# EXECUÇÃO
# ===================================================================

if __name__ == "__main__":
    app = BaixarYouApp()
    app.mainloop()