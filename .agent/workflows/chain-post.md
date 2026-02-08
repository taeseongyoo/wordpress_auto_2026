---
description: 정부지원금 가두리 전략 - 3개 포스트 체인 생성, 이미지 포함
---

# 🔗 정부지원금 체인 포스트 생성 워크플로우

> 이 워크플로우는 3개의 연결된 블로그 포스트를 자동 생성합니다.
> Post 3 → Post 2 → Post 1 → Anchor (기존 인기글)

## 📋 사전 준비

1. OpenAI API 크레딧 확인 (최소 $5 권장)
2. WordPress 사이트 접속 가능 상태 확인

## 🚀 실행 방법

// turbo-all

### Step 1: 프로젝트 폴더로 이동

```bash
cd /Users/yuilsang/wordpress_auto_2026
```

### Step 2: 체인 포스트 생성 실행

```bash
.venv/bin/python run_chain_campaign_v2.py
```

**⏱️ 예상 소요 시간:** 약 5-7분

**📝 생성되는 포스트:**

- Post 1: 정부지원금 종류 총정리 (허브)
- Post 2: 사업계획서 작성 팁 (하우투)
- Post 3: 정책 변화 트렌드 (뉴스)

### Step 3: 이미지 확인

```bash
.venv/bin/python check_images.py
```

### Step 4: 문제 시 이미지 수리

특정 포스트 이미지가 누락된 경우:

```bash
.venv/bin/python repair_post2_images.py  # Post 2 수리 예시
```

## ⚠️ 주의사항

- 스크립트가 중간에 멈추면 **run_chain_campaign_v2.py**를 수정해서 Recovery Mode로 전환해야 함
- 이미지 생성에 OpenAI 크레딧 소모됨 (포스트당 약 4장)
- 생성된 포스트는 **임시글(Draft)** 상태로 저장됨 → WordPress에서 수동 발행 필요

## 📂 관련 파일

| 파일                       | 설명                    |
| -------------------------- | ----------------------- |
| `run_chain_campaign_v2.py` | 메인 실행 스크립트      |
| `check_images.py`          | 이미지 삽입 상태 확인   |
| `repair_chain_images.py`   | 전체 체인 이미지 수리   |
| `repair_post2_images.py`   | Post 2 전용 이미지 수리 |

## 🎯 커스텀 주제로 실행하려면

`run_chain_campaign_v2.py` 파일 내 아래 변수 수정:

- `topic`: Post 1 주제
- `topic2`: Post 2 주제
- `topic3`: Post 3 주제
- `ANCHOR_POST`: 링크할 기존 인기글 정보
