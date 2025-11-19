# clueAI
MMRAG를 기반 AI 시스템.
clueAI는 CLUE서비스에 있는 선생님들의 수업 자료를 바탕으로 내용을 학습하고, 학습 데이터를 바탕으로 학생들에게 답변을 만들어주는 LanChain&MMRAG 시스템 입니다.


## 목표
1. RAG처럼 데이터를 기반으로 답변을 만든다.
2. MuRAG와 같이 모델은 텍스트와이미지를 동시에 검색하여 작업을 수행하도록 설계한다.
3. 다수의 데이터를 빠른 시간 내에 답변한다.
4. 다수의 트래픽을 버틸수 있도록 설계한다.
5. 부적합한 데이터를 필터링하고, 정화한 요청만 받도록 보안성 향상

## 로컬 개발 환경 설정

### 사전 요구사항
- Python 3.11 이상
- PostgreSQL 데이터베이스
- Google Generative AI API 키

### 설치 및 실행

1. 저장소 클론
```bash
git clone <repository-url>
cd clueAI
```

2. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 실제 값 입력
```

3. 의존성 설치 및 실행
```bash
chmod +x run.sh
./run.sh
```

또는 수동으로:
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## 배포

이 프로젝트는 GitHub Actions를 통한 자동 배포를 지원합니다.

- `develop` 브랜치에 push하면 자동으로 EC2에 배포됩니다.
- Docker 및 Docker Compose를 사용하여 컨테이너화된 환경에서 실행됩니다.

상세한 배포 가이드는 [DEPLOYMENT.md](./DEPLOYMENT.md)를 참조하세요.

## API 엔드포인트

- `GET /`: 헬스 체크
- `GET /health`: 상세 헬스 체크 (HealthCheck 라우터)