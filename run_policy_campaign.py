# Policy & Support Solutions Campaign - Post 2 (Youth Rent Support)

## Goal
Generate Post 2 in the "Policy & Support Solutions" chain, strictly enforcing the **"Fixed 5 Internal/External Links"** rule.

## Configuration
- **Topic**: 2026년 청년 월세 특별 지원: 조건, 신청 방법, 지급일 총정리
- **Predecessor**: [Post 1](https://smart-work-solution.com/?p=778)
- **Link Strategy (5 Links Fixed)**:
    - **Internal**:
        1. 2026년 정부지원금 통합 조회 (Post 1 - ID 778)
        2. 청년미래적금 2026 가이드 (ID 743)
        3. 청년도약계좌 신청 (ID 737)
        4. 정부지원금 사업계획서 (ID Unknown - Find latest)
        5. AI 전자책 수익화 (ID 710 - Cross-link)
    - **External**: 1 per section (approx 5-7 total), strictly High Authority.

## Script Logic
1. Load `recent_posts.json` to get URLs.
2. Construct `internal_links` list with exactly 5 items.
3. Call `generator.generate_post` with this list.
4. Verify output.
