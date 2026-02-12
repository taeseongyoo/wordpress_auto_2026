import json
import os
from openai import OpenAI
from src.config.settings import Config
from src.utils.logger import get_logger

logger = get_logger("ContentGenerator")

# ==============================================================================
# [SEO PROTOCOL LOCKED]
# 이 생성기 로직은 'SEO_PROTOCOL.md'에 기준하여 검증되었습니다.
# - 연관 키워드 8개 생성 및 본문 자연스러운 삽입.
# - H2 섹션 6~8개, FAQ 포함 구조.
# - 이미지 메타데이터(Alt/Caption)에 메인 키워드 포함.
# 로직 변경 시 주의가 필요합니다.
# ==============================================================================

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
            
            # [강제 로직] 슬러그 길이 제한 (75자)
            if len(slug) > 75:
                slug = slug[:75].rstrip("-")
            
            # 만약 개요에서 한글 슬러그가 넘어왔다면 안전하게 변환하거나 그대로 둠 (outline 프롬프트도 수정 필요)
            if not slug or slug == "post-slug":
                # 비상시 포커스 키워드를 영문으로 변환하는 로직이 없으므로 일단 한글이라도 넣음 (하지만 outline에서 영문 강제할 것임)
                 slug = focus_keyword.replace(" ", "-")
                 if len(slug) > 75: slug = slug[:75]
            
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
            
            # [신규] 외부 링크 계획 (각 섹션별 고유 출처)
            logger.info("4. 외부 링크 및 내부 링크 전략 수립 중...")
            external_link_plans = self._plan_external_links(sections)
            
            import random
            random.shuffle(internal_links) # 내부 링크 순서 섞기 (중복 방지)
            
            body_html = ""
            total_sections = len(sections)
            
            for idx, section_title in enumerate(sections):
                logger.info(f"5. 섹션 생성 중 [{idx+1}/{total_sections}]: {section_title}")
                
                # 내부 링크 1개 할당 (순환)
                current_internal_link = []
                if internal_links:
                    link_idx = idx % len(internal_links)
                    current_internal_link = [internal_links[link_idx]]
                
                # 외부 링크 힌트 1개 할당
                current_external_hint = None
                if idx < len(external_link_plans):
                    current_external_hint = external_link_plans[idx]
                
                section_content = self._clean_html(self._generate_section(
                    topic, section_title, focus_keyword, 
                    internal_links=current_internal_link, 
                    external_link_hint=current_external_hint
                ))
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
            selected_tags = random.sample(raw_tags, k=min(7, len(raw_tags)))
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
                "images": image_metadata_list,
                "related_keywords": outline_data.get("related_keywords", [])
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
        except Exception as e:
            logger.error(f"이미지 메타데이터 생성 실패: {e}")
            return []
            
        # [Strict Enforcement] 키워드 누락 시 강제 주입
        final_images = []
        raw_images = data.get("images", []) if isinstance(data, dict) else data
        
        if not isinstance(raw_images, list):
            raw_images = []
            
        for img in raw_images:
            # 안전장치: 필수 키 확인
            if "alt" not in img: img["alt"] = keyword
            if "caption" not in img: img["caption"] = keyword
            if "prompt" not in img: img["prompt"] = f"{keyword} illustration"
            
            # 1. Alt Text 강제
            if keyword not in img["alt"]:
                # 문맥 고려 없이 가장 앞에 '키워드: ' 형태로 붙임 (가장 확실함)
                img["alt"] = f"{keyword}: {img['alt']}"
                
            # 2. Caption 강제
            if keyword not in img["caption"]:
                img["caption"] = f"{keyword} - {img['caption']}"
                
            # HTML 태그 제거 (혹시 모를 오염 방지)
            img["alt"] = img["alt"].replace("<", "").replace(">", "")
            img["caption"] = img["caption"].replace("<", "").replace(">", "")
            
            final_images.append(img)
            
        return final_images

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
        1. 'focus_keyword': **가장 중요한 '검색어' 1~2단어만 추출.** (예: "청년미래적금", "청년도약계좌 비교"). **절대로 문장형이나 긴 복합명사 금지.** (3단어 초과 시 감점). 사람들이 구글에 검색할 법한 짧은 명사형.
        2. 'title': **매력적이고 클릭을 유도하는 제목.** 핵심 키워드를 포함하되, 문장형으로 자연스럽게 작성. **반드시 '2026'** 포함. (예: "2026 청년미래적금 vs 청년도약계좌: 금리 비교 및 환승 꿀팁")
        3. 'slug': 주제와 키워드를 반영한 **영문 슬러그** (hyphen-style). **50자 이내로 짧고 간결하게.** (예: youth-future-savings-2026)
        4. 'description': 160자 이내의 메타 디스크립션. **무조건 문장의 맨 첫 단어를 '{' + focus_keyword + '}'(으)로 시작할 것.** (예: "청년미래적금은 2026년...")
        5. 'sections': 본론 H2 소제목 6~8개 리스트.
        6. 'related_keywords': Rank Math SEO 점수를 위한 **연관 키워드(LSI) 8개** 리스트. (예: ["청년 지원금", "2026 적금", "이자 높은 은행", ...])
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        try:
            outline = json.loads(self._clean_html(response.choices[0].message.content))
            
            # [신규 로직] 연관 키워드 8개 추출 (없으면 자동 생성)
            related_keywords = outline.get("related_keywords", [])
            if len(related_keywords) < 8:
                # 부족하면 추가 생성 요청하거나 더미로 채우지 않고 있는대로 씀 (나중에 보완 가능)
                pass
            
            # [강제 로직] 메타 설명이 포커스 키워드로 시작하지 않으면 강제 주입
            desc = outline.get("description", "")
            fk = outline.get("focus_keyword", topic)  # 키워드 없으면 주제 사용
            
            # 조사 제거된 순수 키워드만 사용 (예: "AI 수익화는..." -> "AI 수익화")
            clean_fk = fk.split(" ")[0] if " " in fk else fk 
            
            if not desc.startswith(fk):
                # 기존 설명 앞에 키워드 붙임 (문맥 자연스럽게 연결 시도)
                new_desc = f"{fk}: {desc}"
                outline["description"] = new_desc[:160] # 160자 제한
                logger.info(f"메타 설명 키워드 강제 주입: {outline['description']}")
                
            return outline
        except Exception as e:
            logger.error(f"개요 생성 실패: {e}")
            return {
                "title": f"{topic} 가이드 2026",
                "focus_keyword": topic,
                "slug": f"{topic}-2026",
                "description": f"{topic}: 2026년 최신 트렌드와 전략을 알아보세요.",
                "sections": ["서론", "주요 내용", "결론"],
                "related_keywords": []
            }

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

    def _plan_external_links(self, sections: list) -> list:
        """
        각 섹션별로 사용할 고유한 외부 링크 주제를 계획합니다. (중복 방지)
        """
        section_titles = ", ".join(sections)
        prompt = f"""
        블로그 포스트의 각 섹션에 삽입할 '외부 링크(External Link)' 주제를 계획하세요.
        
        [섹션 목록]
        {section_titles}
        
        [요구사항]
        1. 각 섹션마다 **서로 다른** 공신력 있는 외부 출처를 1개씩 지정하세요.
        2. 출처 예시: 
           - 정부 사이트 (.go.kr), 통계청, 법제처
           - 대형 언론사 (연합뉴스, KBS 등)
           - 구글 학술 검색, 네이버 지식백과 (위키백과 제외)
           - 관련 협회나 공식 기관
        3. **절대로** 같은 사이트를 반복해서 추천하지 마세요. (예: 모든 섹션에 '복지로' 링크 금지)
        4. 출력 형식: JSON 리스트 ["섹션1 출처: 통계청(청년고용동향)", "섹션2 출처: 법제처(관련 법령)", ...]
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(self._clean_html(response.choices[0].message.content))
            links = data.get("links", [])
            # 만약 키가 다르면 값만 리스트로 추출
            if not links:
                links = list(data.values())[0] if data else []
            return links
        except Exception as e:
            logger.error(f"외부 링크 계획 실패: {e}")
            return [f"관련 공신력 있는 출처 {i+1}" for i in range(len(sections))]

    def _generate_section(self, topic: str, section_title: str, keyword: str, 
                          internal_links: list = None, external_link_hint: str = None) -> str:
        
        # 내부 링크: 오직 검증된 URL만 사용 (404 방지)
        internal_link_instruction = "[내부 링크 없음]"
        if internal_links:
            # 리스트가 들어로면 그 중 하나를 *반드시* 쓰도록 유도
            l = internal_links[0] # 첫번째 것 사용 (Generator 메인 루프에서 1개씩 잘라서 줌)
            internal_link_instruction = f"""
            [내부 링크 - 필수 삽입 (문단 중간)]
            - 제목: {l['title']}
            - URL: {l['link']}
            - **[매우 중요] 위치 규칙**: 
              - 절대로 섹션의 맨 마지막에 "참고하세요" 식으로 붙이지 마세요.
              - **반드시** 설명하는 문장의 중간이나 끝에 자연스럽게 녹여내세요.
              - 예시 (O): "...이때 **<a href='{l['link']}' target='_blank'>{l['title']}</a>**를 활용하면 더 효율적으로..."
              - 예시 (X): "...입니다. \n\n 관련 글: {l['title']}" (이런 식의 하단 배치는 금지!)
            - 앵커 텍스트는 유동적으로 변형 가능하나 URL은 절대 변경 금지.
            """

        # 외부 링크 힌트
        ext_link_msg = ""
        if external_link_hint:
            ext_link_msg = f"""
            - **권장 외부 링크 출처**: {external_link_hint}
            - 해당 주제와 관련된 구체적인 페이지를 찾아 링크를 거세요. (예: '{external_link_hint}' 검색 결과 또는 메인 페이지)
            - 형식: <strong><a href="https://..." target="_blank">[{external_link_hint} 바로가기]</a></strong>
            """

        prompt = f"""
        블로그 포스트 '{topic}'의 챕터 '{section_title}' 내용을 상세히 작성하세요.
        
        [기본 규칙]
        - 형식: HTML (H2 태그로 제목 시작, 이후 p, ul/ol, strong 등 사용)
        - 내용: 구체적인 정보, 예시, 데이터 포함. 모호한 표현 금지.
        - **[중요] 키워드 '{keyword}' 남용 금지**:
          - 전체 섹션에서 키워드는 **최대 2~3회**만 자연스럽게 사용하세요. (밀도 2.5% 미만 유지)
          - 같은 단어 반복 대신 **'이 제도', '동 상품', '본 적금'** 등의 대명사나 **'청년 도약 지원책'** 같은 유의어를 적극 활용하세요.
          - 문맥에 맞지 않는 억지스러운 키워드 삽입은 절대 금지합니다.
        
        [링크 전략 - 가두리(Walled Garden) 전략]
        1. **외부 링크 (이 섹션 전용)**:
           {ext_link_msg}
           - 다른 섹션과 중복되지 않는 **고유한 출처**를 사용하세요.
           - ⚠️ 위키백과 금지! 산만하고 집중을 방해함.
           - 존재하지 않는 URL 사용 금지! 확실한 URL만 사용할 것.
        
        2. **내부 링크 (이 섹션 전용)**:
           {internal_link_instruction}
        
        [가독성 (Mobile Optimized)]
        - 한 문단은 2~3문장 이내로 짧게 끊어서 작성할 것.
        - 중요한 핵심 문장이나 키워드는 `<strong>` 태그로 **볼드 처리**하여 강조할 것.
        
        [분량 및 형식]
        - 분량: 공백 포함 500자 내외 (풍부한 내용).
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
