import requests
import yt_dlp
import tkinter as tk
from tkinter import messagebox, ttk
import os

# Caminhos principais
save_folder = r'D:\Programas\BaixarYou\Salvar'
cookie_path = r'D:\Programas\BaixarYou\.venv\cookies.txt'

# Garantir que a pasta de salvamento existe
if not os.path.exists(save_folder):
    os.makedirs(save_folder)
    print(f"Pasta de salvamento criada: {save_folder}")

# Função para baixar diretamente imagens usando requests
def download_image(url, title):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Verifica se houve erro na requisição

        # Detectar a extensão do arquivo a partir do cabeçalho HTTP
        content_type = response.headers.get('Content-Type', '')
        if 'image/' in content_type:
            ext = content_type.split('/')[-1]  # Extrair extensão, ex.: "jpeg" ou "png"
            if ext == 'jpeg':  # Corrigir para ".jpg"
                ext = 'jpg'
        else:
            return None, f"A URL fornecida não parece ser uma imagem válida."

        # Criar caminho do arquivo para salvar
        filename = f"{title}.{ext}"
        saved_path = os.path.join(save_folder, filename)

        # Salvar a imagem no caminho especificado
        with open(saved_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        return saved_path, None
    except Exception as e:
        return None, f"Erro ao baixar a imagem: {e}"

# Função para baixar vídeos e imagens usando yt-dlp
def download_media(url):
    try:
        ydl_opts = {
            'format': 'best',  # Baixa o melhor formato disponível
            'quiet': True,
            'no_warnings': True,
            'cookiefile': cookie_path,  # Caminho para o arquivo de cookies
            'ignoreerrors': True,  # Ignorar erros e continuar
            'outtmpl': os.path.join(save_folder, '%(title)s.%(ext)s'),  # Nome do arquivo com extensão apropriada
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            # Verifica se info_dict é válido e está no formato esperado
            if not isinstance(info_dict, dict):
                raise ValueError("As informações da URL não estão no formato esperado.")

            # Pegar título e tipo de mídia corretamente
            title = info_dict.get('title', 'Desconhecido').replace(" ", "_")
            ext = info_dict.get('ext', 'mp4')  # Usa "mp4" como padrão caso não haja extensão

            # Determinar se é uma imagem direta
            if info_dict.get('_type') == 'url' and 'image' in info_dict.get('url', ''):
                saved_path, error = download_image(info_dict['url'], title)
                if error:
                    return None, None, error
            else:
                # Baixar normalmente se não for uma imagem direta
                ydl.download([url])
                saved_path = os.path.join(save_folder, f"{title}.{ext}")

            # Verificar se o arquivo foi baixado com sucesso
            if not os.path.exists(saved_path):
                raise FileNotFoundError(f"O arquivo {saved_path} não foi encontrado após o download.")

            return title, ext, saved_path, None

    except FileNotFoundError as fnf_error:
        return None, None, None, f"Erro ao salvar o arquivo: {fnf_error}"
    except ValueError as value_error:
        return None, None, None, f"Erro nos dados retornados: {value_error}"
    except Exception as e:
        return None, None, None, f"Erro inesperado: {e}"

# Função chamada ao clicar no botão "Iniciar Download"
def start_download(event=None):
    url = url_entry.get().strip()

    if not url:
        messagebox.showwarning("Aviso", "Por favor, insira uma URL válida.")
        return

    progress_label.config(text="Iniciando download...")
    root.update_idletasks()

    title, ext, saved_path, result = download_media(url)
    if title:
        progress_label.config(text="Download concluído!")
        messagebox.showinfo(
            "Sucesso",
            f"O download foi concluído com sucesso!\n\n"
            f"➡ Título: {title}\n"
            f"➡ Tipo de mídia: {ext}\n"
            f"➡ Caminho do arquivo: {saved_path}"
        )
    else:
        progress_label.config(text="Erro no download.")
        messagebox.showerror(
            "Erro",
            f"Algo deu errado durante o download.\n\nDetalhes do erro:\n{result}"
        )

# Função para fechar o programa
def close_program():
    root.quit()

# Configuração da interface gráfica
root = tk.Tk()
root.title("Downloader de Mídias - Vídeos e Imagens")

# Verificar se o ícone existe antes de aplicar
icon_path = r'D:\Programas\BaixarYou\Letter-B-icon_34764.ico'
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)
else:
    print(f"Ícone não encontrado no caminho: {icon_path}")

# Configuração de cores e estilos
root.geometry('500x400')  # Ajuste para uma interface mais espaçosa
root.configure(bg='#282c34')

style = ttk.Style()
style.theme_use('clam')

style.configure('TButton', background='#4CAF50', foreground='#ffffff', font=('Helvetica', 12, 'bold'))
style.map('TButton', background=[('active', '#56b6c2')])
style.configure('TButton.Red.TButton', background='#f44336', foreground='#ffffff', font=('Helvetica', 12, 'bold'))
style.map('TButton.Red.TButton', background=[('active', '#d32f2f')])
style.configure('TLabel', background='#282c34', foreground='#61afef', font=('Helvetica', 12))
style.configure('TEntry', font=('Helvetica', 12), padding=5)

# Elementos da interface
ttk.Label(root, text="Cole aqui sua URL:", style='TLabel').pack(pady=20)

url_entry = ttk.Entry(root, width=50, style='TEntry')
url_entry.pack(pady=10)
url_entry.focus()  # Foca no campo de entrada ao iniciar o programa

start_button = ttk.Button(root, text="Iniciar Download", command=start_download, style='TButton')
start_button.pack(pady=20)

close_button = ttk.Button(root, text="Fechar Programa", command=close_program, style='TButton.Red.TButton')
close_button.pack(pady=10)

progress_label = ttk.Label(root, text="", style='TLabel')
progress_label.pack(pady=10)

# Rodar a interface
root.mainloop()
