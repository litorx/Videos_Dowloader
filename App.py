import os
import re
from flask import Flask, render_template, request, send_file, jsonify, Response
import yt_dlp as youtube_dl

app = Flask(__name__)

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', filename).strip()

def create_output_dir(output_dir):
    base_path = os.path.abspath('.')
    output_dir_path = os.path.join(base_path, output_dir)
    os.makedirs(output_dir_path, exist_ok=True)
    return output_dir_path

def download_video(url, quality='best', output_dir='downloads'):
    output_dir_path = create_output_dir(output_dir)

    ydl_opts = {
        'format': quality,
        'outtmpl': os.path.join(output_dir_path, '%(title)s.%(ext)s'),
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_name = sanitize_filename(f"{info_dict['title']}.{info_dict['ext']}")
            file_path = os.path.join(output_dir_path, file_name)

        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return "File not found", 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_info', methods=['POST'])
def get_info():
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'URL não fornecida.'}), 400

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
    }

    return get_video_info(url, ydl_opts)

def get_video_info(url, ydl_opts):
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])
            all_formats = extract_formats(formats)

            if not all_formats:
                return jsonify({'error': 'Nenhuma qualidade de vídeo disponível.'}), 404

            return jsonify({'formats': list(all_formats.values())})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def extract_formats(formats):
    all_formats = {}
    for f in formats:
        resolution = f.get('resolution')
        format_id = f.get('format_id')
        if resolution:
            all_formats[resolution] = {
                'format_id': format_id,
                'resolution': resolution,
                'ext': f.get('ext')
            }
        elif f.get('acodec') and f['acodec'] != 'none':
            all_formats[format_id] = {
                'format_id': format_id,
                'resolution': 'Áudio',
                'ext': f.get('ext')
            }
    return all_formats

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    quality = request.form.get('quality')
    if not url or not quality:
        return jsonify({'error': 'URL ou qualidade não fornecida.'}), 400

    response = download_video(url, quality)
    if isinstance(response, Response):
        return response
    else:
        return jsonify({'error': 'Erro ao processar o download.'}), 500

if __name__ == '__main__':
    app.run(debug=True)
