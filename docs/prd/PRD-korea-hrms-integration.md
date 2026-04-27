# PRD — Korea HRMS Integration

> **Product Requirements Document**
> Version: **1.1** (Open Questions resolved)
> Status: **APPROVED FOR DEVELOPMENT**
> Last updated: 2026-04-26
> Owner: 총괄 PM (Claude Opus, this session)
> Sponsor: 사장님 (seojaehong)

---

## 1. Document Metadata

| Field | Value |
|-------|-------|
| Project Name | 한국 노동/세무 자동화 + Frappe HRMS 통합 |
| Repo (서버) | https://github.com/seojaehong/hrms |
| Repo (엔진) | (private) `_10_고객/_active/급여자동화` |
| Base Branch | `feature/korea-payroll-docs` |
| SoT Document Set | `docs/korea/01~10` + `README.md` (이 레포) |
| Adversarial Review Baseline | Codex session `b5e6xaiyi` (2026-04-25) |
| Active PRs | #7 (Korea integration API MVP) |

---

## 2. Executive Summary

본 프로젝트는 **현재 Excel + Python 기반으로 운영 중인 급여자동화 엔진**과 **신규 도입할 Frappe HRMS**를 결합하여, 사장님 회사의 모든 사업장(부평/올웨이즈샤브 외 다수)을 위한 **한국 노동법/세법 100% 정합 인사·급여 시스템**을 구축한다.

핵심 설계 결정:

1. **병렬 결합 아키텍처** — Frappe = HR 백본 (조직/직원/근태) / 급여자동화 엔진 = 한국 룰 엔진 (계산/명세서). 통합 단일 시스템 X.
2. **PII는 Frappe 외부** — 주민번호/계좌/외국인등록번호는 Frappe 어떤 필드(Password/Encrypted 포함)로도 저장 금지. privacy_broker 일회성 조회만.
3. **기존 운영 영향 0%** — 옵셔널 패턴 (visa_type=None, foreign_flat_tax=False 등 디폴트 = 기존 동작 유지). 부평/올샤 운영 중단 없음.
4. **SoT 분할** — `docs/korea/*` (한국 룰 명세, 사장님 권한) / `docs/integration/*` (양측 계약, PM 권한) / 코드 (각 작업자 권한)

---

## 3. Background & Context

### 3-1. 현재 자산
- **급여자동화 엔진** (Python + openpyxl + YAML)
  - 부평, 올웨이즈샤브 등 다수 사업장 운영 중
  - 4대보험/소득세/연말정산/퇴직금/일용직/외국인 룰 구현
  - privacy_broker (PII 처리) 검증 완료 (Privacy Architecture v2)
- **노동법/판례 KB**
  - 노동위 판정례 42k 전수 태깅 (8축)
  - BigCase 판례 17k 파싱
  - 최영우 노동법 3권 195개 챕터
  - 행정해석 671건 (294건 본문 수집)
- **기타**
  - Gmail 자동 브리핑 (AM/PM)
  - 옵시디언 Vault (참고/상담 일지)

### 3-2. 도입 배경
- 현재 엔진은 운영 정확하지만 **HR 전반 (조직도, 직원관리, 근태 UI) 부재**
- Frappe HRMS = 인도산 오픈소스 ERPNext 기반 HR 모듈. 조직/직원/근태/휴가 풍부
- 단, **한국 노동법/세법 미지원**. 직접 구현 시 메인테인 부담 큼
- 결론: **Frappe 의 HR 골격만 가져오고, 한국 룰은 기존 엔진 유지** = 병렬 결합

