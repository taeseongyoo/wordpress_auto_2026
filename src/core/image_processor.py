import requests
from openai import OpenAI
from src.config.settings import Config
from src.utils.logger import get_logger
import os

logger = get_logger("ImageProcessor")

class ImageProcessor:
    """
    DALL-E 3를 사용하여 이미지를 생성하고 로컬에 저장하는 클래스입니다.
    """
    def __init__(self):
        Config.validate()
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.output_dir = "generated_images"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_image(self, prompt: str, file_name: str = "thumbnail.jpg") -> str:
        """
        DALL-E 3로 이미지를 생성하고 WebP로 최적화하여 저장합니다.
        """
        logger.info(f"이미지 생성 시작: {prompt[:30]}...")
        
        full_prompt = (
            f"A high-quality, modern, and clean blog illustration about: {prompt}. "
            "ABSOLUTELY NO TEXT, NO LETTERS, NO CALCULATIONS, NO NUMBERS, NO CHARTS WITH DATA VALUES inside the image. "
            "Use 3D isometric or flat vector illustration style, minimalist, abstract, professional, infographic elements without text labels."
        )

        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=full_prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )

            image_url = response.data[0].url
            
            # 파일 확장자를 강제로 webp로 변경
            base_name, _ = os.path.splitext(file_name)
            save_path = os.path.join(self.output_dir, f"{base_name}.webp")
            
            # 이미지 다운로드
            img_data = requests.get(image_url).content
            
            # 이미지 처리 (PILLOW)
            from PIL import Image
            from io import BytesIO
            
            image = Image.open(BytesIO(img_data))
            
            # 리사이징 (가로 최대 1200px)
            if image.width > 1200:
                ratio = 1200 / image.width
                new_height = int(image.height * ratio)
                image = image.resize((1200, new_height), Image.Resampling.LANCZOS)
                
            # WebP 저장 (Quality 85)
            image.save(save_path, "WEBP", quality=85, optimize=True)
            
            logger.info(f"이미지 최적화 저장 완료: {save_path}")
            return save_path

        except Exception as e:
            logger.error(f"이미지 생성 실패: {e}")
            return None
