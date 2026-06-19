from flask import Flask, request, jsonify, send_file, render_template_string
import yt_dlp
import os
import tempfile
import threading
import uuid
import requests
import logging
import urllib.parse
import re
import time
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
tasks = {}

import os
COBALT_INSTANCES = [
    os.environ.get('COBALT_URL', 'https://cobalt-api-production-69b7.up.railway.app'),
]

HTML = '''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>📥 Video Downloader</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #141820; color: #e0e6f0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    min-height: 100vh; padding: 16px;
  }
  .header { text-align: center; padding: 24px 0 20px; }
  .logo { font-size: 2.5rem; margin-bottom: 6px; }
  .header h1 { font-size: 1.4rem; font-weight: 700; color: #4db8ff; }
  .header p { font-size: 0.8rem; color: #6a7a90; margin-top: 4px; }
  .card { background: #1e2533; border-radius: 16px; padding: 20px; margin-bottom: 16px; border: 1px solid #2a3448; }
  .card-title { font-size: 0.75rem; font-weight: 600; color: #4db8ff; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }
  textarea {
    width: 100%; background: #0f1520; border: 1.5px solid #2a3448;
    border-radius: 12px; color: #e0e6f0; padding: 14px; font-size: 0.95rem;
    resize: none; height: 90px; outline: none; transition: border-color 0.2s;
  }
  textarea:focus { border-color: #4db8ff; }
  textarea::placeholder { color: #3a4a60; }
  .format-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; }
  .format-group label { display: block; font-size: 0.75rem; color: #6a7a90; margin-bottom: 6px; font-weight: 500; }
  select {
    width: 100%; background: #0f1520; border: 1.5px solid #2a3448;
    border-radius: 10px; color: #e0e6f0; padding: 10px 12px; font-size: 0.9rem;
    outline: none; appearance: none; -webkit-appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236a7a90' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
    background-repeat: no-repeat; background-position: right 12px center;
  }
  select:focus { border-color: #4db8ff; }
  .btn { width: 100%; padding: 15px; border-radius: 12px; border: none; font-size: 1rem; font-weight: 600; cursor: pointer; transition: all 0.2s; margin-top: 4px; }
  .btn-primary { background: linear-gradient(135deg, #1a7fd4, #0f5fa8); color: #fff; }
  .btn-primary:active { transform: scale(0.98); }
  .btn-primary:disabled { background: #2a3448; color: #4a5a70; cursor: not-allowed; }
  .btn-secondary { background: #0f5fa8; color: #fff; display: none; margin-top: 10px; }
  .status-box { background: #0f1520; border-radius: 12px; padding: 14px; margin-top: 12px; display: none; border: 1px solid #2a3448; }
  .status-text { font-size: 0.85rem; color: #8aa0bf; line-height: 1.6; }
  .progress-bar { width: 100%; height: 6px; background: #2a3448; border-radius: 3px; margin-top: 10px; overflow: hidden; }
  .progress-fill { height: 100%; background: linear-gradient(90deg, #1a7fd4, #4db8ff); border-radius: 3px; width: 0%; transition: width 0.3s; }
  .badge { display: inline-block; padding: 3px 8px; border-radius: 6px; font-size: 0.7rem; font-weight: 600; margin-right: 4px; margin-bottom: 4px; }
  .badge-blue { background: #1a3a5c; color: #4db8ff; }
  .badge-green { background: #1a3a2a; color: #4dffaa; }
  .badge-yellow { background: #3a2a0a; color: #ffd04d; }
  .sites-grid { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
  .error { color: #ff6b6b; }
  .success { color: #4dffaa; }
  .spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #2a3448; border-top-color: #4db8ff; border-radius: 50%; animation: spin 0.8s linear infinite; vertical-align: middle; margin-right: 6px; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .ping-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #4dffaa; margin-right: 5px; animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
  .footer { text-align: center; padding: 20px 0 8px; font-size: 0.75rem; color: #3a4a60; }
  .keepalive { text-align: center; font-size: 0.7rem; color: #3a5a40; padding-bottom: 16px; }
  .cobalt-badge { display: inline-block; background: #1a2a3a; border: 1px solid #2a4a6a; border-radius: 6px; padding: 2px 7px; font-size: 0.7rem; color: #4db8ff; margin-left: 6px; vertical-align: middle; }
</style>
</head>
<body>
<div class="header">
  <div class="logo">📥</div>
  <h1>Video Downloader</h1>
  <p>1000+ сайтов • YouTube • TikTok • SoundCloud и другие</p>
</div>
<div class="card">
  <div class="card-title">🔗 Ссылка на видео</div>
  <textarea id="urlInput" placeholder="Вставьте ссылку сюда&#10;Например: https://youtube.com/watch?v=...&#10;или https://soundcloud.com/..."></textarea>
</div>
<div class="card">
  <div class="card-title">⚙️ Формат</div>
  <div class="format-row">
    <div class="format-group">
      <label>Тип</label>
      <select id="typeSelect" onchange="updateFormats()">
        <option value="video">🎬 Видео</option>
        <option value="audio">🎵 Аудио</option>
      </select>
    </div>
    <div class="format-group">
      <label>Качество</label>
      <select id="qualitySelect">
        <option value="bestvideo+bestaudio/best">Лучшее</option>
        <option value="bestvideo[height<=1080]+bestaudio/best[height<=1080]">1080p</option>
        <option value="bestvideo[height<=720]+bestaudio/best[height<=720]">720p</option>
        <option value="bestvideo[height<=480]+bestaudio/best[height<=480]">480p</option>
        <option value="bestvideo[height<=360]+bestaudio/best[height<=360]">360p</option>
      </select>
    </div>
  </div>
  <div class="format-group">
    <label>Формат файла</label>
    <select id="formatSelect">
      <option value="mp4">MP4</option>
      <option value="mkv">MKV</option>
    </select>
  </div>
</div>
<button class="btn btn-primary" id="downloadBtn" onclick="startDownload()">⬇️ Скачать</button>
<div class="status-box" id="statusBox">
  <div class="status-text" id="statusText">Подготовка...</div>
  <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
</div>
<button class="btn btn-secondary" id="fileBtn" onclick="downloadFile()">💾 Сохранить файл</button>
<div class="card" style="margin-top:16px">
  <div class="card-title">📋 Поддерживаемые сайты</div>
  <div class="sites-grid">
    <span class="badge badge-blue">YouTube <span class="cobalt-badge">via cobalt</span></span>
    <span class="badge badge-green">TikTok</span>
    <span class="badge badge-green">Instagram</span>
    <span class="badge badge-green">Twitter/X</span>
    <span class="badge badge-green">Facebook</span>
    <span class="badge badge-green">Vimeo</span>
    <span class="badge badge-green">SoundCloud</span>
    <span class="badge badge-green">Bandcamp</span>
    <span class="badge badge-yellow">Reddit</span>
    <span class="badge badge-yellow">Twitch</span>
    <span class="badge badge-yellow">и 990+ других</span>
  </div>
</div>
<div class="footer">Работает на yt-dlp + cobalt • Только для личного использования</div>
<div class="keepalive"><span class="ping-dot"></span>Сервер активен</div>
<script>
let currentTaskId = null;
let pollInterval = null;
let downloadUrl = null;
setInterval(() => { fetch('/ping').catch(() => {}); }, 4 * 60 * 1000);
function updateFormats() {
  const type = document.getElementById('typeSelect').value;
  const qualitySelect = document.getElementById('qualitySelect');
  const formatSelect = document.getElementById('formatSelect');
  if (type === 'audio') {
    qualitySelect.innerHTML = `
      <option value="bestaudio">Лучшее</option>
      <option value="bestaudio[abr<=320]">~320 kbps</option>
      <option value="bestaudio[abr<=192]">~192 kbps</option>
      <option value="bestaudio[abr<=128]">~128 kbps</option>`;
    formatSelect.innerHTML = `
      <option value="mp3">MP3</option>
      <option value="m4a">M4A</option>
      <option value="opus">OPUS</option>`;
  } else {
    qualitySelect.innerHTML = `
      <option value="bestvideo+bestaudio/best">Лучшее</option>
      <option value="bestvideo[height<=1080]+bestaudio/best[height<=1080]">1080p</option>
      <option value="bestvideo[height<=720]+bestaudio/best[height<=720]">720p</option>
      <option value="bestvideo[height<=480]+bestaudio/best[height<=480]">480p</option>
      <option value="bestvideo[height<=360]+bestaudio/best[height<=360]">360p</option>`;
    formatSelect.innerHTML = `
      <option value="mp4">MP4</option>
      <option value="mkv">MKV</option>`;
  }
}
async function startDownload() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) { alert('Вставьте ссылку!'); return; }
  const type = document.getElementById('typeSelect').value;
  const quality = document.getElementById('qualitySelect').value;
  const format = document.getElementById('formatSelect').value;
  const btn = document.getElementById('downloadBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Подготовка...';
  document.getElementById('fileBtn').style.display = 'none';
  document.getElementById('statusBox').style.display = 'block';
  document.getElementById('statusText').textContent = 'Запрос отправлен...';
  document.getElementById('progressFill').style.width = '5%';
  try {
    const resp = await fetch('/download', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url, type, quality, format})
    });
    const data = await resp.json();
    if (data.task_id) { currentTaskId = data.task_id; pollStatus(); }
    else { showError(data.error || 'Неизвестная ошибка'); }
  } catch(e) { showError('Ошибка соединения: ' + e.message); }
}
function pollStatus() {
  pollInterval = setInterval(async () => {
    try {
      const resp = await fetch('/status/' + currentTaskId);
      const data = await resp.json();
      const statusEl = document.getElementById('statusText');
      const progressEl = document.getElementById('progressFill');
      if (data.status === 'pending') {
        statusEl.innerHTML = '<span class="spinner"></span>Ожидание...';
        progressEl.style.width = '8%';
      } else if (data.status === 'downloading') {
        const pct = data.progress || 10;
        progressEl.style.width = pct + '%';
        statusEl.innerHTML = '<span class="spinner"></span>Скачивание... ' + pct + '%';
        document.getElementById('downloadBtn').innerHTML = '<span class="spinner"></span>' + pct + '%';
      } else if (data.status === 'processing') {
        progressEl.style.width = '95%';
        statusEl.innerHTML = '<span class="spinner"></span>Обработка файла...';
      } else if (data.status === 'done') {
        clearInterval(pollInterval);
        progressEl.style.width = '100%';
        statusEl.innerHTML = '<span class="success">✅ Готово! Нажмите кнопку ниже чтобы сохранить файл.</span>';
        downloadUrl = '/file/' + currentTaskId;
        document.getElementById('fileBtn').style.display = 'block';
        const btn = document.getElementById('downloadBtn');
        btn.disabled = false;
        btn.innerHTML = '⬇️ Скачать ещё';
      } else if (data.status === 'error') {
        clearInterval(pollInterval);
        showError(data.error || 'Ошибка при скачивании');
      }
    } catch(e) {}
  }, 1500);
}
function downloadFile() { if (downloadUrl) window.location.href = downloadUrl; }
function showError(msg) {
  clearInterval(pollInterval);
  document.getElementById('statusText').innerHTML = '<span class="error">❌ ' + msg + '</span>';
  document.getElementById('progressFill').style.width = '0%';
  const btn = document.getElementById('downloadBtn');
  btn.disabled = false;
  btn.innerHTML = '⬇️ Попробовать снова';
}
</script>
</body>
</html>'''


