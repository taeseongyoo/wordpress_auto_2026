import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.wp_client import WordPressClient
from src.utils.logger import get_logger

logger = get_logger("FixSlugs")

def fix_slugs():
    client = WordPressClient()
    
    # 수정할 포스트 정보 (ID: 새 슬러그)
    updates = {
        722: "youth-future-savings-2026",
        737: "youth-future-savings-2026-application",
        743: "youth-future-savings-vs-leap-account-2026"
    }
    
    logger.info("========================================")
    logger.info("슬러그 긴급 수정 작업 시작")
    logger.info("========================================")
    
    for post_id, new_slug in updates.items():
        logger.info(f"포스트 {post_id} 슬러그 업데이트 중... -> {new_slug}")
        
        # 업데이트 요청
        result = client.update_post(post_id, {"slug": new_slug})
        
        if result:
            logger.info(f"✅ 성공: {result.get('link')}")
        else:
            logger.error(f"❌ 실패: ID {post_id}")
            
    logger.info("모든 작업 완료.")

if __name__ == "__main__":
    fix_slugs()
