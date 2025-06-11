import os
import sys
import subprocess
from pathlib import Path

# pyinstaller 리소스 경로 처리
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
SETTING_DIR = resource_path('setting')
ENV_PATH = os.path.join(SETTING_DIR, '.env')
DOCKER_COMPOSE_PATH = os.path.join(SETTING_DIR, 'docker-compose.yml')
VENV_DIR = os.path.join(CUR_DIR, 'venv')
PYTHON_EXE = os.path.join(VENV_DIR, 'Scripts', 'python.exe') if os.name == 'nt' else os.path.join(VENV_DIR, 'bin', 'python')

# 가상환경 설정
if not getattr(sys, 'frozen', False):
    if sys.prefix == sys.base_prefix:
        if not os.path.exists(VENV_DIR):
            # 가상환경(venv) 생성 중
            subprocess.check_call([sys.executable, '-m', 'venv', VENV_DIR])
        pip_path = os.path.join(VENV_DIR, 'Scripts', 'pip.exe') if os.name == 'nt' else os.path.join(VENV_DIR, 'bin', 'pip')
        # 패키지 설치 중
        subprocess.check_call([pip_path, 'install', 'customtkinter', 'requests', 'pyinstaller'])
        # 가상환경에서 setup_client_gui.py 재실행
        os.execv(PYTHON_EXE, [PYTHON_EXE, __file__])

# 가상환경 설정 후 필요한 패키지 import
import secrets
import threading
import time
import webbrowser
import socket
import requests
import customtkinter as ctk
from tkinter import messagebox

PRIMARY_COLOR = '#4a90e2'
BTN_BG = '#e3f2fd'
BTN_BORDER = '#4a90e2'
BTN_ACTIVE_BG = '#1976d2'
BTN_TEXT = '#222'
BG_COLOR = '#ffffff'
LOG_BG = '#f2f2f2'
LOG_BORDER = '#b3d1fa'
TEXT_COLOR = '#000000'
LOG_SUCCESS_BG = '#d2f7d2'

FONT_DIR = resource_path('font')
PRETENDARD_PATH = os.path.join(FONT_DIR, 'Pretendard-Regular.ttf')
def get_font(size=15, weight='normal'):
    return ctk.CTkFont(family=PRETENDARD_PATH, size=size, weight=weight)

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind('<Enter>', self.show_tip)
        widget.bind('<Leave>', self.hide_tip)
    def show_tip(self, event=None):
        if self.tipwindow:
            return
        x = self.widget.winfo_rootx() + 40
        y = self.widget.winfo_rooty() + 30
        self.tipwindow = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(tw, text=self.text, justify='left', fg_color="#f7fbff", corner_radius=6, text_color='#222', font=get_font(12))
        label.pack(ipadx=8, ipady=4)
    def hide_tip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