@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/ping')
def ping():
    return jsonify({'status': 'alive'})

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url', '').strip()
    dl_type = data.get('type', 'video')
    quality = data.get('quality', 'bestvideo+bestaudio/best')
    fmt = data.get('format', 'mp4')
    if not url:
        return jsonify({'error': 'URL не указан'}), 400
    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'pending', 'progress': 0, 'file': None, 'error': None}
    thread = threading.Thread(target=run_download, args=(task_id, url, dl_type, quality, fmt))
    thread.daemon = True
    thread.start()
    return jsonify({'task_id': task_id})

@app.route('/status/<task_id>')
def status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'status': 'error', 'error': 'Задача не найдена'}), 404
    return jsonify({
        'status': task['status'],
        'progress': round(task.get('progress', 0)),
        'error': task.get('error')
    })

@app.route('/file/<task_id>')
def get_file(task_id):
    task = tasks.get(task_id)
    if not task or task['status'] != 'done' or not task['file']:
        return 'Файл не найден', 404
    filepath = task['file']
    filename = os.path.basename(filepath)
    return send_file(filepath, as_attachment=True, download_name=filename)


def is_youtube(url):
    return 'youtube.com' in url or 'youtu.be' in url

def cobalt_quality(quality_str):
    for q in ['2160', '1440', '1080', '720', '480', '360', '240', '144']:
        if q in quality_str:
            return q
    return 'max'

