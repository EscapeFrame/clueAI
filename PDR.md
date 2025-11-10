# Gemini-CLI PDR (Project Development Record)

## 요약: Gemini 운영 규칙
| 카테고리 | 규칙 | 상세 내용 |
|---|---|---|
| **개발 방법론** | TDD | 실패하는 테스트를 먼저 작성 후 기능 코드 구현 |
| **아키텍처** | DDD 패키지 구조 | `controller`, `service`, `repository`, `model` 계층 준수 |
| **의존성** | 자율적 관리 | 필요 시 승인 없이 의존성 추가/변경/삭제 가능 |
| **버전 관리** | 커밋 컨벤션 | `type(issue_#): subject` 형식 준수. `type`은 `feat`, `fix` 등 표준 타입 사용. |
| **파일 접근** | 프로젝트 범위 제한 | `/Users/kimminje/PycharmProjects/clueAI` 디렉토리 내에서만 작업 |
| **문서화** | ERD 작성 | DB 관련 작업 시 Mermaid로 ERD 생성 |

---

## 2025년 11월 07일 - 작업 기록

### 작업: 테스트 환경 설정 및 첫 API 테스트
- **목표**: '수업 자료 추천/피드백' API의 첫 번째 기능으로 `GET /api/v1/materials/health` 엔드포인트를 TDD 방식으로 개발.
- **진행 상황**:
    1.  `FastAPI` 프레임워크 및 `uv` 사용 확인.
    2.  `pytest`, `httpx` 의존성 추가 시도.
    3.  DDD 구조에 따라 `app/controller/material` 등 디렉토리 생성.
    4.  기본 `main.py` FastAPI 앱 설정.
    5.  `tests/conftest.py`에 `TestClient` fixture 설정.
    6.  `tests/controller/material/test_material_controller.py`에 첫 번째 실패하는 테스트 작성.
- **문제 발생**: `pytest` 실행 시, 프로젝트의 가상환경(`.venv`)이 아닌 시스템의 전역 Python(Anaconda) 환경을 사용하여 `ModuleNotFoundError` 및 라이브러리 버전 충돌로 인한 `TypeError`가 지속적으로 발생.
- **시도된 해결책 (사용자 취소)**:
    1.  `pytest.ini` 파일을 생성하여 `pytest`의 `pythonpath`를 프로젝트 루트로 설정. (완료)
    2.  `uv venv` 명령으로 가상 환경을 표준화하고, `uv sync`로 `pyproject.toml` 및 `uv.lock`에 명시된 정확한 의존성을 가상 환경 내에 설치하여 환경 문제를 근본적으로 해결하려고 시도함.
- **전략 변경 (2025-10-27)**:
    - **사유**: 사용자가 환경 수정 제안(`uv venv && uv sync`)을 거부함. 이는 현재 내 접근 방식이 프로젝트의 실제 워크플로우와 맞지 않음을 시사.
    - **새로운 접근법**: 환경을 직접 수정하는 대신, 사용자에게 프로젝트의 표준 테스트 실행 명령어를 문의함. 이를 통해 기존 워크플로우를 존중하고 정확한 실행 방법을 학습하여 작업을 재개할 예정.

---

## 전체 규칙 상세

### 1. 개발 방법론: TDD (Test-Driven Development)
- 모든 개발 작업은 테스트 주도 개발 기법을 기반으로 진행합니다.
- 기능 구현 전에 실패하는 테스트를 먼저 작성하고, 그 테스트를 통과시키는 코드를 작성합니다.

### 2. 아키텍처: DDD (Domain-Driven Design) 패키지 구조
- 코드는 DDD 패키지 구조를 따릅니다.
- 파일 및 로직은 `controller`, `service`, `repository`, `model` 등 정해진 계층에 맞게 작성되어야 합니다.

### 3. 의존성 관리: 자율적 관리
- 작업에 필요하다고 판단될 경우, 별도의 승인 없이 의존성을 추가, 변경 또는 삭제할 수 있습니다.

### 4. 버전 관리
- **커밋 메시지 컨벤션**: `타입(이슈 번호): 내용` 형식을 따릅니다.
  - **타입**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore` 중 하나를 사용합니다.
- **커밋 준비**: 작업 완료 후, 컨벤션에 따라 제가 커밋 메시지 초안을 작성하고 제안합니다.

### 5. 파일 접근 범위: 프로젝트 디렉토리 제한
- 모든 파일 관련 작업(읽기, 쓰기, 생성, 수정)은 `/Users/kimminje/PycharmProjects/clueAI` 디렉토리 내에서만 수행합니다.

### 6. 문서화: ERD 작성
- 데이터베이스(DB) 관련 내용을 다룰 때, Mermaid 문법을 사용하여 ERD(Entity-Relationship Diagram)를 작성합니다.