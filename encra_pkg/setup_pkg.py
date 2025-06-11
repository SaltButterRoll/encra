import os
import secrets
import sys
import subprocess
import threading
import webbrowser


# --- setting 폴더 기준 경로 ---
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
SETTING_DIR = os.path.join(CUR_DIR, 'setting')
VENV_DIR = os.path.join(SETTING_DIR, 'venv')
REQUIREMENTS_PATH = os.path.join(SETTING_DIR, 'requirements.txt')
ENV_PATH = os.path.join(SETTING_DIR, '.env')
DOCKER_COMPOSE_PATH = os.path.join(SETTING_DIR, 'docker-compose.yml')
# venv가 없으면 생성 및 패키지 설치 후, 가상환경에서 setup_client.py 재실행
if sys.prefix == sys.base_prefix:
    if not os.path.exists(VENV_DIR):
        # 가상환경(venv) 생성 중
        subprocess.check_call([sys.executable, '-m', 'venv', VENV_DIR])
    
    pip_path = os.path.join(VENV_DIR, 'Scripts', 'pip.exe')
    python_path = os.path.join(VENV_DIR, 'Scripts', 'python.exe')

    # pip, setuptools, wheel 업그레이드 (python -m pip 방식으로)
    # pip, setuptools, wheel 업그레이드 중
    try:
        subprocess.check_call([
            python_path, '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel'
        ])
    except subprocess.CalledProcessError as e:
        # pip 업그레이드 실패
        sys.exit(1)


    # 필수 패키지 설치 중 (flask 등)
    try:
        subprocess.check_call([
            pip_path, 'install', 'flask==3.0.3'
        ])
    except subprocess.CalledProcessError as e:
        # 패키지 설치 실패
        sys.exit(1)

    # 가상환경에서 스크립트 재실행
    # 가상환경에서 setup_pkg.py 재실행
    try:
        os.execv(python_path, [python_path, __file__])
    except Exception as e:
        # 재실행 실패
        sys.exit(1)


from flask import Flask, render_template, request, flash, redirect, url_for, Response, jsonify # 위치 고정

app = Flask(__name__, template_folder=os.path.join(SETTING_DIR, 'templates'))
app.secret_key = 'setup-wizard-secret-key'

def read_env():
    env = {}
    if not os.path.exists(ENV_PATH):
        return env
    try:
        with open(ENV_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line:
                    k, v = line.strip().split('=', 1)
                    env[k] = v
    except Exception:
        pass
    return env

def stream_docker_logs(cmd):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=SETTING_DIR, encoding='utf-8', errors='replace')
    for line in iter(process.stdout.readline, ''):
        yield f'data: {line.rstrip()}' + '\n\n'
    process.stdout.close()
    process.wait()

def docker_compose_build_and_up_sse():
    build_cmd = 'docker-compose build --no-cache'
    up_cmd = 'docker-compose up -d'
    for log in stream_docker_logs(build_cmd):
        yield log
    for log in stream_docker_logs(up_cmd):
        yield log
    yield 'data: [DONE]\n\n'  # SSE 종료 신호

def docker_compose_up_sse():
    check_cmd = 'docker ps -f name=encra_pkg --format "{{.Names}}"'
    result = subprocess.run(check_cmd, shell=True, stdout=subprocess.PIPE, text=True)
    if 'encra_pkg' in result.stdout:
        yield 'data: 컨테이너는 이미 실행 중입니다.\n\n'
        yield 'data: [DONE]\n\n'
        return
    up_cmd = 'docker-compose up -d'
    for log in stream_docker_logs(up_cmd):
        yield log
    yield 'data: [DONE]\n\n'

@app.route('/run_docker_logs')
def run_docker_logs():
    type_ = request.args.get('type')
    if type_ == 'buildup':
        return Response(docker_compose_build_and_up_sse(), mimetype='text/event-stream')
    elif type_ == 'up':
        return Response(docker_compose_up_sse(), mimetype='text/event-stream')
    else:
        return Response('data: Invalid type\n\n', mimetype='text/event-stream')

@app.route('/', methods=['GET', 'POST'])
def setup():
    env_exists = os.path.exists(ENV_PATH)
    env = read_env() if env_exists else {}
    if request.method == 'POST':
        mail_user = request.form.get('MAIL_USERNAME', '').strip()
        mail_pass = request.form.get('MAIL_PASSWORD', '').strip()
        secret_key = secrets.token_hex(24)
        if not (mail_user and mail_pass and secret_key):
            return jsonify({'status': 'fail', 'message': '모든 항목을 입력해 주세요.'})
        try:
            with open(ENV_PATH, 'w', encoding='utf-8') as f:
                f.write(f"MAIL_USERNAME={mail_user}\n")
                f.write(f"MAIL_PASSWORD={mail_pass}\n")
                f.write(f"SECRET_KEY={secret_key}\n")
        except Exception as e:
            return jsonify({'status': 'fail', 'message': f'.env 파일 생성 실패: {e}'})
        return jsonify({'status': 'ok', 'message': '.env 파일이 생성(수정)되었습니다.'})
    return render_template('setting.html', env=env, env_exists=env_exists)

@app.route('/run_container', methods=['POST'])
def run_container():
    ok, msg = docker_compose_up_sse()
    flash(msg, 'success' if ok else 'error')
    return redirect(url_for('setup'))

@app.route('/reset', methods=['GET', 'POST'])
def reset():
    env = read_env()
    return render_template('setting.html', env=env)

def open_browser():
    webbrowser.open_new('http://127.0.0.1:7996/')

if __name__ == '__main__':
    threading.Timer(1.0, open_browser).start()
    app.run(host='127.0.0.1', port=7996, debug=False)