def safe_filename(name):
    name = name.replace('／', '_').replace('＼', '_')
    name = re.sub(r'[\\/*?:"<>|]', '_', name)
    name = re.sub(r'[\x00-\x1f\x7f]', '', name)
    name = name.strip().strip('.')
    return name[:180] or 'video'


def try_cobalt_instance(instance_url, payload):
    try:
        resp = requests.post(
            instance_url + '/',
            json=payload,
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            timeout=30
        )
        logger.info(f"[cobalt] {instance_url} → HTTP {resp.status_code}: {resp.text[:200]}")
        if resp.status_code != 200:
            return None
        data = resp.json()
        status = data.get('status')
        if status == 'error':
            logger.warning(f"[cobalt] ошибка: {data.get('error', {})}")
            return None
        file_url = None
        filename = 'video'
        if status in ('redirect', 'tunnel'):
            file_url = data.get('url')
            filename = data.get('filename', 'video')
        elif status == 'picker':
            picker = data.get('picker', [])
            if picker:
                file_url = picker[0].get('url')
                filename = data.get('filename', 'video')
        if file_url:
            return (file_url, filename)
        return None
    except Exception as e:
        logger.warning(f"[cobalt] {instance_url} → исключение: {e}")
        return None


def fetch_and_save(file_url, out_path, task_id, start_progress=20):
    dl_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Referer': 'https://cobalt.tools/',
        'Accept': '*/*',
        'Accept-Encoding': 'identity',
        'Connection': 'keep-alive',
    }
    with requests.get(file_url, stream=True, timeout=(10, 300), headers=dl_headers) as r:
        logger.info(f"[cobalt] Скачивание → HTTP {r.status_code}")
        logger.info(f"[cobalt] Content-Length: {r.headers.get('Content-Length', 'нет')}")
        logger.info(f"[cobalt] Content-Type: {r.headers.get('Content-Type', 'нет')}")
        if r.status_code != 200:
            return 0, r.headers
        total = int(r.headers.get('Content-Length', 0))
        downloaded = 0
        with open(out_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=131072):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = start_progress + int((downloaded / total) * (98 - start_progress))
                        tasks[task_id]['progress'] = min(pct, 98)
                    else:
                        tasks[task_id]['progress'] = min(
                            tasks[task_id].get('progress', start_progress) + 1, 98
                        )
        return downloaded, r.headers


