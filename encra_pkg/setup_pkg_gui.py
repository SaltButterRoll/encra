import os
import sys
import subprocess
from pathlib import Path

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

if not getattr(sys, 'frozen', False):
    if sys.prefix == sys.base_prefix:
        if not os.path.exists(VENV_DIR):
            subprocess.check_call([sys.executable, '-m', 'venv', VENV_DIR])
        pip_path = os.path.join(VENV_DIR, 'Scripts', 'pip.exe') if os.name == 'nt' else os.path.join(VENV_DIR, 'bin', 'pip')
        subprocess.check_call([pip_path, 'install', 'customtkinter', 'pyinstaller'])
        os.execv(PYTHON_EXE, [PYTHON_EXE, __file__])

import secrets
import threading
import webbrowser
import customtkinter as ctk
from tkinter import messagebox

FONT_DIR = resource_path('font')
PRETENDARD_PATH = os.path.join(FONT_DIR, 'Pretendard-Regular.ttf')
def get_font(size=15, weight='normal'):
    return ctk.CTkFont(family=PRETENDARD_PATH, size=size, weight=weight)

PRIMARY_COLOR = '#4a90e2'  # 연한 파랑
BTN_BG = '#e3f2fd'         # 버튼 연한 파랑
BTN_BORDER = '#4a90e2'     # 버튼 테두리
BTN_ACTIVE_BG = '#1976d2'  # 진한 파랑
BTN_TEXT = '#222'          # 버튼 텍스트
BG_COLOR = '#ffffff'
LOG_BG = '#f2f2f2'
LOG_BORDER = '#b3d1fa'
TEXT_COLOR = '#000000'
LOG_SUCCESS_BG = '#d2f7d2'

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

class SetupGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('encra 키 관리 서버설정')
        self.geometry('500x600')
        self.configure(fg_color=BG_COLOR)
        self.resizable(False, False)

        # 타이틀 + ? 버튼
        title_frame = ctk.CTkFrame(self, fg_color=BG_COLOR, corner_radius=0)
        title_frame.pack(pady=(18, 2), fill='x', padx=0)
        title_label = ctk.CTkLabel(title_frame, text='encra 키 관리 서버설정', font=get_font(22, 'bold'), text_color=PRIMARY_COLOR)
        title_label.pack(padx=(10,0))

        desc_label = ctk.CTkLabel(self, text='인증 메일을 발송하기 위해 Gmail 인증정보를 입력 후 실행해주세요.', font=get_font(12), text_color=TEXT_COLOR, fg_color=BG_COLOR)
        desc_label.pack(pady=(18, 2), anchor='w', fill='x')
        tip_desc = ctk.CTkLabel(self, text='※ 도커가 설치되어있고 도커 엔진이 실행중이어야 합니다.', font=get_font(12), text_color='#888', fg_color=BG_COLOR)
        tip_desc.pack(fill='x', padx=18, pady=(0,4))
        ctk.CTkFrame(self, height=1, fg_color=LOG_BORDER, corner_radius=0).pack(fill='x', padx=18, pady=(0, 10))

        # 입력 폼
        form = ctk.CTkFrame(self, fg_color=BG_COLOR, corner_radius=0)
        form.pack(fill='x', padx=18)
        ctk.CTkLabel(form, text='Gmail 주소', anchor='w', font=get_font(15, 'bold'), text_color=TEXT_COLOR, fg_color=BG_COLOR).pack(fill='x', pady=(0,2))
        self.email_entry = ctk.CTkEntry(form, font=get_font(15), fg_color='white', text_color=TEXT_COLOR, border_color=BTN_BORDER, border_width=1, corner_radius=6)
        self.email_entry.pack(fill='x')
        ctk.CTkLabel(form, text='앱 비밀번호', anchor='w', font=get_font(15, 'bold'), text_color=TEXT_COLOR, fg_color=BG_COLOR).pack(fill='x', pady=(12,2))
        self.pass_entry = ctk.CTkEntry(form, show='*', font=get_font(15), fg_color='white', text_color=TEXT_COLOR, border_color=BTN_BORDER, border_width=1, corner_radius=6)
        self.pass_entry.pack(fill='x')
        link = ctk.CTkLabel(form, text='앱 비밀번호 발급 방법', text_color=PRIMARY_COLOR, font=ctk.CTkFont(size=13, family=PRETENDARD_PATH, underline=True), fg_color=BG_COLOR, cursor='hand2')
        link.pack(anchor='w', pady=(2, 0))
        link.bind('<Button-1>', lambda e: webbrowser.open_new('https://support.google.com/accounts/answer/185833'))

        # 버튼
        btn_frame = ctk.CTkFrame(self, fg_color=BG_COLOR, corner_radius=0)
        btn_frame.pack(fill='x', padx=18, pady=(18,0))
        self.docker_btn = ctk.CTkButton(btn_frame, text='도커 빌드/실행', command=self.on_docker_click, font=get_font(14, 'bold'),
            fg_color=BTN_BG, text_color=BTN_TEXT, hover_color=BTN_ACTIVE_BG, border_color=None, border_width=0, corner_radius=8)
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

    def on_docker_click(self):
        email = self.email_entry.get().strip()
        pw = self.pass_entry.get().strip()
        if not email or not pw:
            messagebox.showwarning('입력 오류', 'Gmail 주소와 앱 비밀번호를 모두 입력하세요.')
            return
        secret_key = secrets.token_hex(24)
        try:
            with open(ENV_PATH, 'w', encoding='utf-8') as f:
                f.write(f"MAIL_USERNAME={email}\n")
                f.write(f"MAIL_PASSWORD={pw}\n")
                f.write(f"SECRET_KEY={secret_key}\n")
        except Exception as e:
            messagebox.showwarning('저장 실패', f'.env 파일 생성 실패: {e}')
            return
        self.docker_btn.configure(state='disabled')
        self.status_label.configure(text='빌드/실행 중', fg_color=PRIMARY_COLOR, text_color='#fff')
        self.log_text.configure(state='normal', fg_color=LOG_BG)
        self.log_text.delete('1.0', 'end')
        self.log_text.insert('end', '[도커 빌드/실행 시작]\n')
        self.log_text.configure(state='disabled')
        threading.Thread(target=self._docker_thread, daemon=True).start()

    def _docker_thread(self):
        def log(msg):
            self.log_text.configure(state='normal')
            self.log_text.insert('end', msg)
            self.log_text.see('end')
            self.log_text.after(10, lambda: self.log_text.see('end'))
            self.log_text.configure(state='disabled')
        cmds = [
            'docker-compose build',
            'docker-compose up -d'
        ]
        for cmd in cmds:
            log(f'\n$ {cmd}\n')
            try:
                process = subprocess.Popen(cmd, shell=True, cwd=SETTING_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
                for line in iter(process.stdout.readline, ''):
                    log(line)
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
        self.docker_btn.configure(state='normal')

if __name__ == '__main__':
    app = SetupGUI()
    app.mainloop()

# venv\Scripts\pyinstaller.exe --noconsole --add-data "setting;setting" --add-data "font;font" --hidden-import=customtkinter setup_pkg_gui.py