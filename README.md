# 📥 BaixarYou - Downloader de Vídeos

Aplicativo em Python para baixar vídeos de plataformas como **YouTube, Instagram, TikTok** e outras suportadas pelo [yt-dlp](https://github.com/yt-dlp/yt-dlp).  
Os vídeos são salvos automaticamente na pasta `videos/` e você pode abrir essa pasta direto pelo programa.

## 🚀 Funcionalidades
- Baixar vídeos de diversas plataformas.
- Salvar automaticamente em `videos/`.
- Interface gráfica com **CustomTkinter** em tons pastel.
- Botão para abrir a pasta de downloads.
- Registro de erros em `download_errors.log` (limpeza automática após 7 dias).

## 📂 Estrutura
BaixarYou/
├── ffmpeg-master-latest-win64-gpl-shared/   # FFmpeg (necessário)
├── videos/                                  # Pasta dos downloads
├── main.py                                  # Código principal
├── README.md                                # Este documento
└── download_errors.log                      # Log de erros (auto-limpeza)

Código

## 🛠️ Requisitos
- Python 3.10+
- Bibliotecas: `yt-dlp`, `customtkinter`
- FFmpeg (já incluído na pasta)

Instalação:
```bash
pip install yt-dlp customtkinter
▶️ Uso
Execute:

bash
python main.py
Cole a URL do vídeo (YouTube, Instagram, TikTok...).

Clique em ⬇️ Baixar Vídeo.

Abra a pasta de downloads com 📂 Abrir Pasta de Downloads.

⚠️ Observações
FFmpeg é necessário para juntar áudio e vídeo.

O log de erros é apagado automaticamente após 7 dias.

Tema pastel pode ser alterado em:

python
ctk.set_default_color_theme("green")
📜 Licença
Uso pessoal e educacional.
Livre para modificar e distribuir.