def is_port_available(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', int(port)))
        return True
    except OSError:
        return False

class SetupClientGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('encra 클라이언트 환경설정')
        self.geometry('500x600')
        self.configure(fg_color=BG_COLOR)
        self.resizable(False, False)

        # 타이틀 + ? 버튼
        title_frame = ctk.CTkFrame(self, fg_color=BG_COLOR, corner_radius=0)
        title_frame.pack(pady=(18, 2), fill='x', padx=0)
        title_label = ctk.CTkLabel(title_frame, text='encra 클라이언트 환경설정', font=get_font(22, 'bold'), text_color=PRIMARY_COLOR)
        title_label.pack(padx=(10,0))
        desc_label = ctk.CTkLabel(self, text='앱을 실행할 포트번호와 키관리 서버 주소를 입력하세요.', font=get_font(15), text_color=TEXT_COLOR, fg_color=BG_COLOR)
        desc_label.pack(pady=(18, 2), anchor='w', fill='x')
        tip_desc = ctk.CTkLabel(self, text='※ 도커가 설치되어있고 도커 엔진이 실행중이어야 합니다.', font=get_font(12), text_color='#888', fg_color=BG_COLOR)
        tip_desc.pack(fill='x', padx=18, pady=(0,4))
        ctk.CTkFrame(self, height=1, fg_color=LOG_BORDER, corner_radius=0).pack(fill='x', padx=18, pady=(0, 10))

        # 입력 폼
        form = ctk.CTkFrame(self, fg_color=BG_COLOR, corner_radius=0)
        form.pack(fill='x', padx=18)
        ctk.CTkLabel(form, text='포트번호', anchor='w', font=get_font(15, 'bold'), text_color=TEXT_COLOR, fg_color=BG_COLOR).pack(fill='x', pady=(0,2))
        self.port_entry = ctk.CTkEntry(form, font=get_font(15), fg_color='white', text_color=TEXT_COLOR, border_color=BTN_BORDER, border_width=1, corner_radius=6)
        self.port_entry.insert(0, '61624')
        self.port_entry.pack(fill='x')
        ctk.CTkLabel(form, text='PKG 서버 URL', anchor='w', font=get_font(15, 'bold'), text_color=TEXT_COLOR, fg_color=BG_COLOR).pack(fill='x', pady=(12,2))
        self.pkg_url_type = ctk.StringVar(value='local')
        radio_frame = ctk.CTkFrame(form, fg_color=BG_COLOR, corner_radius=0)
        radio_frame.pack(fill='x', pady=(0,2))
        local_radio = ctk.CTkRadioButton(radio_frame, text='로컬', variable=self.pkg_url_type, value='local', font=get_font(13), fg_color=PRIMARY_COLOR, border_color=BTN_BORDER, hover_color=BTN_ACTIVE_BG, command=self.on_radio_change)
        local_radio.pack(side='left', padx=(0,10))
        external_radio = ctk.CTkRadioButton(radio_frame, text='외부', variable=self.pkg_url_type, value='external', font=get_font(13), fg_color=PRIMARY_COLOR, border_color=BTN_BORDER, hover_color=BTN_ACTIVE_BG, command=self.on_radio_change)
        external_radio.pack(side='left')
        self.pkg_url_entry = ctk.CTkEntry(form, font=get_font(13), fg_color='white', text_color=TEXT_COLOR, border_color=BTN_BORDER, border_width=1, corner_radius=6)
        self.pkg_url_entry.insert(0, 'http://encra_pkg:6543')
        self.pkg_url_entry.pack(fill='x', pady=(2,0))

        # 버튼
        btn_frame = ctk.CTkFrame(self, fg_color=BG_COLOR, corner_radius=0)
        btn_frame.pack(fill='x', padx=18, pady=(18,0))
        self.docker_btn = ctk.CTkButton(btn_frame, text='도커 빌드/실행', command=self.on_docker_click, font=get_font(14, 'bold'),
            fg_color=BTN_BG, text_color=BTN_TEXT, hover_color=BTN_ACTIVE_BG, border_width=0, border_color=None, corner_radius=8)
        self.docker_btn.pack(side='left', expand=True, fill='x')
        # 상태 표시 라벨과 도커 빌드/실행 버튼 사이 여백
        ctk.CTkFrame(self, height=16, fg_color=BG_COLOR).pack(fill='x')
        # 상태 표시 라벨 (버튼 느낌, 항상 표시)
        self.status_label = ctk.CTkLabel(
            self,
            text='대기 중',
            fg_color='#cccccc',
            text_color='#888',
            font=get_font(14, 'bold'),
            corner_radius=8,
            height=36,
            anchor='center'
        )
        self.status_label.pack(fill='x', padx=18, pady=(0, 10))
        self.open_btn = ctk.CTkButton(self, text='클라이언트 바로가기', state='disabled', fg_color='#cccccc', text_color='#888', hover_color='#cccccc', font=get_font(14, 'bold'), corner_radius=8, command=self.open_client)
        self.open_btn.pack(fill='x', padx=18, pady=(10,0))

        # 도커 로그 구분선
        ctk.CTkFrame(self, height=1, fg_color=LOG_BORDER, corner_radius=0).pack(fill='x', padx=18, pady=(22, 2))

        # 로그 안내
        log_guide = ctk.CTkLabel(self, text='도커 로그 (빌드/실행 과정의 모든 메시지 실시간 표시)', font=get_font(13), text_color=TEXT_COLOR, fg_color=BG_COLOR)
        log_guide.pack(fill='x', padx=18, pady=(0,2))
        log_desc = ctk.CTkLabel(self, text='※ 도커 빌드에는 몇 분 정도 시간이 소요될 수 있습니다.', font=get_font(13), text_color='#888', fg_color=BG_COLOR)
        log_desc.pack(fill='x', padx=18, pady=(0,4))

        # 로그 출력
        self.log_text = ctk.CTkTextbox(self, height=180, font=get_font(12), fg_color=LOG_BG, text_color=TEXT_COLOR, border_width=0, corner_radius=6)
        self.log_text.pack(fill='both', padx=18, pady=(0,18), expand=True)
        self.log_text.configure(state='disabled')

    def on_radio_change(self):
        if self.pkg_url_type.get() == 'local':
            self.pkg_url_entry.configure(state='normal')
            current_value = self.pkg_url_entry.get().strip()
            if not current_value or not current_value.startswith('http://encra_pkg'):
                self.pkg_url_entry.delete(0, 'end')
                self.pkg_url_entry.insert(0, 'http://encra_pkg:6543')
        else:
            self.pkg_url_entry.configure(state='normal')
            self.pkg_url_entry.delete(0, 'end')

    def on_docker_click(self):
        port = self.port_entry.get().strip()
        pkg_url_type = self.pkg_url_type.get()
        pkg_server_url = self.pkg_url_entry.get().strip() if pkg_url_type == 'external' else 'http://encra_pkg:6543'
        # 포트 유효성 검사
        if not port.isdigit() or not (2000 <= int(port) <= 65535):
            messagebox.showwarning('입력 오류', '유효한 포트 번호를 입력해 주세요. (2000~65535)')
            return
        if not is_port_available(port):
            messagebox.showwarning('입력 오류', f'포트 {port}는 이미 사용 중입니다. 다른 포트를 입력해 주세요.')
            return
        secret_key = secrets.token_hex(24)
        client_app_url = f'http://localhost:{port}'
        try:
            with open(ENV_PATH, 'w', encoding='utf-8') as f:
                f.write(f"PORT={port}\n")
                f.write(f"PKG_SERVER_URL={pkg_server_url}\n")
                f.write(f"SECRET_KEY={secret_key}\n")
                f.write(f"CLIENT_APP_URL={client_app_url}\n")
        except Exception as e:
            messagebox.showwarning('저장 실패', f'.env 파일 생성 실패: {e}')
            return
        self.docker_btn.configure(state='disabled')
        self.status_label.configure(text='빌드/실행 중', fg_color=PRIMARY_COLOR, text_color='#fff')
        self.log_text.configure(state='normal', fg_color=LOG_BG)
        self.log_text.delete('1.0', 'end')
        self.log_text.insert('end', '[도커 빌드/실행 시작]\n')
        self.log_text.configure(state='disabled')
        threading.Thread(target=self._docker_thread, args=(port,), daemon=True).start()

    def _docker_thread(self, port):
        def log(msg):
            self.log_text.configure(state='normal')
            self.log_text.insert('end', msg)
            self.log_text.see('end')
            self.log_text.update()
            self.log_text.configure(state='disabled')
        

        
        cmds = [
            'docker-compose build',
            # 'docker-compose build --no-cache', # 빌드 캐시 사용 안함
            'docker-compose up -d'
        ]
        for cmd in cmds:
            log(f'\n$ {cmd}\n')
            try:
                process = subprocess.Popen(cmd, shell=True, cwd=SETTING_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
                for line in iter(process.stdout.readline, ''):
                    log(line)
                    self.log_text.see('end')
                    self.log_text.update()
                process.stdout.close()
                process.wait()
            except Exception as e:
                log(f'\n[오류] {e}\n')
                self.docker_btn.configure(state='normal')
                return
        # 빌드/실행 완료 시각적 표시
        self.log_text.configure(state='normal', fg_color=LOG_SUCCESS_BG)
        self.log_text.insert('end', '\n\n====================\n   ✔ 완료   \n====================\n')
        self.log_text.configure(state='disabled')
        self.status_label.configure(text='완료', fg_color='#7ed957', text_color='#222')
        
        # 클라이언트 서버 연결 테스트
        log('\n[클라이언트 서버 연결 테스트 시작]\n')
        time.sleep(2)
        
        client_ok = False
        
        # 클라이언트 서버 확인
        try:
            client_url = f'http://127.0.0.1:{port}/'
            log(f'[테스트] 클라이언트 서버 연결 확인: {client_url}\n')
            resp = requests.get(client_url, timeout=5)
            if resp.status_code in [200, 401, 403, 405]:
                log(f'[성공] 클라이언트 서버 정상 동작 (응답코드: {resp.status_code})\n')
                client_ok = True
            else:
                log(f'[실패] 클라이언트 서버 응답코드: {resp.status_code}\n')
        except Exception as e:
            log(f'[실패] 클라이언트 서버 연결 실패: {e}\n')
        
        # 최종 결과 판정
        if client_ok:
            log('\n[결과] ✅ 클라이언트 서버가 정상적으로 실행되었습니다!\n')
            self.status_label.configure(text='실행 성공', fg_color='#4bb543', text_color='#fff')
            self.open_btn.configure(state='normal', fg_color=PRIMARY_COLOR, text_color='#fff', hover_color=BTN_ACTIVE_BG)
        else:
            log('\n[결과] ❌ 클라이언트 서버 실행에 실패했습니다.\n')
            self.status_label.configure(text='실행 실패', fg_color='#ffb3b3', text_color='#222')
            self.open_btn.configure(state='disabled', fg_color='#cccccc', text_color='#888', hover_color='#cccccc')
            messagebox.showwarning('실행 실패', '클라이언트 서버가 정상적으로 실행되지 않았습니다.')
        
        self.docker_btn.configure(state='normal')

    def open_client(self):
        port = self.port_entry.get().strip()
        url = f'http://127.0.0.1:{port}/'
        webbrowser.open_new(url)

if __name__ == '__main__':
    app = SetupClientGUI()
    app.mainloop() 
    
# venv\Scripts\pyinstaller.exe --noconsole --add-data "setting;setting" --add-data "font;font" --hidden-import=customtkinter --hidden-import=requests setup_client_gui.py