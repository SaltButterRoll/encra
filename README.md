# ENCRA - Identity-Based Image Security System

ENCRA는 이메일 기반 신원 확인(IBE, Identity-Based Encryption)을 사용하는 이미지 보안 시스템입니다. 이미지와 PDF 파일의 특정 영역(ROI)을 선택하여 암호화하고, 지정된 수신자만 복호화할 수 있는 혁신적인 보안 솔루션입니다.

## 🚀 빠른 시작

### ⚠️ 사전 준비사항
**Docker Desktop을 미리 설치하고 실행해야 합니다:**
1. [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) 다운로드 및 설치
2. **Docker Desktop 실행** (시스템 트레이에서 Docker 아이콘이 활성화 상태인지 확인)
3. PowerShell 또는 Command Prompt에서 `docker version` 명령으로 정상 작동 확인

### 📥 다운로드

📦 **[GitHub 릴리즈 페이지](../../releases)에서 최신 버전을 다운로드하세요**

**일반 사용자 (권장):**
- **`setup_client_gui_vX.X.X.zip`** - 클라이언트 애플리케이션
- 관리자에게 PKG 서버 주소와 포트 정보를 받아서 사용

**관리자 또는 테스트 사용자:**
- **`setup_pkg_gui_vX.X.X.zip`** - 키 관리 서버
- **`setup_client_gui_vX.X.X.zip`** - 클라이언트 애플리케이션

## 🎯 주요 기능

### 🔐 이미지/PDF 암호화
- **선택적 영역 암호화**: 이미지나 PDF의 특정 부분만 드래그로 선택하여 암호화
- **다중 수신자 지원**: 한 번의 암호화로 여러 명에게 전송 가능
- **실시간 미리보기**: 암호화할 영역을 실시간으로 확인
- **다양한 파일 형식**: JPEG, PNG, PDF 지원

### 🔓 안전한 복호화
- **이메일 기반 인증**: 이메일 주소를 신원으로 사용하는 IBE 암호화
- **자동 개인키 관리**: 이메일 인증 후 개인키 자동 생성 및 저장
- **권한 기반 복호화**: 수신자로 지정된 이메일만 복호화 가능

### 🌐 웹 기반 인터페이스
- **사용하기 쉬운 UI**: 직관적인 웹 인터페이스
- **로컬 실행**: 개인 컴퓨터에서 안전하게 실행
- **크로스 플랫폼**: Windows, macOS, Linux 지원 (Docker 기반)

## 📋 시스템 구성

### 👥 사용자 역할

**🔧 관리자 (시스템 관리자)**
- **PKG 서버 운영**: 키 관리 서버 설치 및 운영
- **Gmail 설정**: 인증 메일 발송을 위한 Gmail 계정 설정
- **서버 정보 제공**: 일반 사용자에게 서버 주소/포트 정보 제공

**👤 일반 사용자**
- **클라이언트 앱 사용**: 이미지 암호화/복호화 기능 사용
- **서버 연결**: 관리자가 제공한 PKG 서버 정보로 연결
- **이메일 인증**: 본인 이메일로 인증하여 개인키 발급

### 🏗️ 시스템 아키텍처

```
┌─────────────────┐    이메일 인증 요청     ┌─────────────────┐
│   Client App    │ ──────────────────────→ │   PKG Server    │
│  (일반 사용자)   │                        │   (관리자 운영)  │
│                 │ ←──────────────────────  │                 │
│ • 이미지 암호화  │    개인키 발급           │ • 키 관리        │
│ • 이미지 복호화  │                        │ • 이메일 인증    │
│ • 이메일 인증    │                        │ • 개인키 생성    │
└─────────────────┘                        └─────────────────┘
```

## 🚀 설치 및 실행

### 👤 일반 사용자 (클라이언트만 사용)

1. **클라이언트 앱 다운로드**
   ```
   setup_client_gui_vX.X.X.zip 다운로드 → 압축 해제
   ```

2. **클라이언트 앱 실행**
   ```
   setup_client_gui.exe 실행
   ```

3. **PKG 서버 정보 입력**
   - 관리자에게 받은 **PKG 서버 URL** 입력 (예: `http://192.168.1.100:6543`)
   - **포트 번호** 설정 (기본값: 61624)

4. **Docker 빌드 및 실행**
   - **"도커 빌드/실행"** 버튼 클릭
   - 완료 후 **"클라이언트 바로가기"** 버튼으로 웹 접속

### 🔧 관리자 (PKG 서버 + 클라이언트)

1. **PKG 서버 설정 및 실행**
   ```
   setup_pkg_gui_vX.X.X.zip 다운로드 → 압축 해제
   setup_pkg_gui.exe 실행
   ```
   - **Gmail 주소** 및 **앱 비밀번호** 입력
   - **"도커 빌드/실행"** 버튼 클릭
   - 서버가 `http://localhost:6543`에서 실행됨

2. **클라이언트 앱 설정 및 실행**
   ```
   setup_client_gui_vX.X.X.zip 다운로드 → 압축 해제
   setup_client_gui.exe 실행
   ```
   - PKG 서버 URL: `http://localhost:6543` (로컬 서버)
   - 또는 `http://내부IP:6543` (네트워크 공유 시)

### 🧪 테스트 사용자

