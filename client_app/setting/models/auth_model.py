import os
import jwt
from typing import Optional, Tuple
import requests
from .constants import (AUTH_REQUEST_URL, 
    AUTH_CONFIRM_URL, GENERATE_KEY_URL, USER_KEYS_DIR,
    TOKEN_HEADER_KEY, TOKEN_HEADER_PREFIX
)
from models.ibe_constants import PAIRING_GROUP
import json

class AuthModel:
    def __init__(self):
        self.group = PAIRING_GROUP
        if not os.path.exists(USER_KEYS_DIR):
            os.makedirs(USER_KEYS_DIR)

    def request_email_auth(self, email: str) -> Tuple[bool, str]:
        """이메일 인증 요청을 PKG 서버에 전송"""
        try:
            headers = {'Content-Type': 'application/json'}
            client_app_url = os.getenv('CLIENT_APP_URL')
            payload = {'email': email, 'client_app_url': client_app_url}
            response = requests.post(AUTH_REQUEST_URL, json=payload, headers=headers)
            if response.status_code == 200:
                return True, "인증 메일이 발송되었습니다. 이메일을 확인해주세요."
            return False, response.json().get('error', '인증 요청 실패')
        except requests.RequestException as e:
            return False, f"서버 연결 오류: {str(e)}"

    def confirm_email_auth(self, token: str) -> Tuple[bool, str, Optional[str]]:
        """이메일 인증 확인 및 JWT 토큰 수신"""
        try:
            response = requests.get(f"{AUTH_CONFIRM_URL}/{token}")
            if response.status_code == 200:
                data = response.json()
                return True, "이메일 인증이 완료되었습니다.", data.get('token')
            return False, response.json().get('error', '인증 확인 실패'), None
        except requests.RequestException as e:
            return False, f"서버 연결 오류: {str(e)}", None

    def request_private_key(self, jwt_token: str) -> Tuple[bool, str]:
        """개인키 발급 요청"""
        try:
            headers = {
                TOKEN_HEADER_KEY: f"{TOKEN_HEADER_PREFIX} {jwt_token}",
                'Content-Type': 'application/json'
            }
            response = requests.post(GENERATE_KEY_URL, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                private_key = bytes.fromhex(data['private_key'])
                g = bytes.fromhex(data['g'])
                g_alpha = bytes.fromhex(data['g^alpha'])
                
                # JWT 토큰을 디코드하여 이메일 추출
                token_payload = jwt.decode(jwt_token, options={"verify_signature": False})
                email = token_payload['email']
                
                # 이메일 정보를 JSON으로 저장
                email_path = os.path.join(USER_KEYS_DIR, 'user_info.json')
                with open(email_path, 'w') as f:
                    json.dump({'email': email}, f)
                
                # 개인키를 바이너리 파일로 저장
                key_path = os.path.join(USER_KEYS_DIR, 'private.bin')
                with open(key_path, 'wb') as f:
                    f.write(private_key)
                
                # g 값을 ibe_constants.py에 저장
                ibe_constants_path = os.path.join(os.path.dirname(__file__), 'ibe_constants.py')
                with open(ibe_constants_path, 'r') as f:
                    lines = f.readlines()
                
                # PUBLIC_PARAMS 딕셔너리 업데이트
                for i, line in enumerate(lines):
                    if 'PUBLIC_PARAMS = {' in line:
                        lines[i+1] = f'    "g": "{g.hex()}",\n'
                        lines[i+2] = f'    "g^alpha": "{g_alpha.hex()}"\n'
                        lines[i+3] = '}\n'
                        break
                
                with open(ibe_constants_path, 'w') as f:
                    f.writelines(lines)
                    
                return True, "개인키가 발급되었습니다."
            return False, response.json().get('error', '개인키 발급 실패')
        except Exception as e:
            return False, f"개인키 발급 중 오류: {str(e)}"

    def get_current_user_email(self) -> Optional[str]:
        """현재 저장된 사용자 이메일 가져오기"""
        try:
            info_path = os.path.join(USER_KEYS_DIR, 'user_info.json')
            if os.path.exists(info_path):
                with open(info_path, 'r') as f:
                    data = json.load(f)
                    return data['email']
            return None
        except Exception:
            return None

    def load_private_key(self) -> Optional[bytes]:
        """저장된 개인키 로드"""
        try:
            key_path = os.path.join(USER_KEYS_DIR, 'private.bin')
            if not os.path.exists(key_path):
                return None
                
            with open(key_path, 'rb') as f:
                return f.read()
        except Exception:
            return None 