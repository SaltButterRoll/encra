# ENCRA Key Management Server (PKG)

ENCRA 이미지 보안 시스템의 **키 관리 서버** (관리자용)입니다. IBE(Identity-Based Encryption) 기반의 개인키 생성과 이메일 인증 서비스를 제공하는 백엔드 서버 애플리케이션입니다.

> **🔧 대상 사용자**: 시스템 관리자 (PKG 서버 운영 담당자)
> 
> **👤 일반 사용자**는 `client_app` 폴더를 참조하여 클라이언트 앱만 사용하세요.

## 📋 관리자 역할

### 🔧 시스템 관리자의 책임
1. **PKG 서버 운영**: 키 관리 서버 설치, 설정, 운영
2. **Gmail 계정 설정**: 인증 메일 발송을 위한 Gmail 앱 비밀번호 설정
3. **서버 정보 제공**: 일반 사용자에게 PKG 서버 URL과 포트 정보 제공
4. **시스템 보안**: 서버 보안 및 방화벽 설정 관리

### 📤 일반 사용자에게 제공할 정보
PKG 서버 설정 완료 후, 일반 사용자들에게 다음 정보를 제공하세요:
- **PKG 서버 URL**: `http://서버IP주소:6543` (예: `http://192.168.1.100:6543`)
- **서버 포트**: `6543` (기본값)
- **클라이언트 앱 다운로드 링크**: GitHub 릴리즈 페이지

## 📥 빠른 시작 (관리자용)

