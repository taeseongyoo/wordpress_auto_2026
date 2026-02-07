import logging
import sys
from src.config.settings import Config

def get_logger(name: str):
    """
    표준화된 로거를 반환하는 유틸리티 함수입니다.
    """
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 설정되어 있다면 중복 추가 방지
    if logger.handlers:
        return logger

    logger.setLevel(Config.LOG_LEVEL)

    # 포맷 설정
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 콘솔 출력 핸들러
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
