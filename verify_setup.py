import os
import sys
from dotenv import load_dotenv

# 색상 코드
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def check_env():
    print("🔍 환경 설정 점검 중...")
    
    if not os.path.exists(".env"):
        print(f"{RED}[실패] .env 파일이 없습니다. .env.example을 복사해서 생성해주세요.{RESET}")
        return False
    
    load_dotenv()
    
    required_vars = ["OPENAI_API_KEY", "WP_URL", "WP_USERNAME", "WP_PASSWORD"]
    all_set = True
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            print(f"{RED}[실패] {var} 값이 설정되지 않았습니다.{RESET}")
            all_set = False
        else:
            print(f"{GREEN}[성공] {var} 설정됨{RESET}")
            
    return all_set

def test_connections():
    print("\n🌐 연결 테스트 중...")
    
    # 1. WordPress 연결
    try:
        from src.core.wp_client import WordPressClient
        print("   - 워드프레스 접속 시도...", end=" ")
        client = WordPressClient()
        user = client.get_user_info()
        if user:
            print(f"{GREEN}[성공] 사용자: {user.get('name')} (ID: {user.get('id')}){RESET}")
        else:
            print(f"{RED}[실패] 사용자 정보를 가져오지 못했습니다.{RESET}")
    except Exception as e:
        print(f"{RED}[실패] 워드프레스 연결 에러: {e}{RESET}")

    # 2. OpenAI 연결
    try:
        print("   - OpenAI 접속 시도...", end=" ")
        from src.core.generator import ContentGenerator
        generator = ContentGenerator()
        # 간단한 모델 리스트 조회 대신, 실제로 client 초기화가 잘 되었는지 확인
        # (generator 초기화 시 Config.validate()가 통과되면 일단 OK)
        print(f"{GREEN}[성공] 클라이언트 초기화 완료{RESET}")
    except Exception as e:
         print(f"{RED}[실패] OpenAI 연결 에러: {e}{RESET}")

def main():
    print("========================================")
    print("    워드프레스 자동화 시스템 진단 도구    ")
    print("========================================")
    
    if check_env():
        test_connections()
        print("\n✅ 모든 설정이 올바르면 다음 명령어로 실행해보세요!")
        print("방법 1 (권장): uv run python -m src.main \"주제\"")
        print("방법 2: python3 -m src.main \"주제\"")
    else:
        print("\n❌ 환경 변수 설정을 먼저 완료해주세요.")

if __name__ == "__main__":
    main()