관리자용 설정을 따라하되, 테스트 완료 후에는:
- 실제 운영 시 관리자가 운영하는 PKG 서버 정보로 변경
- 또는 클라이언트만 사용하여 공용 PKG 서버에 연결

## 💡 사용 시나리오

### 시나리오 1: 기업 환경
```
1. IT 관리자가 PKG 서버 운영 (사내 서버)
2. 직원들은 클라이언트 앱만 설치
3. 중요한 문서나 이미지를 특정 직원들에게만 암호화하여 전송
```

### 시나리오 2: 개인/소규모 팀
```
1. 팀 리더가 본인 PC에서 PKG 서버 실행
2. 팀원들은 클라이언트 앱으로 연결
3. 프로젝트 관련 이미지/문서를 안전하게 공유
```

### 시나리오 3: 개인 테스트
```
1. 개인 PC에서 PKG 서버와 클라이언트 모두 실행
2. 자신의 이메일로 인증하여 암호화/복호화 테스트
3. 기능 확인 후 실제 사용 환경에 도입
```

## 📚 사용 방법

### 1️⃣ 이메일 인증 (최초 1회)
1. 클라이언트 웹 접속
2. **"이메일 인증하기"** 버튼 클릭
3. 이메일 주소 입력 후 인증 요청
4. 이메일로 받은 인증 링크 클릭
5. 개인키 자동 생성 및 저장 완료

### 2️⃣ 이미지 암호화
1. **"이미지 암호화"** 메뉴 선택
2. 이미지 또는 PDF 파일 업로드
3. 암호화할 영역을 마우스로 드래그하여 선택
4. **수신자 이메일 주소** 입력 (여러 명 가능)
5. **"암호화"** 버튼 클릭 → 암호화된 파일 다운로드

### 3️⃣ 이미지 복호화
1. **"이미지 복호화"** 메뉴 선택
2. 암호화된 파일 업로드
3. **"복호화"** 버튼 클릭 (개인키 필요)
4. 복호화된 원본 파일 다운로드

## 🔧 시스템 요구사항

### 필수 요구사항
- **Windows 10/11** (64비트)
- **Docker Desktop for Windows** (설치 및 실행 필요)
- **4GB RAM** 이상
- **3GB 디스크 공간** (Docker 이미지 포함)

### PKG 서버 추가 요구사항 (관리자만)
- **Gmail 계정** (앱 비밀번호 설정 필요)
- **인터넷 연결** (이메일 발송용)
- **고정 IP** 또는 **도메인** (클라이언트 접근용)

## 📁 프로젝트 구조

```
encra_dist/
├── README.md                    # 이 파일 (전체 프로젝트 설명)
├── LICENSE                      # 라이선스 정보
├── encra_pkg/                   # PKG 서버 (관리자용)
│   ├── README.md               # PKG 서버 상세 가이드
│   ├── setup_pkg_gui.exe       # PKG 서버 GUI 설정 프로그램
│   └── setting/                # Flask 키 관리 서버
└── client_app/                 # 클라이언트 앱 (일반 사용자용)
    ├── README.md               # 클라이언트 앱 상세 가이드
    ├── setup_client_gui.exe    # 클라이언트 GUI 설정 프로그램
    └── setting/                # Flask 웹 애플리케이션
```

## ❓ 문제 해결

### 자주 묻는 질문

**Q: Docker Desktop이 설치되어 있지 않습니다.**
A: [Docker Desktop](https://docs.docker.com/desktop/install/windows-install/)을 다운로드하여 설치하고 실행한 후 다시 시도하세요.

**Q: "Docker daemon is not running" 오류가 발생합니다.**
A: Docker Desktop을 시작하고 완전히 로딩될 때까지 기다린 후 다시 시도하세요.

**Q: 클라이언트에서 PKG 서버에 연결할 수 없습니다.**
A: 
- PKG 서버가 실행 중인지 확인
- 서버 IP 주소와 포트 번호가 올바른지 확인
- 방화벽에서 해당 포트가 허용되어 있는지 확인

**Q: exe 파일 실행 시 보안 경고가 나타납니다.**
A: Windows Defender 경고는 서명되지 않은 실행 파일에 대한 일반적인 보안 경고입니다. **"추가 정보" → "실행"**을 선택하여 진행하세요.

## 🔒 보안 특징

### IBE (Identity-Based Encryption)
- **이메일 기반 암호화**: 공개키 인증서 없이 이메일 주소만으로 암호화
- **중앙 키 관리**: PKG 서버에서 안전한 키 생성 및 관리
- **선택적 접근**: 지정된 수신자만 복호화 가능

### 로컬 처리
- **개인정보 보호**: 이미지 처리가 로컬에서 수행됨
- **네트워크 최소화**: 키 교환 시에만 서버 통신
- **안전한 저장**: 개인키가 로컬에 안전하게 저장

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🤝 기여하기

1. 이 저장소를 포크하세요
2. 새로운 기능 브랜치를 생성하세요 (`git checkout -b feature/new-feature`)
3. 변경사항을 커밋하세요 (`git commit -am 'Add new feature'`)
4. 브랜치에 푸시하세요 (`git push origin feature/new-feature`)
5. Pull Request를 생성하세요

## 📞 문의 및 지원

추가 문의사항이나 기술 지원이 필요한 경우, 프로젝트 이슈 트래커를 활용해 주세요.

---
**ENCRA Team** | IBE 기반 이미지 보안 시스템 