### 3-3. Codex 어댑서리얼 학습 (2026-04-25)
4 P1 결함 발견 → 모두 해소 (PR #6 머지):
1. `kr_resident_id` Data 평문 저장 → 필드 제거 + privacy_broker only
2. `kr_income_tax` 시그니처에 `withholding_rate` 누락 → 추가
3. 4대보험 base 통합 (`base`) → 보험별 분리 (pension_base / taxable_pay)
4. Hook 등록 시점 `before_save` (계산 후) → `before_validate` (계산 전)

---

## 4. Vision & Goals

### 4-1. Vision
**한국 노동법/세법을 1원 단위로 정확히 처리하면서, 글로벌 HR 표준(Frappe HRMS) UI/UX 위에서 운영 가능한 통합 인사 시스템.**

### 4-2. Goals (우선순위 순)

| # | Goal | 측정 지표 |
|---|------|----------|
| G1 | 기존 운영 사업장 영향 0% | 부평/올샤 4월 급여 1원 단위 동일성 |
| G2 | 한국 노동법/세법 100% 정합 | docs/korea/01~10 명세 vs 구현 갭 0건 |
| G3 | PII 외부 보관 (Frappe 무PII) | Frappe DB grep "주민" "resident" 결과 0건 |
| G4 | 신규 사업장 1주 내 추가 가능 | 사업장 마스터 설정 + YAML → 운영 |
| G5 | 운영 사고 0건 (1년 기준) | 1원 차이/세무신고 오류/PII 유출 |

### 4-3. Non-Goals (이 PRD 범위 외)
- ERPNext 의 회계/재고/CRM 모듈 사용
- 모바일 앱 (Phase 4 이후)
- 다국어 (한국어 only, 영어는 Frappe 디폴트만)
- Custom Frappe Framework 수정

---

## 5. Scope & Out-of-Scope

### 5-1. In Scope
- Frappe HRMS 한국 리전 설정
- Korea Salary Slip Extension (DocType)
- Korea Severance Slip (DocType)
- 직원/근태/휴가/사업장 master sync API (양방향)
- 급여 결과 import API (엔진 → Frappe)
- 04/05 import API (연말정산/퇴직금)
- privacy_broker 통합 (PII 일회성 조회)
- 한국 명세서 양식 (Print Format)
- 1개 사업장 파일럿 → 전 사업장 확대

### 5-2. Out of Scope
- ERPNext 의 다른 모듈 활용
- Frappe Framework Core 수정
- 신규 노동법 룰 발굴 (docs/korea/ 가 SoT — 사장님 결정)
- AI 기반 급여 예측/이상감지
- 다른 회사 (사장님 외) 사용

---

## 6. Stakeholders & Personas

### 6-1. Stakeholders
| Role | 책임 | 결정 권한 |
|------|------|----------|
| 사장님 (Sponsor) | 비즈니스 결정, SoT 명세 권한, 작업자 라우팅 | 최종 결재 |
| 총괄 PM (Claude Opus) | 양측 조율, git 모니터링, 결정자 | 양보 불가 라인 + 머지 (사장님 컨펌) |
| 로컬엔진 작업자 | 한국 룰 엔진 메인테이너 | 코드 구현 자율 |
| 서버개발자 (Hermes) | Frappe HRMS 확장 | 코드 구현 자율 |

### 6-2. Personas (사용자)
- **인사담당자** (사장님 회사) — 매월 급여 처리, 4대보험 신고, 연말정산
- **점장/매장 책임자** — 직원 등록, 근태 입력, 명세서 출력
- **세무사** (외부) — 매월 세무대장 수신, 연말정산 보조
- **공단/세무서** (간접) — 신고서/명세서 수신

---

## 7. Use Cases

### UC-1. 매월 급여 처리 (반복)
1. 점장이 Frappe 에 근태 입력
2. PM 또는 자동화가 매월 25일 트리거
3. Frappe → 엔진: 직원 마스터 + 근태 export (REST)
4. 엔진: privacy_broker 통해 PII 일회성 조회
5. 엔진: 4대보험 + 소득세 + 비과세 적용 → 결과 JSON
6. 엔진 → Frappe: import_payroll_result API
7. Frappe: Korea Salary Slip 생성 + 명세서 PDF
8. 사장님: Frappe Dashboard 에서 사업장별 합계 확인
9. 세무사 발송: 자동 메일

### UC-2. 신규 사업장 추가
1. 사장님: Frappe 에 Company/Branch 생성
2. PM: 사업장 YAML 생성 (`config/{사업장}.yaml`)
3. Frappe → 엔진: 사업장 마스터 sync API
4. 엔진: 사업장별 4대보험 적용 룰 설정
5. 첫 달 1원 단위 검증 후 정식 운영

### UC-3. 연말정산 (연 1회)
1. 1~2월: Frappe 에 직원별 공제증빙 입력 또는 import
2. 엔진: 7단계 계산 (Method A/B 비교)
3. 엔진 → Frappe: import_year_end_settlement_result API
4. Frappe: 결정세액 / 차감징수세액 표시
5. 2월 급여에 반영

### UC-4. 퇴직금 (수시)
1. 점장: Frappe 에 퇴사일 입력
2. 엔진: 평균임금 + 근속연수 + 퇴직소득세 계산
3. 엔진 → Frappe: import_severance_result API
4. Frappe: Korea Severance Slip 생성

### UC-5. 외국인 직원 (수시)
1. 점장: Frappe 에 입사 등록 + visa_type 입력
2. 엔진: 비자별 4대보험 + 19% 단일세율 옵션 적용
3. (이하 UC-1 동일)

---

## 8. Functional Requirements (FR)

> 양측 계약(`docs/integration/frappe-side-contract.md`, `docs/integration/engine-side-contract.md`)을 정식 규격으로 본다. 본 절은 우선순위/범위 명시.

### FR-1. Frappe Custom DocType (Phase 1)
- **Korea Salary Slip Extension** (Salary Slip 확장)
  - 한국 항목: 과세/비과세/4대보험/소득세/실지급액
  - 외부 엔진 결과 import 받음
- **Korea Severance Slip** (별도 DocType)
  - 평균임금 / 근속연수 / 퇴직금 / 퇴직소득세 / 실지급액
- **Korea Calc Reference** (감사용 캐시)
  - 외부 엔진 호출 결과 + timestamp + run_id

### FR-2. Frappe API Endpoints (Phase 1)
- `export_employee_master` — 직원 마스터 (PII 차단)
- `export_time_and_leave` — 근태/휴가 export
- `sync_worksite` — 사업장 마스터 양방향 sync
- `import_payroll_result` — 급여 결과 import (idempotent)
- `import_year_end_settlement_result` — 04 연말정산 결과 (Phase 2)
- `import_severance_result` — 05 퇴직금 결과 (Phase 2)

### FR-3. 엔진 측 Interface (Phase 1)
- `LocationConfig` JSON Schema (사업장 YAML → JSON)
- `EmployeeRecord` 통일 dict 출력
- 25 REST endpoint 후보 (engine-side-contract §3 참조)
- privacy_broker 일회성 조회 (`get_pii(employee_id, field)`)
- Frappe push 인터페이스 (idempotency + 멱등키)

### FR-4. Hook (Frappe → 엔진 트리거) (Phase 1)
- `before_validate` on Salary Slip → 한국 데이터 로드
- `validate` on Salary Slip → net_pay 음수 검증
- 자동화: Payroll Entry 생성 시 Salary Slip 자동 호출

### FR-5. 한국 명세서 양식 (Phase 1)
- Korean Print Format (HTML/PDF)
- 4대보험 breakdown
- 비과세 식대/자가운전보조금 명시
- 회사 도장 (옵션)

### FR-6. 4대보험 신고서 (Phase 2)
- 취득신고서 / 상실신고서 (현재 엔진이 생성)
- 보수총액 정산 (현재 엔진이 생성)
- Frappe 에서 신고서 PDF 다운로드 가능

### FR-7. 한국화 UI (Phase 3)
- 메뉴 한국어 라벨
- 직원 입력 폼 한국 필드 추가 (visa_type, dependents 등)
- Dashboard (사업장별/월별 합계)

### FR-8. CI/CD (Phase 1 시작)
- GitHub Actions
- Frappe 서버: lint + test
- 엔진: pytest + 회귀

### FR-9. 운영 인프라 (Phase 4)
- 도메인 + HTTPS (사장님 도메인)
- Cloudflare Tunnel + Access (Zero Trust 인증 게이팅)
- 백업 (DB + 파일)
- 모니터링 (에러 알림)

---

## 9. Non-Functional Requirements (NFR)

### NFR-1. 정확성 (Correctness)
- **1원 단위 정확** — 모든 급여 계산 결과는 1원도 차이 없음
- 회귀 테스트: 기존 사업장 1개월치 직원 전체 1원 단위 동일성

### NFR-2. 보안 (Security)
- **PII 금지** — Frappe DB 어떤 필드(Password/Encrypted 포함)에도 주민번호/계좌/외국인등록번호 저장 금지
- privacy_broker 일회성 조회 + 감사 로그
- HTTPS only (운영)
- Cloudflare Access 인증 게이팅 (운영)

### NFR-3. 운영 영향 0% (Operational Continuity)
- 기존 사업장 (부평/올샤 등) 운영 중단 없이 도입
- 엔진 코드 변경은 옵셔널 패턴 (디폴트 = 기존 동작)
- Frappe 도입은 점진적 (1 사업장 파일럿 → 확대)

### NFR-4. 가용성 (Availability)
- 운영 시간 09:00~18:00 가용 (KR 시간)
- 매월 25~31일 (급여 처리 기간) 다운타임 0
- 백업 일 1회

### NFR-5. 성능 (Performance)
- 1 사업장 50명 급여 계산: < 30초
- API 응답: P95 < 2초
- 신고서 생성: < 60초

### NFR-6. 감사 (Auditability)
- 모든 API 호출 로그 (호출자/시점/payload 요약)
- privacy_broker 조회 로그 별도 보관 (개인정보보호법)
- Salary Slip 변경 이력 (Frappe 기본 audit)

### NFR-7. 메인테인 (Maintainability)
- docs/korea/ SoT 명세 우선 (코드는 명세 따름)
- 양측 계약 (docs/integration/) 변경 시 PM 결재
- Frappe upstream 업데이트 추적 (월 1회)

---

## 10. Architecture (요약)

```
[사장님]
   │
   ├── Frappe HRMS (HR 백본)             [급여자동화 엔진]
   │     ├── Employee                       ├── insurance.py
   │     ├── Attendance                     ├── payroll_calc.py
   │     ├── Leave                          ├── severance.py
   │     ├── Korea Salary Slip ◀──┐         ├── minimum_wage.py
   │     └── Korea Severance Slip │         ├── daily_worker_tax.py
   │                              │         └── [...신규 모듈]
   │                              │              │
   │     [Korea Integration API]  │              │
   │     ├── export_employee  ◀───┼──────────────┘ (REST)
   │     ├── export_time      ◀───┼─────── (REST)
   │     ├── sync_worksite    ◀───┼─────── (REST 양방향)
   │     ├── import_payroll   ◀───┴─── (REST 결과 push)
   │     ├── import_yearend   ◀───── (REST)
   │     └── import_severance ◀───── (REST)
   │
   └── privacy_broker (PII 일회성 조회)
         ├── 주민번호 (encrypted store)
         ├── 계좌번호
         ├── 외국인등록번호
         └── 감사 로그
```

원칙:
- Frappe = HR 마스터 / 엔진 = 룰 엔진
- 양방향 sync 는 사업장 마스터만 (나머지는 단방향)
- PII = Frappe 외부 (privacy_broker only)
- 결과 결합 = Frappe 측이 import (엔진 측이 push)

---

## 11. Interface Contracts

본 PRD 의 인터페이스 권위 문서:
- 서버측: [`docs/integration/frappe-side-contract.md`](../integration/frappe-side-contract.md)
- 엔진측: [`docs/integration/engine-side-contract.md`](../integration/engine-side-contract.md)

본 문서는 PRD level 만 명시. 라인-by-라인 명세는 위 두 파일 참조.

---

## 12. Roles & Responsibilities (3자 + 사장님)

### 12-1. 사장님 (Sponsor / SoT 권한자)
**책임**:
- 비즈니스 우선순위 결정 (사업장 파일럿 시점, 운영 적용 게이트)
- `docs/korea/*` SoT 명세 권한 (변경 시 사장님 컨펌 필수)
- 작업자 메시지 라우팅 (PM ↔ 양측 작업자 통신 중계)
- 최종 결재 (PR 머지, 운영 적용)
- 비용/예산 관리

**금지/주의**:
- 직접 PR 머지 (PM 검증 후 권장. 단 권한은 사장님)
- 양측 작업자 직접 git 명령 위임 (PM 거치는 게 안전)

### 12-2. 총괄 PM (Claude Opus, this session)
**책임**:
- 양측 작업 조율 / 인터페이스 계약 통합
- git 직접 모니터링 (gh CLI 으로 PR/브랜치/커밋 검증)
- 결정자 (PII 경계, 머지 순서, 우선순위) — 사장님 컨펌 필요시 컨펌 받음
- 검증 도구 활용 (Codex 어댑서리얼, gap-detector)
- 양측 작업자 회신 지시문 작성 (사장님이 전달)
- 정기 회고 (주 1회 금요일)
- 위험 관리 / 미해결 이슈 추적

**산출물**:
- 양측 회신 지시문
- PR 검토 보고서
- 머지 결정 + 실행 (사장님 컨펌 후)
- PRD 갱신
- Codex/gap-detector 분석 보고서

**금지/주의**:
- 자율 머지 — 사장님 컨펌 필수 (지난 사이클 학습)
- 직접 코드 작성 — 작업자 영역 (단, 문서 작성/cherry-pick 정도는 OK)
- `docs/korea/*` 직접 수정 — 사장님 SoT
- 양측 작업자에게 메시지 직접 전송 — 사장님 라우터 거침

### 12-3. 로컬엔진 작업자 (급여자동화 메인테이너)
**책임**:
- 한국 노동법/세법 룰 엔진 (4대보험, 소득세, 연말정산, 퇴직금, 일용직, 외국인)
- 1원 단위 정확한 계산 (CLAUDE.md 룰 준수)
- privacy_broker 통합 (PII 처리)
- 기존 운영 사업장 (부평/올샤 등) 운영 책임
- engine-side-contract 구현 (FastAPI 또는 CLI 기반)
- 회귀/단위 테스트 유지

**산출물**:
- 급여 계산 결과 JSON (Frappe import 용)
- 신규 코드 모듈 (insurance.py, minimum_wage.py 등)
- 04/05 export 스키마 + 구현 코드
- docs/integration/engine-side-contract.md
- 회귀 테스트 + pytest

**금지/주의**:
- Frappe 내부 코드 수정 (서버측 영역)
- `docs/korea/*` 명세 직접 수정 (사장님 SoT)
- 기존 운영 영향 (옵셔널 패턴 유지)
- main 브랜치 직접 commit 시 회귀 테스트 + 1원 단위 검증 자료 첨부 필수
- privacy_broker 우회 (직접 PII 접근 금지)

### 12-4. 서버개발자 (Hermes)
**책임**:
- Frappe HRMS 확장 (Custom DocType, API, Hook, Print Format)
- 한국화 UI (locale, 메뉴) — Phase 3
- frappe-side-contract 구현
- 인프라 (Cloudflare Tunnel, 도메인, CI/CD)
- 양측 통신 (REST API)
- Frappe upstream 업데이트 추적

**산출물**:
- hrms/api/korea_integration.py (PR #7 기준)
- Custom DocType 메타 (Korea Salary Slip Extension, Korea Severance Slip)
- Salary Component Formula (docs/korea/10 fix 후)
- Migration scripts
- Print Format
- Test suite (pytest 또는 Frappe TestCase)
- docs/integration/frappe-side-contract.md

**금지/주의**:
- `docs/korea/*` 명세 직접 수정 (사장님 SoT)
- 로컬 엔진 코드 수정 (로컬엔진 영역)
- PR base 위반 (반드시 `feature/korea-payroll-docs`)
- PM 결정 무시 (특히 PII 경계 — 양보 불가 라인)
- Force push 또는 머지된 PR 의 브랜치 수정

---

## 13. Decision Authority Matrix

| 결정 종류 | 1차 권한 | 2차 컨펌 | 흐름 |
|-----------|---------|---------|------|
| 코드 구현 방법 | 작업자 | - | 자율 |
| PR 생성 | 작업자 | - | 자율 (작업자 push) |
| PR base 브랜치 결정 | PM | - | PR 생성 전 PM 안내 |
| **PR 머지** | PM | **사장님 컨펌** | 작업자 push → PM 검토 → 사장님 컨펌 → PM 머지 |
| 양측 계약 변경 (`docs/integration/`) | PM | 사장님 통지 | PM 결정 |
| **`docs/korea/*` 변경** | **사장님** | - | 사장님 컨펌 후 작업자 |
| **PII 경계** | **PM 양보 불가** | - | PM 결정 |
| 운영 적용 (사업장 파일럿) | 사장님 | PM 검증 | 사장님 결정 |
| 비용/예산 | 사장님 | - | 사장님 결정 |
| Codex 어댑서리얼 실행 | PM | - | 자율 |
| 머지된 PR 의 revert | PM | **사장님 컨펌 필수** | revert 영향 큼 |
| 브랜치 삭제 (dangling) | PM | 사장님 통지 | PM 진행 |
| 다음 사이클 우선순위 | PM | 사장님 컨펌 | PM 추천 + 사장님 결정 |

---

## 14. Communication Protocol

### 14-1. 통신 흐름

```
[사장님]
   │  ▲
   │  │ (메시지 라우팅)
   ▼  │
[총괄 PM (Claude Opus)] ─── 직접 ───▶ [Git (SoT)]
                                          ▲
                                          │ (push, PR)
[로컬엔진 작업자] ─────────────────────────┤
[서버개발자 (Hermes)] ─────────────────────┘
```

**핵심 규칙**:
- 작업자 ↔ PM 직접 통신 X (사장님 라우터)
- PM ↔ Git 직접 (gh CLI)
- 작업자 ↔ Git 직접 (push, PR)
- 사장님 = 비동기 메시지 중계자

### 14-2. 작업자 → PM 보고 패턴 (사장님 통과)
표준 형식:
1. **결론** (1-2줄)
2. **근거** (커밋 SHA, PR 번호, 변경 파일, 검증 결과)
3. **리스크** (있으면)
4. **다음 행동** (제안)

### 14-3. PM → 작업자 회신 패턴 (사장님 통과)
표준 형식:
1. **평가** (✅ APPROVED / ⚠ 조건부 / ❌ 반려)
2. **수정 사항** (필요시, 라인-by-라인)
3. **PR 생성/처리 지시** (브랜치명, base, title, body 형식)
4. **금지 사항**
5. **완료 후 보고 형식**

### 14-4. 정기 PM 정리 세션
- 주기: 매주 금요일
- 내용: 사이클 회고 + 다음 주 우선순위 + 위험 검토
- 산출물: PRD 의 "변경 이력" 갱신 + 다음 주 행동 plan

---

## 15. Phasing & Roadmap

### Phase 1 — 인터페이스 확정 + Frappe API MVP (현재) ✅ 진행 중
- ✅ 양측 계약 작성 + 머지 (PR #3, #4)
- ✅ docs/korea/10 P1 4건 fix (PR #6)
- 🔄 hrms/api/korea_integration.py MVP (PR #7 — 검토 중)
- ⏸ 사업장 마스터 sync API
- ⏸ 04/05 import API 구현 (계약은 있음)

**완료 게이트**:
- PR #7 머지
- 사업장 마스터 양방향 sync 작동
- 04/05 import API 1건 동작 검증

### Phase 2 — Custom DocType + 부평/올샤 파일럿
- Korea Salary Slip Extension DocType 구현
- Korea Severance Slip DocType 구현
- Hook (before_validate, on_calculate, validate) 등록
- Salary Component Formula 등록
- Korea Tax Table / Korea Insurance Rates DocType
- **첫 파일럿: 부평 사업장 (Week 1-4)**
  - 1개월 parallel run (기존 엔진 + Frappe 동시)
  - 1원 단위 동일성 검증
- **두 번째 파일럿: 올웨이즈샤브 (Week 2-5, 1주 시차)**
  - 동일 검증 패턴
  - 부평 1주 검증 결과 안정 후 진입

**완료 게이트**:
- 두 파일럿 사업장 1개월치 1원 단위 동일성 100%
- PII 감사 로그 정상 작동
- 백업/복구 검증

### Phase 3 — 한국화 UI + 추가 사업장 확대
- 메뉴/필드 한국어 라벨
- Dashboard (사업장별/월별 합계)
- 사업장 2~3개 확대 적용
- 신고서 PDF 다운로드 기능

### Phase 4 — 운영 인프라 + 전 사업장 적용
- 도메인 + HTTPS + Cloudflare Access
- 모니터링 + 알림
- 백업/복구 자동화
- 전 사업장 점진 마이그레이션
- 기존 엔진 = 룰 엔진으로만 전환

---

## 16. Milestones & Gates

| Milestone | 완료 조건 | 게이트 (다음 단계 진입) |
|-----------|----------|----------------------|
| M1: 인터페이스 확정 | 양측 계약 머지 + Codex 어댑서리얼 P1 = 0 | ✅ 통과 (2026-04-25) |
| M2: API MVP | PR #7 머지 + 04/05 작동 | 🔄 진행 중 |
| M3: DocType + Hook | Salary Slip 자동 생성 작동 | ⏸ |
| M4: 1 사업장 파일럿 | parallel run 1원 동일성 100% | ⏸ |
| M5: 한국화 UI | 메뉴 한국어 + Dashboard | ⏸ |
| M6: 전 사업장 운영 | 모든 사업장 Frappe 마이그레이션 | ⏸ |

**전환 게이트** (절대 통과 조건):
1. 1원 단위 동일성 (1개월 parallel run)
2. PII 감사 로그 작동
3. 백업/복구 검증
4. 운영자(사장님) 컨펌

→ 위 4건 모두 통과 전엔 실데이터 운영 진입 금지.

---

## 17. Acceptance Criteria

### Phase 1 (현재) 완료 조건
- [ ] PR #7 머지 (Korea integration API MVP)
- [ ] 사업장 마스터 sync API 동작 검증
- [ ] 04/05 import API 1건 동작 검증
- [ ] frappe-side-contract.md ↔ korea_integration.py 정량 갭 0건 (gap-detector)

### 1 사업장 파일럿 (Phase 2 게이트)
- [ ] parallel run 1개월치 1원 단위 동일성 100% (직원 전체)
- [ ] PII 감사 로그 모든 호출 기록
- [ ] privacy_broker 일회성 조회 작동
- [ ] 명세서 PDF 한국 양식 출력 정상
- [ ] 4대보험 신고서 (취득/상실) 정상 생성

### 전 사업장 운영 (Phase 4 게이트)
- [ ] 6개월 무사고 운영 (1원 차이/세무신고 오류/PII 유출 0건)
- [ ] 모든 사업장 마이그레이션 완료
- [ ] 백업/복구 정기 테스트 통과
- [ ] 운영자(사장님) 자율 운영 가능 (PM 의존도 ↓)

---

## 18. Risk Register

| ID | 위험 | 확률 | 영향 | 완화 |
|----|------|------|------|------|
| R1 | 비동기 통신 충돌 (작업자 ↔ PM) | 중 | 중 | PM 자동 머지 X. 사장님 컨펌 패턴. 학습됨 (PR #6 사이클) |
| R2 | Frappe upstream 변경으로 한국화 깨짐 | 중 | 큼 | 월 1회 dry-run merge. 충돌 시 즉시 PM 알림 |
| R3 | PII 누출 (Frappe 또는 privacy_broker) | 낮 | 매우 큼 | 양보 불가 라인. Codex 어댑서리얼 정기 (분기 1회). 감사 로그 |
| R4 | 1원 단위 차이 (운영 적용 후) | 중 | 큼 | parallel run 게이트. 첫 달 1원 검증 후 적용. 옵셔널 패턴 |
| R5 | docs/korea/ 미세 결함 (Codex 미발견) | 중 | 중 | 분기 1회 어댑서리얼 + gap-detector |
| R6 | 작업자 1명 부재 (휴가/아웃 등) | 낮 | 큼 | 산출물 = 코드 + 문서. PM 이 산출물 기반 인계 가능 |
| R7 | PM (Claude Opus) context 한계 | 중 | 중 | 정기 정리 세션 + 메모리 시스템 활용. 핵심 결정은 PRD 갱신 |
| R8 | 비용 (Claude 토큰) 누적 | 중 | 작 | 효율 운영 (단순 결정 자율 / 큰 결정 컨펌) |
| R9 | dangling 브랜치 누적 | 중 | 작 | 정기 PM 정리 (주 1회) — 삭제/처리 결정 |
| R10 | 사장님 부재 시 작업자 자율 진행 | 중 | 큼 | PRD = 1차 가이드. PM 결정 위임 룰 명시 |

---

## 19. Resolved Decisions (formerly Open Questions)

본 PRD v1.1 시점 모두 결정 완료. 사장님 OQ1 직접 결정, OQ2~OQ7 PM 자율 결정 (사장님 위임).

| ID | 질문 | **결정** | 결정자 | 근거 |
|----|------|---------|--------|------|
| **OQ1** | 첫 파일럿 사업장은? | **부평 + 올웨이즈샤브 둘 다.** 부평 Week 1-4 → 올샤 Week 2-5 (1주 시차) | **사장님** | 양 사업장 다 검증 = 더 강력한 안전망. 1주 시차 = 부평 결과 보고 올샤 보정 가능 |
| **OQ2** | privacy_broker 외부 store 위치? | **기존 privacy_broker 구조 유지** (Privacy Architecture v2 검증 완료 자산). Phase 4 운영 진입 시 cloud KMS 마이그레이션 검토 | PM | 검증된 자산 우선. 클라우드 KMS는 운영 비용+락인 부담. 현재 구조로 양보 불가 라인 충족 |
| **OQ3** | 엔진 측 API 방식? | **FastAPI 얇은 REST 래퍼 우선 (Phase 1).** Celery/큐 기반은 Phase 4 (전 사업장 동시 처리 시) 검토 | PM | engine-side-contract.md 추천 일치. 동기 호출이 1~3 사업장 규모에 충분. 단순 우선 |
| **OQ4** | Frappe 인증? | **Phase 1~3 = Frappe 자체 인증 (간소).** Phase 4 = 사내 SSO 검토 — 네이버웍스(winhr.co.kr) SAML 우선 검토, 미지원 시 Google Workspace fallback | PM | 초기 단계는 단순. 운영 확대 시 SSO 도입. 사장님 도메인이 네이버웍스라 그쪽 우선 |
| **OQ5** | dangling 브랜치 처리? | **bcfa2d5f (PM 반려안 — Data→Password) = 삭제.** **514638098 (PII 강화안 — 옵션 B) = 별도 PR 머지** (PR 번호는 다음 사이클에서 할당) | PM | 반려안은 무용. 강화안은 의미 있는 보강 (운영 시 무지성 변경 방지) |
| **OQ6** | PR #7 누락 항목? | **별도 PR로 분리.** 순서: PR #7 (현 MVP) 머지 → PR (사업장 sync) → PR (04/05 import) | PM | 작은 PR이 review 효율 ↑. PR #7 검증 완료 상태에서 추가 변경은 새 검증 필요 |
| **OQ7** | 정기 회고 일정? | **매주 금요일 16:00 KR (30분).** 내용: 주간 사이클 회고 + 다음 주 우선순위 + 위험 검토. 사장님 부재 시 PM 단독 진행 + 산출물 보고 | PM | 금요일 = 주말 진입 전 정리. 16:00 = 노무 업무 마감 후. 30분 = 사장님 부담 낮음 |

### 결정 영향 요약 (Action Items)

- **즉시 액션**:
  1. bcfa2d5f 브랜치 삭제 (PM 진행)
  2. 514638098 별도 PR 생성 지시 (Hermes)
  3. PR #7 머지 후 사업장 sync PR / 04/05 import PR 순차 진행
  4. 첫 회고: 다음 금요일 (2026-05-01) 16:00 KR

- **Phase 2 진입 시**:
  - 부평 + 올샤 1주 시차 파일럿 plan 확정
  - parallel run 인프라 준비 (기존 엔진 + Frappe 동시 호출)

- **Phase 4 진입 시**:
  - 네이버웍스 SAML 가능성 조사
  - cloud KMS 마이그레이션 검토 (privacy_broker)
  - Celery/큐 도입 검토

---

## 20. Glossary

- **SoT** — Single Source of Truth. 단일 진실의 원천
- **PII** — Personally Identifiable Information. 개인식별정보 (주민번호 등)
- **privacy_broker** — PII 일회성 조회 + 감사 로그 시스템 (Frappe 외부)
- **양측 계약** — frappe-side-contract.md + engine-side-contract.md
- **옵셔널 패턴** — 신규 파라미터 디폴트 = None/False = 기존 동작 유지
- **parallel run** — 기존 엔진 + 신규 시스템 동시 실행 + 결과 비교
- **Codex 어댑서리얼** — Codex (다른 LLM) 가 설계 결함을 도전적으로 검증
- **gap-detector** — bkit 의 명세 ↔ 구현 정량 갭 측정 도구

---

## 21. Appendix: Change Log

| Version | Date | 작성자 | 변경 |
|---------|------|--------|------|
| 1.0 | 2026-04-26 | 총괄 PM | 초안 작성 (Phase 1 진행 중 시점) |
| **1.1** | **2026-04-26** | **총괄 PM** | **OQ1~OQ7 모두 결정 완료. 부평+올샤 파일럿 plan 명시. PDF 변환** |

---

## 22. Approval

| Role | Approver | Date | Signature |
|------|----------|------|-----------|
| Sponsor | 사장님 (seojaehong) | 2026-04-26 | OQ1 결정 + OQ2~OQ7 PM 위임 = 묵시 승인 |
| 총괄 PM | Claude Opus | 2026-04-26 | v1.1 결정 완료 |

---

**END OF PRD**
