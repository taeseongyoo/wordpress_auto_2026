import json
import os
from openai import OpenAI
from src.config.settings import Config
from src.utils.logger import get_logger

logger = get_logger("ContentGenerator")

class ContentGenerator:
    """
    OpenAI API를 사용하여 블로그 콘텐츠를 생성하는 클래스입니다.
    """
    def __init__(self):
        Config.validate()
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = "gpt-4o"  # 최신 모델 사용
        self.verified_tags = self._load_verified_tags()

    def _load_verified_tags(self):
        """승인된 태그 리스트를 로드합니다."""
        try:
            # 절대 경로로 태그 파일 접근 (설정 파일 위치 기준)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            tag_file = os.path.join(base_dir, "config", "verified_tags.json")
            
            with open(tag_file, 'r', encoding='utf-8') as f:
                tags_data = json.load(f)
                # 모든 카테고리의 태그를 하나의 리스트로 통합
                all_tags = []
                for category in tags_data.values():
                    all_tags.extend(category)
                return ", ".join(all_tags)
        except Exception as e:
            logger.error(f"태그 파일 로드 실패: {e}")
            return "인공지능, 자동화, 수익화, 정부지원금, 디지털노마드" # 기본 태그

    def _extract_core_keyword(self, topic: str) -> str:
        """
        주제에서 조사(은/는/이/가/을/를/의/에/로/와/과 등)를 제거하고 핵심 명사만 추출합니다.
        간단한 규칙 기반으로 처리하며, 필요시 AI를 활용할 수도 있습니다.
        """
        return topic.strip()

    def generate_post(self, topic: str, internal_links: list = None) -> dict:
        """
        주어진 주제로 SEO 최적화된 블로그 포스트를 생성합니다. (Iterative 방식: 3000자 이상 보장)
        Args:
            topic (str): 주제
            internal_links (list): 내부 링크 리스트 [{'title':..., 'link':...}, ...]
        """
        logger.info(f"콘텐츠 생성 시작 (Iterative V4 - Smart SEO): {topic}")
        
        try:
            # 1. 핵심 키워드 및 개요 생성
            logger.info("1. 개요 생성 중...")
            outline_data = self._generate_outline(topic)
            focus_keyword = outline_data.get("focus_keyword", topic)
            title = outline_data.get("title", f"{focus_keyword} 가이드")
            
            # 슬러그: 영문 (구글 SEO 친화적, 인코딩 이슈 해결)
            slug = outline_data.get("slug", "post-slug")
            # 만약 개요에서 한글 슬러그가 넘어왔다면 안전하게 변환하거나 그대로 둠 (outline 프롬프트도 수정 필요)
            if not slug or slug == "post-slug":
                # 비상시 포커스 키워드를 영문으로 변환하는 로직이 없으므로 일단 한글이라도 넣음 (하지만 outline에서 영문 강제할 것임)
                 slug = focus_keyword.replace(" ", "-")
            
            description = outline_data.get("description", "")
            sections = outline_data.get("sections", [])
            
            logger.info(f"개요 완료: {len(sections)} 섹션 / 키워드: {focus_keyword} / 슬러그: {slug}")
            
            # 2. 이미지 메타데이터 생성 (신규: 캡션/ALT 정밀화)
            logger.info("2. 이미지 메타데이터(Alt/Caption) 생성 중...")
            image_metadata_list = self._generate_image_metadata(topic, title, sections, focus_keyword)
            # 호환성 유지
            image_prompts = [item['prompt'] for item in image_metadata_list]

            # 3. 서론 생성
            logger.info("3. 서론 생성 중...")
            intro_html = self._clean_html(self._generate_intro(topic, focus_keyword))
            
            # 4. 본론 섹션별 상세 생성 (내부 링크 분배)
            body_html = ""
            total_sections = len(sections)
            links_per_section = 1 # 섹션당 1개 정도 배분
            
            import random
            random.shuffle(internal_links) # 링크 순서 섞기
            
            for idx, section_title in enumerate(sections):
                logger.info(f"4. 섹션 생성 중 [{idx+1}/{total_sections}]: {section_title}")
                
                # 현재 섹션에 할당할 링크 계산
                start_idx = idx * links_per_section
                end_idx = start_idx + links_per_section
                section_links = internal_links[start_idx:end_idx] if internal_links else []
                
                section_content = self._clean_html(self._generate_section(topic, section_title, focus_keyword, section_links))
                body_html += section_content + "\n\n"

            # 5. 결론 및 FAQ 생성
            logger.info("5. 결론 및 FAQ 생성 중...")
            faq_html = self._clean_html(self._generate_faq(topic, focus_keyword))
            
            # 6. 남은 내부 링크 하단 배치 (보조 수단)
            # 본문에 삽입되지 못한 나머지 링크들을 하단에 배치하여 연결성 확보
            remaining_links = internal_links[total_sections * links_per_section:]
            internal_link_html = ""
            
            if remaining_links:
                internal_link_html = f"""
                <div class="internal-links" style="margin: 30px 0; padding: 20px; background-color: #f9f9f9; border-left: 5px solid #0073aa;">
                    <h3>💡 {focus_keyword} 관련 더 보기</h3>
                    <ul>
                """
                for link in remaining_links:
                    t = link.get('title', '관련 글')
                    u = link.get('link', '#')
                    internal_link_html += f"<li><a href='{u}' target='_blank' rel='dofollow'>{t}</a></li>"
                internal_link_html += "</ul></div>"
                logger.info(f"하단 보조 링크 섹션 생성 완료 ({len(remaining_links)}개)")

            # 7. 전체 병합
            full_content = f"{intro_html}\n\n{body_html}\n\n{internal_link_html}\n\n{faq_html}"
            
            # 태그 선택
            raw_tags = self.verified_tags.split(", ")
            import random
            selected_tags = random.sample(raw_tags, k=min(5, len(raw_tags)))
            selected_tags.append(focus_keyword)

            result = {
                "title": title,
                "slug": slug,
                "content": full_content,
                "tags": list(set(selected_tags)),
                "rank_math_focus_keyword": focus_keyword,
                "rank_math_description": description,
                "excerpt": description,
                "image_prompts": image_prompts,
                "images": image_metadata_list
            }
            
            logger.info(f"콘텐츠 생성 완료 (총 길이: {len(full_content)}자)")
            return result

        except Exception as e:
            logger.error(f"콘텐츠 생성 전체 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _generate_image_metadata(self, topic: str, title: str, sections: list, keyword: str) -> list:
        """
        주제와 섹션 정보를 바탕으로 4장의 이미지에 대한 정밀한 메타데이터(Prompt, Alt, Caption)를 생성합니다.
        """
        prompt = f"""
        블로그 포스트의 주제와 섹션 정보를 바탕으로, 본문에 삽입할 4장의 이미지에 대한 메타데이터를 JSON으로 작성하세요.
        
        주제: {topic}
        핵심 키워드: {keyword}
        섹션 목차: {", ".join(sections)}
        
        [필수 요구사항]
        1. **총 4장**의 이미지 정보를 생성하세요. (1번째: type='featured', 나머지 3개: type='body')
        2. **프롬프트(Prompt)**: DALL-E 3가 고품질 이미지를 생성할 수 있도록 영어로 구체적으로 작성하세요. (Modern, High quality, Infographic style 등)
        3. **대체 텍스트(Alt Text)**: 검색 엔진을 위해 '{keyword}'를 반드시 포함하고, 시각 장애인을 위해 이미지를 묘사하세요. (한글)
        4. **캡션(Caption)**: **반드시** '{keyword}'를 포함하여 **20자 이내**로 간결하게 작성하세요. (예: "AI 수익화의 핵심 전략 그래프")
        
        [출력 구조 (JSON)]
        {{
            "images": [
                {{
                    "type": "featured",
                    "prompt": "eng prompt...",
                    "alt": "한글 대체 텍스트",
                    "caption": "한글 캡션 (간결)"
                }},
                {{
                    "type": "body",
                    "prompt": "eng prompt...",
                    "alt": "한글 대체 텍스트",
                    "caption": "한글 캡션 (간결)"
                }},
                ... (총 4개 필수)
            ]
        }}
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            content = self._clean_html(response.choices[0].message.content)
            data = json.loads(content)
            if "images" in data:
                return data["images"]
            elif isinstance(data, list):
                return data
            else:
                for key, val in data.items():
                    if isinstance(val, list):
                        return val
                return []
        except Exception as e:
            logger.error(f"이미지 메타데이터 생성 실패: {e}")
            return [
                {"type": "featured", "prompt": f"{topic}, high quality", "alt": topic, "caption": f"{topic} 대표 이미지"},
                {"type": "body", "prompt": f"{topic} detail, infographic", "alt": f"{topic} 상세", "caption": f"{topic} 상세 설명"},
                {"type": "body", "prompt": f"{topic} analysis, chart", "alt": f"{topic} 분석", "caption": f"{topic} 분석 도표"},
                {"type": "body", "prompt": f"{topic} future, vision", "alt": f"{topic} 전망", "caption": f"{topic} 미래 전망"}
            ]

    def _clean_html(self, text: str) -> str:
        """
        AI 응답에서 불필요한 마크다운 코드 블록(```html, ```)을 제거합니다.
        """
        if not text:
            return ""
        text = text.replace("```html", "").replace("```", "")
        return text.strip()

    def _generate_outline(self, topic: str) -> dict:
        prompt = f"""
        주제 '{topic}'에 대한 블로그 포스트 개요를 JSON으로 작성하세요.
        필수 조건:
        1. 'focus_keyword': 주제의 핵심 단어만 추출. **조사(의, 를, 을, 로써, 에서 등), 접속사, 부사 등 모든 불필요한 단어 완전 배제.** 순수 명사/키워드만. (예: "AI 자동화", "노코드 수익화")
        2. 'title': 핵심 키워드가 맨 앞에 오고, **반드시 '2026'** 같은 연도를 포함한 매력적인 제목.
        3. 'slug': 주제와 키워드를 반영한 **영문 슬러그** (hyphen-style). (예: ai-monetization-strategy-2026)
        4. 'description': 160자 이내의 메타 디스크립션. **반드시 '{1}'(Focus Keyword)를 문장 초반에 포함할 것.** 순수 한글/영문/숫자만 사용.
        5. 'sections': 본론 H2 소제목 6~8개 리스트.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(self._clean_html(response.choices[0].message.content))

    def _generate_intro(self, topic: str, keyword: str) -> str:
        prompt = f"""
        주제 '{topic}'(키워드: '{keyword}')에 대한 서론을 HTML로 작성하세요.
        - 첫 문장은 반드시 '{keyword}'(으)로 시작할 것.
        - 독자의 호기심을 자극하고 문제 의식을 제기할 것.
        - 분량: 300~500자.
        - 문단: 한 문단은 2~3문장을 넘지 않게 <p> 태그로 자주 나눌 것. (모바일 가독성)
        - 출력: 순수 HTML (마크다운 ``` 사용 금지).
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    def _generate_section(self, topic: str, section_title: str, keyword: str, links: list = None) -> str:
        
        # 내부 링크: 오직 검증된 URL만 사용 (404 방지)
        internal_link_instruction = "[내부 링크 없음]"
        if links:
            link_list_str = "\n".join([f"- URL: {l['link']}, 제목: {l['title']}" for l in links])
            internal_link_instruction = f"""
            [내부 링크 - 필독]
            ⚠️ 아래 제공된 URL만 사용하세요. 절대로 URL을 상상하거나 만들어내지 마세요!
            - 검증된 링크:
            {link_list_str}
            - 사용법: 문맥에 맞게 1개만 자연스럽게 삽입. (예: "더 자세한 내용은 <a href='...'>[제목]</a>에서 확인하세요")
            - 중요: 위 목록에 없는 URL은 절대 사용 금지! 404 에러 발생함.
            """

        prompt = f"""
        블로그 포스트 '{topic}'의 챕터 '{section_title}' 내용을 상세히 작성하세요.
        
        [기본 규칙]
        - 형식: HTML (H2 태그로 제목 시작, 이후 p, ul/ol, strong 등 사용)
        - 내용: 구체적인 정보, 예시, 데이터 포함. 모호한 표현 금지.
        - 키워드 '{keyword}'를 자연스럽게 2회 이상 포함.
        
        [링크 전략 - 매우 중요]
        1. **외부 링크 (글당 최소 1개, 최대 3개 / 이 섹션에서 1개 권장)**:
           - 허용 대상: 대형 글로벌 기업(Netflix, Spotify, Google, Amazon 등), 정부기관(.go.kr, .gov), 공식 통계청
           - ⚠️ 위키백과 금지! 산만하고 집중을 방해함.
           - 형식: <strong><a href="실제URL" target="_blank">출처명</a></strong>
           - 존재하지 않는 URL 사용 금지! 확실한 URL만 사용할 것.
        
        2. **내부 링크**:
           {internal_link_instruction}
        
        [가독성 (Mobile Optimized)]
        - 한 문단은 2~3문장 이내로 짧게 끊어서 작성할 것.
        - 중요한 핵심 문장이나 키워드는 `<strong>` 태그로 **볼드 처리**하여 강조할 것.
        
        [분량 및 형식]
        - 분량: 공백 포함 700자 이상 필수.
        - H2 태그에는 '{section_title}'을 그대로 쓸 것.
        - 금지: '[이미지 설명]', '그림 1' 같은 이미지 관련 텍스트 절대 금지.
        - 출력: 순수 HTML (마크다운 ``` 사용 금지).
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    def _generate_faq(self, topic: str, keyword: str) -> str:
        prompt = f"""
        주제 '{topic}' 관련 자주 묻는 질문(FAQ) 3가지와 답변을 작성하세요.
        - **최신성 반영**: 2025~2026년 최신 트렌드와 미래 전망을 반영하여 답변할 것.
        - 형식: HTML <details><summary>질문</summary>답변</details> 구조 사용.
        - 마지막 태그: <h2>자주 묻는 질문</h2> 으로 시작할 것.
        - 답변에도 키워드 '{keyword}'를 포함할 것.
        - 출력: 순수 HTML (마크다운 ``` 사용 금지).
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
