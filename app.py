from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context
import yt_dlp
import os
import tempfile
import threading
import uuid
import requests
import logging
import re
import urllib.parse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
tasks = {}

COBALT_INSTANCES = [
    'https://cobalt-api-production-69b7.up.railway.app',
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
  .btn-green { background: linear-gradient(135deg, #1a9a4a, #0f7a35); color: #fff; display: none; margin-top: 10px; }
  .status-box { background: #0f1520; border-radius: 12px; padding: 14px; margin-top: 12px; display: none; border: 1px solid #2a3448; }
  .status-text { font-size: 0.85rem; color: #8aa0bf; line-height: 1.6; }
  .progress-bar { width: 100%; height: 6px; background: #2a3448; border-radius: 3px; margin-top: 10px; overflow: hidden; }
  .progress-fill { height: 100%; background: linear-gradient(90deg, #1a7fd4, #4db8ff); border-radius: 3px; width: 0%; transition: width 0.4s; }
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
  .cobalt-badge { display: inline-block; background: #1a2a3a; border: 1px solid #2a4a6a; border-radius: 6px; padding: 2px 7px; font-size: 0.7rem; color: #4db8ff; margin-left: 4px; }
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
<button class="btn btn-green" id="saveBtn" onclick="saveFile()">💾 Сохранить файл</button>
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

// Пользователь нажимает кнопку — браузер идёт на /stream/ который стримит файл напрямую
function saveFile() {
  if (currentTaskId) {
    window.location.href = '/stream/' + currentTaskId;
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
  document.getElementById('saveBtn').style.display = 'none';
  document.getElementById('statusBox').style.display = 'block';
  document.getElementById('statusText').innerHTML = '<span class="spinner"></span>Запрос отправлен...';
  document.getElementById('progressFill').style.width = '10%';

  try {
    const resp = await fetch('/download', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url, type, quality, format})
    });
    const data = await resp.json();
    if (data.task_id) {
      currentTaskId = data.task_id;
      pollStatus();
    } else {
      showError(data.error || 'Неизвестная ошибка');
    }
  } catch(e) {
    showError('Ошибка соединения: ' + e.message);
  }
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
        progressEl.style.width = '15%';
      } else if (data.status === 'downloading') {
        const pct = data.progress || 20;
        progressEl.style.width = pct + '%';
        statusEl.innerHTML = '<span class="spinner"></span>Скачивание... ' + pct + '%';
        document.getElementById('downloadBtn').innerHTML = '<span class="spinner"></span>' + pct + '%';
      } else if (data.status === 'processing') {
        progressEl.style.width = '90%';
        statusEl.innerHTML = '<span class="spinner"></span>Обработка...';
      } else if (data.status === 'done') {
        clearInterval(pollInterval);
        progressEl.style.width = '100%';
        statusEl.innerHTML = '<span class="success">✅ Готово! Нажмите кнопку ниже.</span>';
        const btn = document.getElementById('downloadBtn');
        btn.disabled = false;
        btn.innerHTML = '⬇️ Скачать ещё';
        document.getElementById('saveBtn').style.display = 'block';
      } else if (data.status === 'error') {
        clearInterval(pollInterval);
        showError(data.error || 'Ошибка при скачивании');
      }
    } catch(e) {}
  }, 1500);
}

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
    tasks[task_id] = {
        'status': 'pending', 'progress': 0,
        'file': None, 'error': None,
        'cobalt_url': None, 'cobalt_filename': None,
        'is_youtube': False,
    }
    thread = threading.Thread(target=run_download, args=(task_id, url, dl_type, quality, fmt))
    thread.daemon = True
    thread.start()
    return jsonify({'task_id': task_id})

def is_youtube(url):
    return 'youtube.com' in url or 'youtu.be' in url

def cobalt_quality(quality_str):
    if '2160' in quality_str: return '2160'
    if '1440' in quality_str: return '1440'
    if '1080' in quality_str: return '1080'
    if '720' in quality_str: return '720'
    if '480' in quality_str: return '480'
    if '360' in quality_str: return '360'
    return 'max'

def safe_filename(name):
    name = name.replace('／', '_').replace('＼', '_')
    name = re.sub(r'[\\/*?:"<>|]', '_', name)
    name = re.sub(r'[\x00-\x1f\x7f]', '', name)
    return (name.strip().strip('.')[:180]) or 'video'

def try_cobalt_instance(instance_url, payload):
    try:
        resp = requests.post(
            instance_url + '/',
            json=payload,
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
            timeout=20
        )
        logger.info(f"[cobalt] {instance_url} → HTTP {resp.status_code}: {resp.text[:300]}")
        if resp.status_code != 200:
            return None
        data = resp.json()
        status = data.get('status')
        if status == 'error':
            return None
        file_url, filename = None, 'video'
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
        logger.warning(f"[cobalt] {instance_url} → ошибка: {e}")
        return None

def download_via_cobalt(task_id, url, dl_type, quality, fmt):
    """Получаем URL от cobalt и сохраняем — стриминг к пользователю по кнопке."""
    try:
        tasks[task_id]['status'] = 'downloading'
        tasks[task_id]['progress'] = 40
        tasks[task_id]['is_youtube'] = True

        payload = {
            'url': url,
            'downloadMode': 'audio' if dl_type == 'audio' else 'auto',
            'videoQuality': cobalt_quality(quality),
            'audioFormat': fmt if dl_type == 'audio' and fmt in ['mp3', 'ogg', 'wav', 'opus'] else 'mp3' if dl_type == 'audio' else 'best',
            'filenameStyle': 'pretty',
        }

        result = None
        for instance in COBALT_INSTANCES:
            logger.info(f"[cobalt] Пробуем: {instance}")
            result = try_cobalt_instance(instance, payload)
            if result:
                break

        if not result:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['error'] = 'Cobalt не ответил. Попробуйте позже.'
            return

        file_url, raw_filename = result
        filename = safe_filename(raw_filename)
        logger.info(f"[cobalt] URL получен, файл: {filename}")

        # Сохраняем URL — /stream/ запросит его заново когда пользователь нажмёт кнопку
        # Но URL одноразовый! Поэтому запрашиваем новый URL прямо в /stream/
        # Здесь сохраняем payload чтобы /stream/ мог повторить запрос к cobalt
        tasks[task_id]['cobalt_payload'] = payload
        tasks[task_id]['cobalt_filename'] = filename
        tasks[task_id]['cobalt_instance'] = COBALT_INSTANCES[0]
        tasks[task_id]['progress'] = 100
        tasks[task_id]['status'] = 'done'

    except Exception as e:
        logger.error(f"[cobalt] Исключение: {e}", exc_info=True)
        tasks[task_id]['status'] = 'error'
        tasks[task_id]['error'] = str(e)[:300]

def run_download(task_id, url, dl_type, quality, fmt):
    if is_youtube(url):
        download_via_cobalt(task_id, url, dl_type, quality, fmt)
        return

    tmp_dir = tempfile.mkdtemp()
    output_path = os.path.join(tmp_dir, '%(title)s.%(ext)s')

    def progress_hook(d):
        if d['status'] == 'downloading':
            pct_str = d.get('_percent_str', '0%').strip().replace('%', '')
            try:
                tasks[task_id]['progress'] = float(pct_str)
                tasks[task_id]['status'] = 'downloading'
            except:
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

@app.route('/status/<task_id>')
def status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'status': 'error', 'error': 'Задача не найдена'}), 404
    return jsonify({
        'status': task['status'],
        'progress': round(task.get('progress', 0)),
        'error': task.get('error'),
    })

@app.route('/stream/<task_id>')
def stream_file(task_id):
    """
    Для YouTube: запрашивает СВЕЖИЙ URL у cobalt прямо сейчас и стримит файл.
    Для остальных: отдаёт сохранённый файл.
    Вызывается когда пользователь нажимает кнопку — URL всегда свежий.
    """
    task = tasks.get(task_id)
    if not task or task['status'] != 'done':
        return 'Задача не найдена', 404

    # Не-YouTube: отдаём файл с диска
    if not task.get('is_youtube'):
        from flask import send_file
        if not task.get('file'):
            return 'Файл не найден', 404
        return send_file(task['file'], as_attachment=True,
                         download_name=os.path.basename(task['file']))

    # YouTube: запрашиваем НОВЫЙ свежий URL у cobalt прямо сейчас
    payload = task.get('cobalt_payload')
    filename = task.get('cobalt_filename', 'video.mp4')
    instance = task.get('cobalt_instance', COBALT_INSTANCES[0])

    if not payload:
        return 'Данные задачи потеряны', 404

    logger.info(f"[stream] Запрашиваем свежий URL у cobalt для стриминга...")
    result = try_cobalt_instance(instance, payload)

    if not result:
        return 'Не удалось получить ссылку от cobalt. Попробуйте скачать заново.', 502

    fresh_url, _ = result
    logger.info(f"[stream] Свежий URL получен, начинаем стриминг: {fresh_url[:60]}...")

    # Определяем Content-Type
    ext = os.path.splitext(filename)[1].lower()
    content_type_map = {
        '.mp4': 'video/mp4', '.mkv': 'video/x-matroska',
        '.mp3': 'audio/mpeg', '.m4a': 'audio/mp4',
        '.opus': 'audio/ogg', '.webm': 'video/webm',
    }
    content_type = content_type_map.get(ext, 'application/octet-stream')

    # Стримим файл от cobalt напрямую пользователю
    cobalt_resp = requests.get(
        fresh_url,
        stream=True,
        timeout=300,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
    )

    if cobalt_resp.status_code != 200:
        return f'Cobalt вернул ошибку: {cobalt_resp.status_code}', 502

    safe_name = urllib.parse.quote(filename)

    def generate():
        for chunk in cobalt_resp.iter_content(chunk_size=65536):
            if chunk:
                yield chunk

    headers = {
        'Content-Disposition': f"attachment; filename*=UTF-8''{safe_name}",
        'Content-Type': content_type,
        'X-Accel-Buffering': 'no',
    }
    # Передаём Content-Length если cobalt его знает
    if 'Content-Length' in cobalt_resp.headers:
        headers['Content-Length'] = cobalt_resp.headers['Content-Length']

    return Response(
        stream_with_context(generate()),
        headers=headers,
        status=200
    )

@app.route('/file/<task_id>')
def get_file(task_id):
    from flask import send_file
    task = tasks.get(task_id)
    if not task or task['status'] != 'done' or not task.get('file'):
        return 'Файл не найден', 404
    return send_file(task['file'], as_attachment=True,
                     download_name=os.path.basename(task['file']))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
