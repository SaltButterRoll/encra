import os
from dotenv import load_dotenv

# .env 파일 자동 로딩
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../.env'))

# IBE 시스템 설정
PKG_SERVER_URL = os.getenv('PKG_SERVER_URL')  # PKG 서버 주소
CLIENT_APP_URL = os.getenv('CLIENT_APP_URL')   # 클라이언트 앱 주소 (외부 접근용)

# API 엔드포인트
AUTH_REQUEST_URL = f'{PKG_SERVER_URL}/auth/request'
AUTH_CONFIRM_URL = f'{PKG_SERVER_URL}/auth/confirm'  # PKG 서버에서 처리
GENERATE_KEY_URL = f'{PKG_SERVER_URL}/auth/generate-key'

# 토큰 관련 설정
TOKEN_HEADER_KEY = 'Authorization'
TOKEN_HEADER_PREFIX = 'Bearer'

# 클라이언트 ID
CLIENT_ID = 'encra_client'

# 데이터 디렉토리 설정
DATA_DIR = './'

# 디렉토리 상수
USER_KEYS_DIRNAME = 'user_keys'  # 키 저장 디렉토리 이름
UPLOADS_DIRNAME = 'uploads'      # 업로드 디렉토리 이름
KEY_FILE_NAME = 'private.bin'    # 개인키 파일 이름

# 클라이언트별 데이터 디렉토리 구조
CLIENT_DATA_DIR = os.path.join(DATA_DIR, CLIENT_ID)
USER_KEYS_DIR = os.path.join(CLIENT_DATA_DIR, USER_KEYS_DIRNAME)
UPLOAD_DIR = os.path.join(CLIENT_DATA_DIR, UPLOADS_DIRNAME)

# 필요한 디렉토리 생성
for directory in [CLIENT_DATA_DIR, USER_KEYS_DIR, UPLOAD_DIR]:
    os.makedirs(directory, exist_ok=True) 