import yt_dlp
import whisper
from fpdf import FPDF
import requests
import json
import os

OLLAMA_API_URL = "http://localhost:11434"

# Função para interagir com o Ollama (Llama 3.2)
def corrigir_transcricao_com_ai(texto, modelo="llama3.2"):
    # Prompt mais restritivo: sem criação de novas frases e sem adição de informações extras
    prompt = (f"Você deve corrigir apenas as palavras que estiverem erradas, baseando-se na transcrição do áudio que você recebeu. "
              f"Não adicione novas frases, palavras ou informações que não estão presentes no áudio original. "
              f"A transcrição precisa ser mantida com o conteúdo do vídeo. Corrija apenas erros gramaticais e vocabulários que não sejam do português brasileiro. "
              f"Não faça alterações além das necessárias, e não adicione nenhuma explicação ou comentário sobre as correções feitas. "
              f"Texto a ser corrigido:\n\n{texto}")

    try:
        response = requests.post(
            f"{OLLAMA_API_URL}/api/generate",
            json={
                "model": modelo,
                "prompt": prompt
            },
            timeout=60
        )

        # Verifica se a resposta foi bem-sucedida
        if response.status_code == 200:
            try:
                # Processa a resposta em partes (caso venha como streaming)
                response_text = ""
                for line in response.iter_lines(decode_unicode=True):  # Decodifica como UTF-8
                    if line.strip():
                        line_data = json.loads(line)
                        response_text += line_data.get("response", "")

                # Remover comentários da IA (qualquer explicação ou comentário)
                response_text = response_text.replace("A frase corrigida em português brasileiro seria:", "").strip()
                response_text = response_text.replace("Nenhuma palavra foi alterada, apenas verificada se estava no vocabulário português brasileiro.", "").strip()

                # Garantir que não há frases novas
                # Remover qualquer frase extra que não tenha no áudio
                response_text = " ".join([line for line in response_text.splitlines() if line.strip() != ""])

                return response_text.strip()
            except json.JSONDecodeError as e:
                print(f"Erro ao decodificar JSON: {e}")
                print(f"Resposta bruta: {response.text}")
                return texto  # Retorna o texto original em caso de erro no JSON
        else:
            print(f"Erro na API Ollama: {response.status_code} - {response.text}")
            return texto  # Retorna o texto original em caso de erro na API

    except requests.exceptions.RequestException as e:
        print(f"Erro de comunicação com Ollama: {e}")
        return texto  # Retorna o texto original em caso de erro de comunicação


# Função para transcrever e corrigir o áudio
def transcrever_por_topicos(audio_path):
    modelo = whisper.load_model("base")
    resultado = modelo.transcribe(audio_path, word_timestamps=False)

    topicos = []
    for segmento in resultado['segments']:
        inicio = segmento['start']
        fim = segmento['end']
        texto = segmento['text']

        try:
            texto_corrigido = corrigir_transcricao_com_ai(texto)
        except Exception as e:
            print(f"Erro ao corrigir transcrição: {e}")
            texto_corrigido = texto  # Usa o texto original em caso de erro

        topicos.append({
            "inicio": f"{int(inicio // 60)}:{int(inicio % 60):02d}",
            "fim": f"{int(fim // 60)}:{int(fim % 60):02d}",
            "texto": texto_corrigido.strip()
        })

    return topicos


# Função para gerar o PDF
def gerar_pdf_por_topicos(topicos, output_path="teste-em-pdf.pdf"):
    pdf = FPDF()
    pdf.add_page()

    # Caminho do arquivo de fonte TTF
    font_path = "DejaVuSans.ttf"  # Defina o caminho da sua fonte

    # Verificar se o arquivo de fonte existe
    if not os.path.exists(font_path):
        print(f"Erro: A fonte '{font_path}' não foi encontrada!")
        return

    # Adiciona a fonte TTF (DejaVuSans) ao PDF
    pdf.add_font('DejaVu', '', font_path, uni=True)
    pdf.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf', uni=True)
    pdf.add_font('DejaVu', 'I', 'DejaVuSans-Oblique.ttf', uni=True)

    pdf.set_font('DejaVu', '', 12)  # Usando a fonte DejaVuSans

    for i, topico in enumerate(topicos, start=1):
        pdf.set_font("DejaVu", 'B', size=12)
        pdf.cell(0, 10, f"Tópico {i} ({topico['inicio']} - {topico['fim']})", ln=True)
        pdf.set_font("DejaVu", '', size=12)
        pdf.multi_cell(0, 10, topico['texto'])
        pdf.ln(5)

    pdf.output(output_path)


# Função para extrair o áudio de um vídeo do YouTube sem baixá-lo completamente
def extrair_audio_youtube(url_video, caminho_audio="audio_extraido.mp3"):
    # Verificar se a pasta existe, caso contrário, criar
    caminho_destino = r"C:\Users\beatr\OneDrive\Área de Trabalho\Verbo-Janga\from-audio-to-pdf"
    if not os.path.exists(caminho_destino):
        os.makedirs(caminho_destino)

    ydl_opts = {
        'format': 'bestaudio/best',  # Extrair apenas o melhor áudio
        'extractaudio': True,        # Extração de áudio
        'audioquality': 0,           # Melhor qualidade
        'outtmpl': os.path.join(caminho_destino, '%(title)s.%(ext)s'),  # Caminho para salvar o áudio
        'quiet': True,               # Suprime os logs para uma execução limpa
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Mudança: download=True para salvar o áudio
        info_dict = ydl.extract_info(url_video, download=True)
        # Obtendo o caminho do arquivo de áudio baixado
        audio_path = ydl.prepare_filename(info_dict)  # Garante o caminho correto do arquivo
        print(f"Áudio extraído com sucesso: {audio_path}")

    return audio_path


# Exemplo de uso
url_video = "https://www.youtube.com/watch?v=2ayt3eouRvE"  # Substitua com o URL do vídeo do YouTube
try:
    caminho_audio = extrair_audio_youtube(url_video)  # Extrai o áudio do YouTube
    topicos = transcrever_por_topicos(caminho_audio)  # Transcreve o áudio extraído
    gerar_pdf_por_topicos(topicos)  # Gera o PDF com os tópicos
    print("PDF gerado com tópicos separados e transcrição corrigida!")
except Exception as e:
    print(f"Ocorreu um erro durante o processamento: {e}")
