# ENCRA Client Application

ENCRA 이미지 보안 시스템의 **클라이언트 애플리케이션** (일반 사용자용)입니다. 이미지와 PDF 파일의 특정 영역(ROI)을 선택하여 암호화하고, 이메일 기반 신원 확인을 통해 복호화할 수 있는 웹 애플리케이션입니다.

> **👥 대상 사용자**: 일반 사용자 (관리자로부터 PKG 서버 정보를 받아서 사용)
> 
> **🔧 관리자용 PKG 서버**는 별도로 `encra_pkg` 폴더를 참조하세요.

## 📥 빠른 시작

### 1. 관리자에게 PKG 서버 정보 요청
클라이언트 앱을 사용하기 전에 **시스템 관리자**에게 다음 정보를 받아야 합니다:
- **PKG 서버 URL** (예: `http://192.168.1.100:6543`)
- **서버 포트 번호** (일반적으로 6543)

### 2. 간편 실행
1. **클라이언트 앱 다운로드**: `setup_client_gui_vX.X.X.zip`
2. **압축 해제** 후 `setup_client_gui.exe` 실행
3. **PKG 서버 정보 입력** (관리자에게 받은 정보)
4. **도커 빌드/실행** 버튼 클릭
5. **클라이언트 바로가기** 버튼으로 웹 접속

> **🧪 테스트 목적**: 테스트를 위해 본인이 직접 PKG 서버를 실행하려면 `encra_pkg` 폴더의 README.md를 참조하세요.

## 주요 기능

### 📸 이미지/PDF 암호화
- **ROI 기반 암호화**: 이미지나 PDF의 특정 영역을 드래그하여 선택 후 암호화
- **다중 수신자 지원**: 한 번의 암호화로 여러 명의 수신자에게 전송 가능
- **PDF 품질 조절**: PDF 암호화 시 품질 스케일 조정 가능
- **실시간 미리보기**: 암호화할 영역을 실시간으로 확인

### 🔓 이미지/PDF 복호화
- **개인키 기반 복호화**: 이메일 인증을 통해 발급받은 개인키로 복호화
- **파일 형식 지원**: JPEG, PNG, PDF 등 다양한 형식 지원
- **복호화 검증**: 원본과 복호화된 파일의 차이점 검증

### 🔐 이메일 기반 인증
- **IBE (Identity-Based Encryption)**: 이메일 주소를 ID로 사용하는 암호화 시스템
- **자동 개인키 발급**: 이메일 인증 시 자동으로 개인키 생성 및 저장
- **안전한 키 관리**: 로컬 저장소에 안전하게 개인키 보관

## 시스템 요구사항

### 필수 요구사항
- **Python 3.9+**
- **Docker & Docker Compose**
- **Docker Engine 실행 중** ⚠️ **중요: Docker Desktop이 실행되어 있어야 함**
- **Windows 10/11** (개발 환경 기준)

### 권장 사양
- **RAM**: 8GB 이상
- **디스크 공간**: 3GB 이상 (Docker 이미지 포함)
- **네트워크**: 키 관리 서버와의 통신을 위한 네트워크 연결

## 🚀 설치 및 실행

