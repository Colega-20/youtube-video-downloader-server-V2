from flask import Flask, request, render_template, send_from_directory, jsonify, send_file
import yt_dlp
import os, time, urllib.parse
import threading
import re
import daemon

# from http.server import HTTPServer
# from flask_cors import CORS
# from http.server import BaseHTTPRequestHandler
ffmpeg_path = os.getenv("FFMPEG_PATH", "ffmpeg")
print("Ruta de ffmpeg:", ffmpeg_path)
app = Flask(__name__)

# Carpeta donde se guardarán los videos descargados
DOWNLOAD_FOLDER = "./descargas"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
# Configurar Flask para servir archivos estáticos desde la carpeta de descargas
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
last_access_times = {}# Diccionario para rastrear el último acceso a cada archivo
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36' #user agent
lock = threading.Lock() # Bloqueo para evitar problemas de concurrencia

# Mapeo de números a opciones de calidad
QUALITY_OPTIONS = {
    '0': 'bestaudio[acodec=opus]/bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio',                    # Solo audio
    '1': 'bestvideo[height<=360][vcodec^=avc1]+bestaudio[ext=m4a]/best[height<=360]',   # 360p
    '2': 'bestvideo[height<=480][vcodec^=avc1]+bestaudio[ext=m4a]/best[height<=480]',   # 480p
    '3': 'bestvideo[height<=720][vcodec^=avc1]+bestaudio[ext=m4a]/best[height<=720]',   # 720p
    '4': 'bestvideo[height<=1080][vcodec^=avc1]+bestaudio[ext=m4a]/best[height<=1080]', # 1080p
    '5': 'bestvideo[height<=1440][vcodec^=vp9]+bestaudio[ext=m4a]/best[height<=1440]',  # 1440
    '6': 'bestvideo[vcodec^=vp9]+bestaudio[ext=webm]/best', # Mejor calidad

    's1': 'bestvideo[height<=854][vcodec^=avc1]+bestaudio[ext=m4a]/best[height<=854][vcodec^=avc1]',   # 480p (solo avc1)
    's2': 'bestvideo[height<=1080][vcodec^=avc1]+bestaudio[ext=m4a]/best[height<=1080][vcodec^=avc1]''bestvideo[height=1080][vcodec^=vp9]+bestaudio[ext=m4a]',    # # 480p plus (usar vp9 o av01 si existe, fallback a avc1)
    's3': 'bestvideo[height<=1280][vcodec^=avc1]+bestaudio[ext=m4a]/best[height<=1280][vcodec^=avc1]',    # 720 hp (usa avc1)
    's4': 'bestvideo[height<=1920][vcodec^=avc1]+bestaudio[ext=m4a]/best[height<=1920][vcodec^=avc1]/''bestvideo[height<=1920][vcodec^=vp9]+bestaudio[ext=m4a]',   # 1080 (solo vp9 o avc1)
    's5': 'bestvideo[height<=2560][vcodec^=vp9]+bestaudio[ext=m4a]/best[height<=2560][vcodec^=vp9]',    # 1440 (solo avc1 o vp9)
    's6': 'bestvideo'    # 4k (solo avc1 o vp9)
}

