import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """
    프로젝트 전반에서 사용되는 환경 변수 및 설정을 관리하는 클래스입니다.
    """
    # OpenAI 설정
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # WordPress 설정
    WP_URL = os.getenv("WP_URL")
    WP_USERNAME = os.getenv("WP_USERNAME")
    WP_PASSWORD = os.getenv("WP_PASSWORD")

    # 기타 설정
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls):
        """필수 환경 변수가 설정되어 있는지 확인합니다."""
        missing = []
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if not cls.WP_URL:
            missing.append("WP_URL")
        if not cls.WP_USERNAME:
            missing.append("WP_USERNAME")
        if not cls.WP_PASSWORD:
            missing.append("WP_PASSWORD")
        
        if missing:
            raise ValueError(f"다음 필수 환경 변수가 누락되었습니다: {', '.join(missing)}")

# 설정 유효성 검사 실행 (임포트 시점에 체크)
# 주의: .env가 없는 초기 상태에서는 에러가 날 수 있으므로, 실제 구동 시점에 호출하는 것이 좋을 수도 있습니다.
# 여기서는 클래스 정의만 하고 호출은 main에서 하거나 필요 시 수행합니다.
