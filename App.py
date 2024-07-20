import os
import re
from flask import Flask, request, jsonify, send_file, render_template_string
import yt_dlp as youtube_dl

app = Flask(__name__)

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', filename).strip()

def create_output_dir(output_dir):
    output_dir_path = os.path.join(os.path.abspath('.'), output_dir)
    os.makedirs(output_dir_path, exist_ok=True)
    return output_dir_path

@app.route('/')
def index():
    with open('index.html', 'r', encoding='utf-8') as file:
        return render_template_string(file.read())

@app.route('/get_info', methods=['POST'])
def get_info():
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'URL não fornecida.'}), 400

    ydl_opts = {'format': 'bestaudio/best', 'quiet': True}

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

    try:
        output_dir_path = create_output_dir('downloads')
        ydl_opts = {
            'format': quality,
            'outtmpl': os.path.join(output_dir_path, '%(title)s.%(ext)s')
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_name = sanitize_filename(f"{info_dict['title']}.{info_dict['ext']}")
            file_path = os.path.join(output_dir_path, file_name)

        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'Arquivo não encontrado.'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