### ⚠️ 사전 준비사항
1. **Docker Desktop 설치 및 실행** ([다운로드 링크](https://docs.docker.com/desktop/install/windows-install/))
2. **관리자에게 PKG 서버 정보** 요청 (URL 및 포트 번호)

### GUI를 통한 간편 실행
1. **`setup_client_gui.exe` 실행**
2. **PKG 서버 URL** 입력 (관리자에게 받은 정보)
   - 예시: `http://192.168.1.100:6543`
   - 로컬 테스트: `http://localhost:6543`
3. **클라이언트 포트** 설정 (기본값: 61624)
4. **"도커 빌드/실행"** 버튼 클릭
5. 빌드 완료 후 **"클라이언트 바로가기"** 버튼으로 웹 접속

> **💡 참고**: exe 파일 실행 시 Windows Defender 경고가 나타날 수 있습니다. **"추가 정보" → "실행"**을 선택하여 진행하세요.

## 프로젝트 구조

```
client_app/
├── setup_client_gui.py          # GUI 설정 프로그램
├── setup_client_gui.spec        # PyInstaller 빌드 설정
├── font/                        # 프로그램에서 사용하는 폰트
├── setting/                     # Flask 웹 애플리케이션
│   ├── app.py                   # Flask 앱 메인 파일
│   ├── requirements.txt         # Python 의존성
│   ├── Dockerfile              # Docker 빌드 설정
│   ├── docker-compose.yml      # Docker Compose 설정
│   ├── controllers/            # 비즈니스 로직
│   │   ├── auth_controller.py  # 인증 관련 로직
│   │   ├── encrypt_controller.py # 암호화 로직
│   │   └── decrypt_controller.py # 복호화 로직
│   ├── models/                 # 데이터 모델
│   │   └── roi_handler.py      # ROI 처리 로직
│   ├── views/                  # 뷰 컨트롤러
│   │   ├── encryption_view.py  # 암호화 페이지 뷰
│   │   └── decryption_view.py  # 복호화 페이지 뷰
│   ├── templates/              # HTML 템플릿
│   │   ├── layout.html         # 기본 레이아웃
│   │   ├── index.html          # 메인 페이지
│   │   ├── encrypt.html        # 암호화 페이지
│   │   ├── decrypt.html        # 복호화 페이지
│   │   └── auth/               # 인증 관련 템플릿
│   └── static/                 # 정적 파일 (CSS, JS)
├── build/                      # PyInstaller 빌드 폴더
├── dist/                       # 빌드된 실행 파일
└── venv/                       # Python 가상환경
```

## 주요 의존성

```txt
Flask==3.0.3              # 웹 프레임워크
python-dotenv==1.0.1      # 환경 변수 관리
pycryptodome==3.20.0      # 암호화 라이브러리
opencv-python==4.9.0.80   # 이미지 처리
numpy==1.24.4             # 수치 계산
PyMuPDF                   # PDF 처리
Pillow==10.2.0            # 이미지 조작
scikit-image==0.22.0      # 이미지 분석
requests==2.31.0          # HTTP 클라이언트
PyJWT==2.3.0              # JWT 토큰
```

## 사용 방법

### 1. 첫 실행 및 인증
1. 웹 브라우저에서 `http://localhost:61624` 접속
2. **이메일 인증하기** 버튼 클릭
3. 이메일 주소 입력 후 인증 요청
4. 이메일로 받은 인증 링크 클릭
5. 개인키가 자동으로 생성되어 로컬에 저장

### 2. 이미지 암호화
1. **이미지 암호화** 메뉴 선택
2. 이미지 또는 PDF 파일 업로드
3. 암호화할 영역을 마우스로 드래그하여 선택
4. 수신자 이메일 주소 입력 (여러 명 가능)
5. **암호화** 버튼 클릭
6. 암호화된 파일 다운로드

### 3. 이미지 복호화
1. **이미지 복호화** 메뉴 선택
2. 암호화된 파일 업로드
3. **복호화** 버튼 클릭 (개인키가 있어야 함)
4. 복호화된 파일 다운로드

## 문제 해결

### 일반적인 문제

**Q: 포트가 이미 사용 중이라는 오류가 발생합니다.**
A: 다른 포트 번호를 사용하거나, 해당 포트를 사용하는 프로세스를 종료하세요.

**Q: Docker 빌드가 실패합니다.**
A: 다음 순서로 확인해보세요:
   1. **Docker Desktop이 실행 중인지 확인** (시스템 트레이의 Docker 아이콘이 초록색)
   2. `docker version` 명령으로 Docker 엔진 상태 확인
   3. 충분한 디스크 공간이 있는지 확인 (최소 3GB)
   4. Docker Desktop을 재시작해보세요

**Q: "Docker daemon is not running" 오류가 발생합니다.**
A: Docker Desktop이 실행되지 않은 상태입니다. Docker Desktop을 시작하고 완전히 로딩될 때까지 기다린 후 다시 시도하세요.

**Q: 이메일 인증이 안 됩니다.**
A: 키 관리 서버가 실행 중인지 확인하고, PKG_SERVER_URL이 올바른지 확인하세요.

**Q: 복호화가 안 됩니다.**
A: 개인키가 올바르게 생성되었는지 확인하고, 해당 이메일로 암호화된 파일인지 확인하세요.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 기여하기

1. 이 저장소를 포크하세요
2. 새로운 기능 브랜치를 생성하세요 (`git checkout -b feature/new-feature`)
3. 변경사항을 커밋하세요 (`git commit -am 'Add new feature'`)
4. 브랜치에 푸시하세요 (`git push origin feature/new-feature`)
5. Pull Request를 생성하세요

## 문의 및 지원

추가 문의사항이나 기술 지원이 필요한 경우, 프로젝트 이슈 트래커를 활용해 주세요. 