### 1. Gmail 앱 비밀번호 준비
- [Gmail 앱 비밀번호 설정 가이드](https://support.google.com/accounts/answer/185833) 참조
- 16자리 앱 비밀번호 생성 및 복사

### 2. PKG 서버 실행
1. **PKG 서버 다운로드**: `setup_pkg_gui_vX.X.X.zip`
2. **압축 해제** 후 `setup_pkg_gui.exe` 실행
3. **Gmail 정보 입력** (이메일 주소 및 앱 비밀번호)
4. **도커 빌드/실행** 버튼 클릭
5. 서버가 `http://localhost:6543`에서 실행됨

### 3. 네트워크 설정 (선택사항)
- **방화벽**: 6543 포트 허용
- **내부 네트워크 공유**: `http://내부IP:6543`으로 클라이언트 접근 허용

## 주요 기능

### 🔐 IBE 키 관리
- **마스터 키 생성**: 시스템 전체의 마스터 키 쌍 자동 생성
- **개인키 생성**: 이메일 주소 기반 개인키 생성 및 관리
- **안전한 키 저장**: 생성된 키들을 안전하게 로컬 저장

### 📧 이메일 인증 서비스
- **Gmail SMTP 연동**: Gmail을 통한 인증 메일 발송
- **인증 링크 생성**: 안전한 토큰 기반 인증 링크 제공
- **개인키 자동 발급**: 인증 완료 시 개인키 자동 생성 및 전송

### 🌐 RESTful API
- **인증 요청 처리**: 클라이언트의 이메일 인증 요청 처리
- **키 검증**: 개인키 존재 여부 확인
- **보안 통신**: JWT 토큰 기반 보안 통신

## 시스템 요구사항

### 필수 요구사항
- **Python 3.9+**
- **Docker & Docker Compose**
- **Docker Engine 실행 중** ⚠️ **중요: Docker Desktop이 실행되어 있어야 함**
- **Windows 10/11** (개발 환경 기준)
- **Gmail 계정** (앱 비밀번호 설정 필요)

### 권장 사양
- **RAM**: 4GB 이상
- **디스크 공간**: 2GB 이상 (Docker 이미지 포함)
- **네트워크**: 이메일 발송을 위한 인터넷 연결

## 🚀 설치 및 실행 (관리자용)

### ⚠️ 사전 준비사항
1. **Docker Desktop 설치 및 실행** ([다운로드 링크](https://docs.docker.com/desktop/install/windows-install/))
2. **Gmail 계정 및 앱 비밀번호** 준비 ([설정 가이드](https://support.google.com/accounts/answer/185833))

### GUI를 통한 간편 실행
1. **`setup_pkg_gui.exe` 실행**
2. **Gmail 정보 입력**:
   - Gmail 주소 (인증 메일 발송용)
   - 16자리 앱 비밀번호
3. **"도커 빌드/실행"** 버튼 클릭
4. 서버가 `http://localhost:6543`에서 실행됨

### 일반 사용자에게 안내
PKG 서버 실행 후, 클라이언트 사용자들에게 다음 정보를 제공하세요:
- **PKG 서버 URL**: `http://서버IP:6543`
- **클라이언트 앱 다운로드**: GitHub 릴리즈 페이지 링크

> **💡 참고**: exe 파일 실행 시 Windows Defender 경고가 나타날 수 있습니다. **"추가 정보" → "실행"**을 선택하여 진행하세요.

## 프로젝트 구조

```
encra_pkg/
├── setup_pkg_gui.py            # GUI 설정 프로그램
├── setup_pkg_gui.spec          # PyInstaller 빌드 설정
├── setup_pkg.py                # 콘솔 설정 프로그램
├── font/                       # 프로그램에서 사용하는 폰트
├── setting/                    # Flask 웹 서버
│   ├── app.py                  # Flask 앱 메인 파일
│   ├── requirements.txt        # Python 의존성
│   ├── Dockerfile             # Docker 빌드 설정
│   ├── docker-compose.yml     # Docker Compose 설정
│   ├── controllers/           # API 컨트롤러
│   │   └── auth_controller.py # 인증 관련 API
│   └── models/                # 데이터 모델
│       ├── pkg_model.py       # IBE 키 관리 모델
│       └── email_manager.py   # 이메일 발송 관리
├── build/                     # PyInstaller 빌드 폴더
├── dist/                      # 빌드된 실행 파일
└── venv/                      # Python 가상환경
```

## 주요 의존성

```txt
Flask==3.0.3              # 웹 프레임워크
python-dotenv==1.0.1      # 환경 변수 관리
pycryptodome==3.10.1      # 암호화 라이브러리
cryptography==3.4.7       # 고급 암호화 기능
Flask-Mail==0.9.1         # 이메일 발송
PyJWT==2.3.0              # JWT 토큰
Cython==3.0.12            # C 확장 지원
gmpy2==2.2.1              # 고성능 수학 연산
```

## Gmail 앱 비밀번호 설정

키 관리 서버는 Gmail SMTP를 통해 인증 메일을 발송합니다:

### 1. Gmail 설정
1. **Google 계정 관리** 페이지 접속
2. **보안** → **2단계 인증** 활성화
3. **앱 비밀번호** 생성

### 2. 앱 비밀번호 생성
1. [Google 앱 비밀번호 페이지](https://support.google.com/accounts/answer/185833) 참조
2. **앱 선택** → "메일"
3. **기기 선택** → "Windows 컴퓨터" 또는 "기타"
4. 생성된 **16자리 비밀번호** 복사
5. GUI 프로그램에서 해당 비밀번호 입력

## API 엔드포인트

### 인증 관련 API
```
POST /auth/request_auth
- 이메일 인증 요청
- Body: {"email": "user@example.com"}

GET /auth/verify_token/<token>
- 인증 토큰 검증 및 개인키 생성

POST /auth/check
- 개인키 존재 여부 확인
- Body: {"email": "user@example.com"}
```

## 사용 방법

### 1. 서버 실행
1. GUI 프로그램으로 서버 설정 및 실행
2. 서버가 `http://localhost:6543`에서 실행됨
3. 마스터 키가 `pkg_keys/` 폴더에 자동 생성

### 2. 클라이언트 연동
- 클라이언트 앱에서 PKG 서버 URL을 `http://localhost:6543`으로 설정
- 또는 네트워크 환경에 따라 `http://IP주소:6543` 형태로 설정

### 3. 인증 플로우
1. 클라이언트에서 이메일 인증 요청
2. 서버에서 Gmail로 인증 메일 발송
3. 사용자가 이메일의 인증 링크 클릭
4. 서버에서 개인키 생성 및 클라이언트로 전송

## 문제 해결

### 일반적인 문제

**Q: Gmail 인증이 실패합니다.**
A: Gmail 2단계 인증이 활성화되어 있고, 앱 비밀번호를 올바르게 입력했는지 확인하세요.

**Q: Docker 빌드가 실패합니다.**
A: 다음 순서로 확인해보세요:
   1. **Docker Desktop이 실행 중인지 확인** (시스템 트레이의 Docker 아이콘이 초록색)
   2. `docker version` 명령으로 Docker 엔진 상태 확인
   3. 충분한 디스크 공간이 있는지 확인 (최소 2GB)
   4. Docker Desktop을 재시작해보세요

**Q: "Docker daemon is not running" 오류가 발생합니다.**
A: Docker Desktop이 실행되지 않은 상태입니다. Docker Desktop을 시작하고 완전히 로딩될 때까지 기다린 후 다시 시도하세요.

**Q: 클라이언트에서 서버에 연결할 수 없습니다.**
A: 방화벽에서 6543 포트가 허용되어 있는지 확인하고, 서버 IP 주소가 올바른지 확인하세요.

**Q: 개인키 생성이 안 됩니다.**
A: 마스터 키가 올바르게 생성되었는지 `pkg_keys/` 폴더를 확인하세요.

### 로그 확인
- GUI 프로그램의 로그 창에서 실시간 로그 확인
- Docker 로그: `docker-compose logs -f`
- Flask 서버 로그는 Docker 컨테이너 내부에서 확인 가능

## 포트 정보

- **기본 포트**: 6543
- **Docker 컨테이너**: 내부 포트 6543을 호스트 6543으로 매핑
- **방화벽**: 클라이언트 접근을 위해 6543 포트 허용 필요

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