def download_via_cobalt(task_id, url, dl_type, quality, fmt):
    tmp_dir = tempfile.mkdtemp()
    try:
        tasks[task_id]['status'] = 'downloading'
        tasks[task_id]['progress'] = 5

        payload = {
            'url': url,
            'downloadMode': 'audio' if dl_type == 'audio' else 'auto',
            'videoQuality': cobalt_quality(quality),
            'audioFormat': (fmt if fmt in ['mp3', 'ogg', 'wav', 'opus'] else 'mp3') if dl_type == 'audio' else 'best',
            'filenameStyle': 'pretty',
        }

        ext = (fmt if fmt in ['mp3', 'm4a', 'opus'] else 'mp3') if dl_type == 'audio' else 'mp4'
        valid_exts = ['mp4', 'mkv', 'mp3', 'm4a', 'opus', 'webm', 'ogg']

        for instance in COBALT_INSTANCES:
            logger.info(f"[cobalt] Пробуем: {instance}")
            result = try_cobalt_instance(instance, payload)
            if not result:
                continue

            file_url, raw_filename = result
            # Переключаемся на внутренний адрес для скачивания туннеля
            file_url = file_url.replace(
                'https://cobalt-api-production-69b7.up.railway.app',
                'http://cobalt-api.railway.internal:9000'
            )
            logger.info(f"[cobalt] Туннель URL: {file_url[:80]}")
            tasks[task_id]['progress'] = 15

            filename = safe_filename(raw_filename or 'video')
            if not any(filename.lower().endswith(f'.{e}') for e in valid_exts):
                base = os.path.splitext(filename)[0] if '.' in filename else filename
                filename = f'{base}.{ext}'

            out_path = os.path.join(tmp_dir, filename)
            logger.info(f"[cobalt] Файл: [{filename}]")

            try:
                downloaded, resp_headers = fetch_and_save(file_url, out_path, task_id)
            except Exception as e:
                logger.warning(f"[cobalt] ошибка скачивания: {e}")
                downloaded = 0
                resp_headers = {}

            logger.info(f"[cobalt] записано {downloaded} байт")

            if downloaded > 0:
                content_disp = resp_headers.get('Content-Disposition', '')
                better_name = None
                if "filename*=UTF-8''" in content_disp:
                    encoded = content_disp.split("filename*=UTF-8''")[-1].split(';')[0].strip().strip('"\'')
                    try:
                        better_name = urllib.parse.unquote(encoded)
                    except Exception:
                        pass
                if not better_name and 'filename=' in content_disp:
                    part = content_disp.split('filename=')[-1].split(';')[0].strip().strip('"\'')
                    if not part.upper().startswith('UTF-8') and part:
                        better_name = part
                if better_name:
                    better_name = safe_filename(better_name)
                    if not any(better_name.lower().endswith(f'.{e}') for e in valid_exts):
                        base = os.path.splitext(better_name)[0] if '.' in better_name else better_name
                        better_name = f'{base}.{ext}'
                    new_path = os.path.join(tmp_dir, better_name)
                    if new_path != out_path:
                        try:
                            os.rename(out_path, new_path)
                            out_path = new_path
                        except Exception:
                            pass

                tasks[task_id]['file'] = out_path
                tasks[task_id]['status'] = 'done'
                tasks[task_id]['progress'] = 100
                logger.info(f"[cobalt] Успех!")
                return True

            try:
                os.remove(out_path)
            except Exception:
                pass

        logger.warning("[cobalt] Не удалось скачать")
        return False

    except Exception as e:
        logger.error(f"[cobalt] Исключение: {e}", exc_info=True)
        return False


