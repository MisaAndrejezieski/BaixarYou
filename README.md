📥 BaixarYou - Downloader de Vídeos do YouTube
<div align="center">
https://img.shields.io/badge/Python-3.8+-blue.svg
https://img.shields.io/badge/License-MIT-green.svg
https://img.shields.io/badge/Status-Est%25C3%25A1vel-brightgreen.svg
https://img.shields.io/badge/Platform-Windows-orange.svg

Baixe vídeos do YouTube com qualidade máxima e interface gráfica moderna

</div>
📋 Índice
Sobre o Projeto

Funcionalidades

Demonstração

Pré-requisitos

Instalação

Como Usar

Resolução de Problemas

Tecnologias Utilizadas

Aviso Legal

Licença

📖 Sobre o Projeto
BaixarYou é um downloader de vídeos do YouTube com interface gráfica intuitiva, desenvolvido em Python. Com ele, você pode baixar vídeos em alta qualidade (até 1080p) ou extrair apenas o áudio em MP3, tudo com uma interface moderna e fácil de usar.

Por que BaixarYou?
🎯 Simples - Cole a URL e clique em baixar

🚀 Rápido - Downloads otimizados com suporte a multi-threading

🎨 Bonito - Interface moderna com CustomTkinter

🛡️ Confiável - Suporte a cookies para autenticação

✨ Funcionalidades
Funcionalidade	Descrição
📹 Download de Vídeos	Baixe em até 1080p com áudio incluso
🎵 Extração de Áudio	Converta vídeos para MP3 (192kbps)
📊 Barra de Progresso	Acompanhe em tempo real com velocidade
🍪 Suporte a Cookies	Evita bloqueios do YouTube
📂 Pasta Personalizável	Escolha onde salvar seus arquivos
⚡ Multi-threading	Interface não trava durante o download
🎨 Modo Escuro	Interface moderna e confortável
⌨️ Atalho Enter	Baixe rapidamente pressionando Enter
🖥️ Demonstração
<div align="center"> <img src="screenshot.png" alt="Interface do BaixarYou" width="600"> </div>
Opções de Qualidade:
Opção	Descrição	Requer FFmpeg?
Melhor (MP4)	Baixa a melhor qualidade disponível	✅ Sim
720p (MP4)	Baixa em HD (1280x720)	✅ Sim
Apenás Áudio (MP3)	Extrai apenas o áudio em MP3	✅ Sim
💡 Dica: Instale o FFmpeg para ter acesso a todos os formatos e qualidades.

📦 Pré-requisitos
Dependências Obrigatórias:
Python 3.8+

Node.js (necessário para extração de formatos)

Dependências Opcionais:
FFmpeg (para qualidade máxima e extração de MP3)

Bibliotecas Python:
text
yt-dlp >= 2024.12.13
customtkinter >= 5.2.0
🚀 Instalação
Método 1: Clonar e Executar (Recomendado)
bash
# Clone o repositório
git clone https://github.com/MisaAndrejezieski/BaixarYou.git
cd BaixarYou

# Crie um ambiente virtual
python -m venv .venv

# Ative o ambiente virtual
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Execute o programa
python main.py
Método 2: Download Direto
Baixe o arquivo BaixarYou.exe da seção Releases

Execute diretamente (não requer Python instalado)

📖 Como Usar
Download Básico
Copie a URL do vídeo do YouTube

Cole no campo "URL do vídeo"

Selecione a qualidade desejada no menu suspenso:

Melhor (MP4) - Melhor qualidade disponível

720p (MP4) - Alta definição

Apenás Áudio (MP3) - Extrai apenas o áudio

Clique em "BAIXAR" ou pressione Enter

Aguarde - o arquivo será salvo na pasta Downloads/

Gerenciando Downloads
📂 Abrir Pasta - Clique no botão "Alterar" para escolher onde salvar

📜 Histórico - O programa mantém registro dos downloads (opcional)

Configurando Cookies (Opcional)
Se o YouTube estiver bloqueando os downloads:

Instale a extensão "Get cookies.txt LOCALLY"

Faça login no YouTube pelo navegador

Exporte os cookies como cookies.txt

Coloque o arquivo na pasta do BaixarYou

🛠️ Resolução de Problemas
Erro: "Requested format is not available"
Solução:

Verifique se o Node.js está instalado: node --version

Atualize o yt-dlp: pip install --upgrade yt-dlp

Use a opção "720p (MP4)" ou "Apenás Áudio (MP3)"

Erro: "FFmpeg not found"
Solução:

Baixe o FFmpeg: ffmpeg.org

Copie ffmpeg.exe para a pasta do BaixarYou

Ou adicione ao PATH do sistema

Erro: "Sign in to confirm"
Solução:

Exporte os cookies do YouTube com a extensão

Coloque cookies.txt na pasta do projeto

Tente novamente

O vídeo não tem áudio
Solução:

Instale o FFmpeg na pasta do projeto

Use a opção "Melhor (MP4)" que combina vídeo + áudio

O programa vai automaticamente mesclar os arquivos

🔬 Tecnologias Utilizadas
Tecnologia	Uso
Python 3.8+	Linguagem principal
yt-dlp	Engine de download (fork do youtube-dl)
CustomTkinter	Interface gráfica moderna
Tkinter	Base da GUI
FFmpeg	Processamento e merge de áudio/vídeo
Node.js	Extração de formatos do YouTube
Threading	Execução assíncrona (não trava a UI)
⚠️ Aviso Legal
Este software é fornecido apenas para fins educacionais e uso pessoal legítimo.

📜 Respeite os direitos autorais - Baixe apenas conteúdo que você tem permissão

🔒 Verifique os Termos de Serviço - Cada plataforma possui suas próprias regras

👤 Uso pessoal - Destina-se ao download de conteúdo próprio ou domínio público

⚖️ Responsabilidade - O autor não se responsabiliza por uso indevido

💡 Dica: Use esta ferramenta para baixar seus próprios vídeos, conteúdos Creative Commons ou materiais com permissão explícita do criador.

🤝 Contribuição
Contribuições são bem-vindas!

Faça um Fork do projeto

Crie uma Branch para sua feature (git checkout -b feature/nova-funcionalidade)

Faça o Commit (git commit -m 'Adiciona nova funcionalidade')

Faça o Push (git push origin feature/nova-funcionalidade)

Abra um Pull Request

Áreas que precisam de contribuição:
✅ Testes automatizados

🔧 Suporte a mais plataformas

🌐 Versão para Linux/macOS

📦 Fila de downloads múltiplos

🎨 Interface em outros idiomas

📄 Licença
Este projeto está licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.

text
MIT License

Copyright (c) 2026 Misa Andrejezieski

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
...
🌟 Agradecimentos
yt-dlp - Pelo excelente trabalho mantendo a biblioteca

CustomTkinter - Pela interface moderna

FFmpeg - Pelo processamento de áudio e vídeo

Comunidade open-source do Python

📞 Contato
GitHub: @MisaAndrejezieski

Issues: Abrir um problema

<div align="center">
⭐ Se este projeto foi útil, considere deixar uma estrela no repositório!

Feito com ❤️ por Misa Andrejezieski

</div>
