import os
import requests
from urllib.request import urlopen
from bs4 import BeautifulSoup
import yt_dlp
import http.cookiejar

# Configuração de diretórios
BASE_DIR = "D:/Programas/BaixarYou/"
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
SAVE_DIR = os.path.join(BASE_DIR, "Salvar")
FFMPEG_DIR = os.path.join(BASE_DIR, "ffmpeg-master-latest-win64-gpl-shared/bin")

# Adicionar FFmpeg ao PATH do sistema
os.environ["PATH"] += os.pathsep + FFMPEG_DIR

def setup_folders():
    """Cria as pastas necessárias se não existirem"""
    os.makedirs(SAVE_DIR, exist_ok=True)
    os.makedirs(RESOURCES_DIR, exist_ok=True)

def load_cookies():
    """Carrega cookies se existirem"""
    cookie_file = os.path.join(RESOURCES_DIR, "cookies.txt")
    if os.path.exists(cookie_file):
        jar = http.cookiejar.MozillaCookieJar()
        jar.load(cookie_file)
        return jar
    return None

def download_video(url):
    """Baixa vídeos usando yt-dlp"""
    cookies = load_cookies()
    
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(SAVE_DIR, '%(title)s.%(ext)s'),
        'cookiefile': os.path.join(RESOURCES_DIR, "cookies.txt") if cookies else None,
        'merge_output_format': 'mp4',
        'ffmpeg_location': FFMPEG_DIR,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("Download de vídeo concluído!")
    except Exception as e:
        print(f"Erro ao baixar vídeo: {e}")

def download_image(url):
    """Baixa imagens de URLs diretas"""
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            content_type = response.headers['content-type']
            if 'image' in content_type:
                ext = content_type.split('/')[-1]
                filename = os.path.join(SAVE_DIR, f"image_{hash(url)}.{ext}")
                
                with open(filename, 'wb') as f:
                    for chunk in response:
                        f.write(chunk)
                print(f"Imagem salva em: {filename}")
            else:
                print("A URL não aponta para uma imagem válida")
    except Exception as e:
        print(f"Erro ao baixar imagem: {e}")

def main():
    setup_folders()
    
    print("Escolha o tipo de download:")
    print("1 - Vídeo")
    print("2 - Imagem")
    
    choice = input("Digite sua opção (1/2): ")
    url = input("Cole a URL: ")

    if choice == '1':
        download_video(url)
    elif choice == '2':
        download_image(url)
    else:
        print("Opção inválida")

if __name__ == "__main__":
    main()