#funcion de descarga
def download_video(video_url, quality_option):
    try:
        quality = QUALITY_OPTIONS.get(quality_option, QUALITY_OPTIONS['3'])  # Por defecto 720p
        audio_only = quality_option == '0'
        # Opciones comunes
        ydl_opts = {
            'user_agent': user_agent,
            'http_headers': {'User-Agent': user_agent, 'Accept-Language': 'en-US,en;q=0.9'},
            'noplaylist': False, # para descargar listas completas, cambiar a valor true
            'extractor_args': {'youtube': {'player-client': ['web']}},
            'nocheckcertificate': True,  # evita problemas de SSL
            'geo_bypass': True,          # evita bloqueos por región
            'force_generic_extractor': True, # Esto hace que yt-dlp evite usar algunos clientes como safari/web.
            'format': quality,
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'writethumbnail': True,
        }

        if audio_only:   # Solo audio en mp3
            ydl_opts.update({
                'postprocessors': [
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}, # 1. Convertir a MP3 de alta calidad
                # {'key': 'FFmpegThumbnailsConvertor', 'format': 'png'}, #formato de la miniatura
                {'key': 'FFmpegMetadata', 'add_metadata': True}, # 2. Escribir metadatos
                {'key': 'EmbedThumbnail', 'already_have_thumbnail': False}, # 3. Insertar miniatura como portada
                ],
            })
        else:
            # Video + audio
            ydl_opts.update({
                'cookiefile': 'cookies.json', #eliminar en casos de erores de calidades y formatos o no tener la calidad deseada
                'prefer_ffmpeg': True,
                'postprocessor_args': {
                'ThumbnailsConvertor': ['-f', '-s']
                },
                'postprocessors': [
                {'key': 'FFmpegMetadata', 'add_metadata': True}, # 2. Escribir metadatos
                {'key': 'EmbedThumbnail', 'already_have_thumbnail': False}, # 3. Insertar miniatura como portada
                ],
                'merge_output_format': 'mp4', # no borra, se encarga de cambiar la extension a mp4 siempre
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)
            # Ajustar extensión según el tipo
            if audio_only:
                base_path = os.path.splitext(file_path)[0]
                file_path = f"{base_path}.mp3"
            else:
                base_path = os.path.splitext(file_path)[0]
                file_path = f"{base_path}.mp4"
            # Registrar acceso
            with lock:
                last_access_times[file_path] = time.time()

            return file_path

    except yt_dlp.utils.DownloadError as e:
        return {"error": f"Download error: {str(e)}"}
    except yt_dlp.utils.ExtractorError as e:
        return {"error": f"Extractor error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

# Función para archivos específicos con verificación adicional
def cleanup_files():
    """Versión avanzada con múltiples métodos de detección y configuración."""
    CHECK_INTERVAL = 10  # Segundos entre verificaciones
    MAX_ATTEMPTS = 3    # Intentos antes de considerar el archivo como bloqueado
    time.sleep(16)  # Espera 16 segundos
    file_attempt_count = {}
    
    while True:
        time.sleep(CHECK_INTERVAL)
        
        with lock:
            files_to_check = list(last_access_times.keys())
        
        # Si no hay archivos que verificar, terminar la función
        if not files_to_check:
            print("No hay más archivos que verificar. Finalizando cleanup.")
            break
        
        for file in files_to_check:
            try:
                if not os.path.exists(file):
                    with lock:
                        if file in last_access_times:
                            del last_access_times[file]
                    if file in file_attempt_count:
                        del file_attempt_count[file]
                    continue
                
                # Verificar múltiples indicadores de uso
                file_free = True
                # Verificación 1: Intentar renombrar (muy efectivo)
                temp_name = file + ".tmp_check"

                try:
                    os.rename(file, temp_name)
                    os.rename(temp_name, file)  # Restaurar nombre
                except OSError:
                    file_free = False
                
                # Si el archivo parece libre, intentar eliminarlo
                if file_free:
                    try:
                        os.remove(file)
                        print(f"Archivo eliminado automáticamente: {file}")
                        with lock:
                            if file in last_access_times:
                                del last_access_times[file]
                                
                        if file in file_attempt_count:
                            del file_attempt_count[file]
                            
                    except Exception as e:
                        print(f"Error al eliminar {file}: {e}")
                        # Incrementar contador de intentos fallidos
                        file_attempt_count[file] = file_attempt_count.get(file, 0) + 1
                        # Si ha fallado muchas veces, remover del tracking
                        if file_attempt_count[file] >= MAX_ATTEMPTS:
                            print(f"Archivo {file} removido del tracking tras {MAX_ATTEMPTS} intentos fallidos")
                            with lock:
                                if file in last_access_times:
                                    del last_access_times[file]
                            del file_attempt_count[file]
                            
            except Exception as e:
                print(f"Error procesando archivo {file}: {e}")
    
# funcion de limpieza
def clean_filename(filename):
    # filename = emoji.replace_emoji(filename, replace=" ")  
    filename = re.sub(r'[#&+:;,/\\*?<>|"]', ' ', filename)  # Reemplazar caracteres especiales no deseados por espacios,
    return re.sub(r'\s+', ' ', filename).strip() # Eliminar espacios repetidos y recortar

# app build
@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/download_video', methods=['POST'])
def download_video_route():
    video_url = request.form.get('video_url')
    quality_option = request.form.get('quality', '3')  # Por defecto HD (720p) = 4

    if not video_url:
        return jsonify({"error": "No se proporcionó una URL"}), 400
    
    # Descargar el video o audio en un hilo separado
    file_path = download_video(video_url, quality_option)
    # Verificar si hay un mensaje de error
    if isinstance(file_path, dict) and "error" in file_path:
        return jsonify(file_path), 500
    if not os.path.exists(file_path):
        return jsonify({"error": f"Error al descargar: {file_path}"}), 500
    
    # Esperar hasta que el archivo realmente exista y tenga contenido
    max_wait_time = 80  # Segundos máximo de espera
    start_time = time.time()

    while not os.path.isfile(file_path) or os.path.getsize(file_path) == 0:
        time.sleep(1)

        if time.time() - start_time > max_wait_time:
            return jsonify({"error": "La descarga tardó demasiado en completarse"}), 500

    # Validar si el archivo se generó correctamente antes de continuar
    if os.path.isfile(file_path) and os.path.getsize(file_path) > 0:
        filename = os.path.basename(file_path)
        clean_name = clean_filename(filename)  # Aplicar limpieza
        # Renombrar el archivo con el nuevo nombre limpio
        new_file_path = os.path.join(os.path.dirname(file_path), clean_name)
        # Si el archivo ya existe, no sobrescribas (evita conflictos)
        if os.path.exists(new_file_path) and new_file_path != file_path:
            # Agrega un número aleatorio para hacerlo único
            import random
            # clean_name = f"{base_name} {random.randint(1000, 9999)}{expected_ext}"
            new_file_path = os.path.join(os.path.dirname(file_path), clean_name)
        # Al final, renombra el archivo
        if file_path != new_file_path:
            os.rename(file_path, new_file_path)
        # URL segura para usar en el navegador (codifica los espacios y caracteres especiales)
        safe_filename = urllib.parse.quote(clean_name)
        file_url = f"/Url_Ready/{safe_filename}"
        # Registrar el acceso al archivo
        with lock:
            last_access_times[new_file_path] = time.time()
            
        return jsonify({"downloadUrl": file_url})
    return jsonify({"error": f"Error al descargar: {file_path}"}), 500

# Nueva ruta para servir archivos descargados
@app.route('/Url_Ready/<path:filename>', methods=['GET'])
def serve_file(filename):
    # Decodificar el nombre del archivo para manejar caracteres especiales en la URL
    decoded_filename = urllib.parse.unquote(filename)
    # Actualizar el tiempo de último acceso
    full_path = os.path.join(app.config['DOWNLOAD_FOLDER'], decoded_filename)
    if os.path.exists(full_path):
        with lock:
            last_access_times[full_path] = time.time()
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], decoded_filename, as_attachment=True, conditional=True)

@app.route("/ping", methods=["GET"])
def handle_ping():
    print("\033[38;2;10;101;97mPing recibido. Ejecutando limpieza...\033[0m")
    cleanup_thread = threading.Thread(target=cleanup_files, daemon=True)
    cleanup_thread.start()
    return jsonify({"message": "Cleanup ejecutado"}), 200

# para pruebas locales en desarrollo
# if __name__ == '__main__':
#     app.run(host="0.0.0.0", port=5012, threaded=True, debug=True, use_reloader=True)
# if __name__ == '__main__':
#     app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5012)), threaded=True, debug=True, use_reloader=True)
