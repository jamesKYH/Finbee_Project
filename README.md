# FinBee 딱카 - 카드 추천 서비스

사용자 소비 패턴 분석 및 카드 혜택 정보 기반 개인화 카드 추천 서비스입니다.

## 프로젝트 소개

FinBee 딱카는 사용자의 소비 패턴을 분석하고 개인화된 카드 추천을 제공하는 서비스입니다. RAG(Retrieval Augmented Generation) 기술을 활용하여 사용자의 질문에 맞는 카드를 정확하게 추천하고, 카드 혜택에 대한 상세한 정보를 제공합니다.

## 주요 기능

1. **사용자 소비 패턴 분석**: 사용자 거래 데이터를 분석하여 소비 패턴을 파악합니다.
2. **개인화된 카드 추천**: 소비 패턴에 맞는 최적의 카드를 추천합니다.
3. **마케팅 문구 자동 생성**: 카드 혜택 기반 맞춤형 마케팅 문구를 생성합니다.
4. **카드 혜택 챗봇**: 카드 관련 질문에 RAG 기반으로 정확한 답변을 제공합니다.

## 기술 스택

- **Backend**: Python, Streamlit
- **Database**: MySQL, ChromaDB(벡터 데이터베이스)
- **AI/ML**: OpenAI API, Sentence Transformers
- **Deployment**: Docker, Docker Compose

## 프로젝트 구조

```
.
├── assets/             # 이미지 등 정적 자산
├── db_backup/          # ChromaDB 벡터 저장소
│   └── chroma_db/      # 카드 혜택 임베딩 저장소
├── src/                # 소스 코드
│   ├── app.py          # 메인 스트림릿 애플리케이션
│   ├── db/             # 데이터베이스 관련 코드
│   │   ├── db_utils.py # DB 유틸리티 함수
│   │   └── migrations/ # DB 초기화 스크립트
│   ├── llm/            # 대형 언어 모델 관련 코드
│   │   ├── marketing_generator.py # 마케팅 문구 생성
│   │   └── rag_answer.py # RAG 기반 카드 추천 엔진
│   ├── models/         # 임베딩 모델 관련 코드
│   │   └── insert_embeddings.py # 임베딩 생성 및 저장
│   └── utils/          # 유틸리티 함수
│       └── user_summary.py # 사용자 프로필 요약
├── .env.example        # 환경 변수 예시
├── Dockerfile          # 도커 이미지 빌드 정의
├── docker-compose.yml  # 도커 컴포즈 설정
└── requirements.txt    # 필요 패키지 목록
```

## 설치 및 실행 방법

### 필수 요구사항

- Docker 및 Docker Compose가 설치되어 있어야 합니다.
- MySQL 데이터베이스 접속 정보
- OpenAI API 키

### 실행 방법

1. 이 저장소를 클론합니다:

   ```bash
   git clone https://github.com/your-username/finbee-card-recommender.git
   cd finbee-card-recommender
   ```

2. `.env` 파일을 프로젝트 루트 디렉토리에 생성하고 다음 정보를 입력합니다:

   ```
   MYSQL_HOST=your_mysql_host
   MYSQL_PORT=your_mysql_port
   MYSQL_USER=your_mysql_user
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DATABASE=your_mysql_database
   OPENAI_API_KEY=your_openai_api_key
   ```

3. Docker Compose로 애플리케이션을 실행합니다:

   ```bash
   docker-compose up -d
   ```

4. 브라우저에서 다음 주소로 접속합니다:
   ```
   http://localhost:8503
   ```

### 종료 방법

```bash
docker-compose down
```

## 사용 방법

1. 웹 인터페이스에 접속한 후, 사용자 ID를 입력합니다.
2. 프로필 및 추천 카드 탭에서 사용자의 소비 패턴과 추천 카드를 확인할 수 있습니다.
3. 카드 상담 챗봇 탭에서 원하는 혜택이나 카드에 대해 질문하면 맞춤형 카드 추천을 받을 수 있습니다.

## 데이터베이스 설정

이 프로젝트는 MySQL 데이터베이스와 ChromaDB 벡터 데이터베이스를 사용합니다. 필요한 테이블과 데이터는 Docker 컨테이너 실행 시 자동으로 설정됩니다.

## 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.

## 기여 방법

1. 이 저장소를 포크합니다.
2. 새로운 브랜치를 생성합니다: `git checkout -b feature/amazing-feature`
3. 변경사항을 커밋합니다: `git commit -m 'Add some amazing feature'`
4. 브랜치에 푸시합니다: `git push origin feature/amazing-feature`
5. Pull Request를 제출합니다.

## 문의사항

문의사항이 있으시면 이슈를 등록하거나 이메일로 연락주세요.
