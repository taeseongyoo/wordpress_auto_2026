# WordPress Automation System v1.0 🚀

LEO 대표님을 위한 워드프레스 자동화 시스템입니다.
이 프로젝트는 **Python**을 사용하여 워드프레스 포스팅, SEO 설정, 이미지 업로드를 자동화합니다.

## 🛠️ 설치 및 실행 가이드 (Installation)

이 프로젝트는 초고속 패키지 매니저 **`uv`** 사용을 권장합니다.

### 1. 환경 설정 및 설치

```bash
# 1. uv 설치 (아직 없다면)
pip install uv

# 2. 가상환경 생성 및 패키지 설치
uv venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate   # Windows

# 3. 의존성 설치
uv pip install -r requirements.txt
```

### 2. 비밀 금고 설정 (`.env`)

`.env.example` 파일을 복사하여 `.env` 파일을 만들고, 아래 정보를 채워주세요.

```ini
OPENAI_API_KEY=sk-...
WP_URL=https://your-wordpress-site.com
WP_USERNAME=your_username
WP_PASSWORD=your_app_password
```

### 3. 실행 (Usage)

```bash
python main.py
```

## 📁 프로젝트 구조

- `src/`: 소스 코드 디렉토리
- `config/`: 설정 파일
- `logs/`: 실행 로그