def download_via_ytdlp(task_id, url, dl_type, quality, fmt):
    tmp_dir = tempfile.mkdtemp()
    output_path = os.path.join(tmp_dir, '%(title)s.%(ext)s')

    def progress_hook(d):
        if d['status'] == 'downloading':
            pct_str = d.get('_percent_str', '0%').strip().replace('%', '')
            try:
                tasks[task_id]['progress'] = float(pct_str)
                tasks[task_id]['status'] = 'downloading'
            except Exception:
                pass
        elif d['status'] == 'finished':
            tasks[task_id]['progress'] = 99
            tasks[task_id]['status'] = 'processing'

    ydl_opts = {
        'outtmpl': output_path,
        'progress_hooks': [progress_hook],
        'noplaylist': True,
        'nocheckcertificate': True,
        'retries': 5,
        'fragment_retries': 5,
        'socket_timeout': 30,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        },
    }

    if dl_type == 'audio':
        audio_fmt = fmt if fmt in ['mp3', 'm4a', 'opus'] else 'mp3'
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['writethumbnail'] = True
        ydl_opts['postprocessors'] = [
            {'key': 'FFmpegExtractAudio', 'preferredcodec': audio_fmt, 'preferredquality': '192'},
            {'key': 'EmbedThumbnail'},
            {'key': 'FFmpegMetadata', 'add_metadata': True},
        ]
    else:
        ydl_opts['format'] = quality
        ydl_opts['merge_output_format'] = fmt

    try:
        tasks[task_id]['status'] = 'downloading'
        tasks[task_id]['progress'] = 5
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        media_extensions = {'.mp4', '.mkv', '.mp3', '.m4a', '.opus', '.webm', '.ogg', '.flac'}
        found_file = None
        for f in os.listdir(tmp_dir):
            if os.path.splitext(f)[1].lower() in media_extensions:
                found_file = os.path.join(tmp_dir, f)
                break

        if found_file:
            tasks[task_id]['file'] = found_file
            tasks[task_id]['status'] = 'done'
            tasks[task_id]['progress'] = 100
        else:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['error'] = 'Файл не найден после скачивания'
    except Exception as e:
        tasks[task_id]['status'] = 'error'
        tasks[task_id]['error'] = str(e)[:300]


def run_download(task_id, url, dl_type, quality, fmt):
    if is_youtube(url):
        logger.info("[run] YouTube — cobalt")
        success = download_via_cobalt(task_id, url, dl_type, quality, fmt)
        if not success:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['error'] = 'Не удалось скачать. Попробуйте позже или другое видео.'
        return

    download_via_ytdlp(task_id, url, dl_type, quality, fmt)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
