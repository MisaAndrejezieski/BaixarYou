import yt_dlp
import tkinter as tk
from tkinter import messagebox, ttk
import os

# Caminho principal
save_folder = r'D:\Programas\BaixarYou\Salvar'
cookie_path = r'D:\Programas\BaixarYou\.venv\cookies.txt'
icon_path = r'D:\Programas\BaixarYou\Letter-B-icon_34764.ico'

# Garantir que a pasta de salvamento existe
if not os.path.exists(save_folder):
    os.makedirs(save_folder)
    print(f"Pasta de salvamento criada: {save_folder}")

# Função para baixar vídeos usando yt-dlp
def download_video(url):
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
            info_dict = ydl.extract_info(url, download=True)
            
            # Verificar se o info_dict foi preenchido corretamente
            if not info_dict:
                raise ValueError("Não foi possível obter informações da URL fornecida.")

            title = info_dict.get('title', 'Desconhecido').replace(" ", "_")
            ext = info_dict.get('ext', 'mp4')  # Usa "mp4" como padrão caso não haja extensão
            saved_path = os.path.join(save_folder, f"{title}.{ext}")

            return title, ext, saved_path, None

    except Exception as e:
        return None, None, None, f"Erro ao realizar o download: {e}"

# Função chamada ao clicar no botão "Iniciar Download"
def start_download(event=None):
    url = url_entry.get().strip()

    if not url:
        messagebox.showwarning("Aviso", "Por favor, insira uma URL válida.")
        return

    progress_label.config(text="Iniciando download...")
    progress_bar.start()
    root.update_idletasks()

    title, ext, saved_path, error = download_video(url)
    progress_bar.stop()
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
            f"Algo deu errado durante o download.\n\nDetalhes do erro:\n{error}"
        )

# Função para fechar o programa
def close_program():
    root.quit()

# Configuração da interface gráfica
root = tk.Tk()
root.title("Downloader de Vídeos")

# Aplicar o ícone, se disponível
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)
else:
    print(f"Ícone não encontrado no caminho: {icon_path}")

# Melhorias na interface gráfica
root.geometry('650x500')
root.configure(bg='#1f2937')  # Fundo escuro e moderno
root.resizable(False, False)

# Configuração de estilos
style = ttk.Style()
style.theme_use('clam')

# Botões
style.configure('TButton', background='#2563eb', foreground='#ffffff', font=('Helvetica', 12, 'bold'))
style.map('TButton', background=[('active', '#1e40af')])
style.configure('TButton.Red.TButton', background='#dc2626', foreground='#ffffff', font=('Helvetica', 12, 'bold'))
style.map('TButton.Red.TButton', background=[('active', '#991b1b')])

# Labels e Entradas
style.configure('TLabel', background='#1f2937', foreground='#ffffff', font=('Helvetica', 13))
style.configure('TEntry', font=('Helvetica', 12), padding=5)

# Elementos da interface
header_label = ttk.Label(root, text="🎥 Downloader de Vídeos 🎥", style='TLabel', font=('Helvetica', 18, 'bold'))
header_label.pack(pady=20)

ttk.Label(root, text="Cole aqui sua URL:", style='TLabel').pack(pady=10)

url_entry = ttk.Entry(root, width=65, style='TEntry')
url_entry.pack(pady=10)
url_entry.focus()

start_button = ttk.Button(root, text="Iniciar Download", command=start_download, style='TButton')
start_button.pack(pady=20)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="indeterminate")
progress_bar.pack(pady=10)

progress_label = ttk.Label(root, text="Pronto para começar!", style='TLabel', font=('Helvetica', 12))
progress_label.pack(pady=10)

close_button = ttk.Button(root, text="Fechar Programa", command=close_program, style='TButton.Red.TButton')
close_button.pack(pady=20)

footer_label = ttk.Label(root, text="Desenvolvido por Misael © 2025", style='TLabel', font=('Helvetica', 10, 'italic'))
footer_label.pack(side='bottom', pady=10)

# Rodar a interface
root.mainloop()
