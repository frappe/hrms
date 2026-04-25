# Engine Interface Specification

> 급여자동화 엔진의 입출력 형식, REST API 후보, PII 경계 정리
> 작성일: 2026-04-25
> 목적: Frappe HR SaaS 전환 시 현 엔진의 재사용 가능 범위 식별

---

## 1. 입력 형식 (Input Schema)

### 1-1. 사업장 설정 (YAML → LocationConfig)

```yaml
# config/{사업장명}.yaml → LocationConfig dataclass
```

```jsonschema
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "LocationConfig",
  "type": "object",
  "required": ["company", "location"],
  "properties": {
    "company":      { "type": "string", "description": "회사명 (법인명)" },
    "location":     { "type": "string", "description": "지점명" },
    "paths": {
      "type": "object",
      "properties": {
        "base":          { "type": "string", "description": "급여파일 루트 경로 (연도/월 하위)" },
        "templates_dir": { "type": "string", "description": "신고서 템플릿 디렉토리" }
      }
    },
    "files": {
      "type": "object",
      "properties": {
        "prefix": { "type": "string", "description": "엑셀 파일명 접두어 (예: '쿠우쿠우_상봉_')" }
      }
    },
    "reader_type": {
      "type": "string",
      "enum": ["type_a", "type_b", "type_c", "generic", "jecheon"],
      "description": "사업장 엑셀 구조 유형"
    },
    "workers": {
      "type": "object",
      "properties": {
        "alias_map": {
          "type": "object",
          "description": "근태계산 이름 ↔ 정직원 이름 매핑",
          "additionalProperties": { "type": "string" }
        }
      }
    },
    "reports": {
      "type": "object",
      "properties": {
        "job_code":          { "type": "string", "default": "532" },
        "standard_hours":    { "type": "string", "default": "40" },
        "contract_type":     { "type": "string", "default": "2" },
        "default_bosu":      { "type": "integer", "default": 1800000, "description": "기본 보수월액" },
        "loss_reason_code":  { "type": "string", "default": "11" },
        "loss_detail_code":  { "type": "string", "default": "01다른 직장으로..." }
      }
    },
    "sheets": {
      "type": "object",
      "description": "엑셀 시트명 override",
      "properties": {
        "kitchen":    { "type": "string", "default": "주방직원" },
        "hall":       { "type": "string", "default": "홀직원" },
        "attendance": { "type": "string", "default": "근태계산" },
        "regular":    { "type": "string", "default": "정직원" }
      }
    },
    "wage_ledger": {
      "type": "object",
      "description": "임금대장 컬럼 좌표 (Master DB/보수총액용)",
      "properties": {
        "sheet":      { "type": "string" },
        "data_row":   { "type": "integer" },
        "name":       { "type": "integer", "description": "이름 열 번호" },
        "jumin":      { "type": "integer", "description": "주민번호 열" },
        "hire_date":  { "type": "integer" },
        "quit_date":  { "type": "integer" },
        "total_wage": { "type": "integer", "description": "임금총액 열" },
        "tax":        { "type": "integer", "description": "소득세 열" }
      }
    },
    "staff_source": {
      "type": "object",
      "description": "직원현황 시트 컬럼 좌표 (type_b/c용)",
      "properties": {
        "sheet":     { "type": "string" },
        "data_row":  { "type": "integer" },
        "name":      { "type": "integer" },
        "jumin":     { "type": "integer" },
        "hire_date": { "type": "integer" },
        "quit_date": { "type": "integer" },
        "salary":    { "type": "integer" },
        "insurance": { "type": "integer" },
        "bank":      { "type": "integer" },
        "account":   { "type": "integer" }
      }
    },
    "generic_reader": {
      "type": "object",
      "description": "범용 리더 설정 (신규 사업장 코드 수정 불필요)",
      "properties": {
        "sheet":     { "type": "string" },
        "data_row":  { "type": "integer" },
        "columns":   { "type": "object", "description": "컬럼명 → 열 번호 매핑" },
        "defaults":  { "type": "object" },
        "exclude_rules": { "type": "array" }
      }
    },
    "tax_split": {
      "type": "object",
      "description": "세무분리 설정 (직원/파트 분리, win32com)"
    },
    "insurance_from_ledger": {
      "type": "object",
      "description": "임금대장 기반 4대보험 판단"
    }
  }
}
```

### 1-2. 직원 데이터 (Excel → dict)

모든 reader (kitchen, hall, staff_source, part_source, generic)가 동일한 키 구조로 반환:

```jsonschema
{
  "title": "EmployeeRecord",
  "type": "object",
  "properties": {
    "성명":     { "type": "string" },
    "파트":     { "type": "string", "description": "주방/홀/파트 등" },
    "근무타입": { "type": "string" },
    "직급":     { "type": "string" },
    "주민번호": { "type": "string", "description": "PII — 13자리 (하이픈 포함 가능)" },
    "은행명":   { "type": "string" },
    "계좌번호": { "type": "string", "description": "PII" },
    "연락처":   { "type": "string", "description": "PII" },
    "입사일":   { "type": ["string","null"], "format": "date" },
    "퇴사일":   { "type": ["string","null"], "format": "date" },
    "4대보험":  { "type": "string", "description": "유/무/X/F/미가입/프리랜서" },
    "급여":     { "type": "integer", "description": "월 급여 (원)" },
    "추가금":   { "type": "integer", "default": 0 },
    "공제금":   { "type": "integer", "default": 0 },
    "비고":     { "type": "string" }
  }
}
```

### 1-3. 파이프라인 실행 인자

| Step | 필수 인자 | 선택 인자 |
|------|----------|----------|
| Step 0 (세무분리) | `site_key`, `year`, `month` | `password` |
| Step 1 (파일 복사) | `site_key`, `year`, `month` | — |
| Step 2 (근태 반영) | `site_key`, `year`, `month` | — |
| Step 3 (취득신고) | `site_key`, `year`, `month` | `bosu`, `names` |
| Step 4 (상실신고) | `site_key`, `year`, `month` | `names` |
| Step 5 (일용직) | `site_key`, `year`, `month` | — |

### 1-4. Privacy Broker CLI 인자

```
python privacy_broker.py <command> \
  --site-key <key> \
  --year <YYYY> --month <MM> \
  [--employee-token emp_XXXX] \
  [--bosu <int>] \
  [--names name1 name2 ...] \
  [--json-data '{}']
```

---

## 2. 출력 형식 (Output Schema)

### 2-1. 파이프라인 Step 결과

모든 Step은 `dict`를 반환. Privacy Broker는 이를 JSON 정화 후 stdout 출력.

```jsonschema
{
  "title": "StepResult",
  "type": "object",
  "required": ["status"],
  "properties": {
    "ok":       { "type": "boolean" },
    "status":   { "type": "string", "enum": ["success", "skipped", "error", "split", "already_split", "no_parts"] },
    "job_id":   { "type": "string", "pattern": "^job-\\d{8}-\\d{6}$" },
    "code":     { "type": "string", "description": "에러 코드 (실패 시)" },
    "message":  { "type": "string" },
    "file":     { "type": "string", "description": "생성/수정된 파일 경로 (정화됨)" },
    "emp_count":  { "type": "integer" },
    "part_count": { "type": "integer" },
    "daily_workers": {
      "type": "object",
      "properties": {
        "count":      { "type": "integer" },
        "biz_income": { "type": "integer", "description": "120만 초과 사업소득 전환 인원" },
        "report":     { "type": "boolean", "description": "근로내용확인신고서 생성 여부" }
      }
    }
  }
}
```

### 2-2. 급여 요약 (payroll-summary)

```jsonschema
{
  "title": "PayrollSummary",
  "type": "object",
  "properties": {
    "ok":        { "type": "boolean" },
    "site_key":  { "type": "string" },
    "year":      { "type": "integer" },
    "month":     { "type": "integer" },
    "headcount": { "type": "integer", "description": "총 인원 (직원+파트)" },
    "employees": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "token":      { "type": "string", "description": "emp_XXXX (비식별 ID)" },
          "name_masked":{ "type": "string", "description": "김OO (마스킹)" },
          "hire_month":  { "type": "string", "description": "YYYY-MM" },
          "is_insured": { "type": "boolean" },
          "is_new":     { "type": "boolean", "description": "당월 입사자" },
          "is_leaving": { "type": "boolean", "description": "당월 퇴사자" },
          "gross_pay":  { "type": "integer" },
          "insurance_total": { "type": "integer" },
          "tax_total":  { "type": "integer" },
          "net_pay":    { "type": "integer" }
        }
      }
    },
    "totals": {
      "type": "object",
      "properties": {
        "gross":     { "type": "integer" },
        "insurance": { "type": "integer" },
        "tax":       { "type": "integer" },
        "net":       { "type": "integer" }
      }
    }
  }
}
```

### 2-3. 취득신고서 결과

```jsonschema
{
  "title": "AcquisitionReport",
  "type": "object",
  "properties": {
    "ok":    { "type": "boolean" },
    "count": { "type": "integer", "description": "신고 대상 인원" },
    "file":  { "type": "string" },
    "entries": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name":       { "type": "string", "description": "마스킹된 이름" },
          "hire_date":  { "type": "string", "format": "date" },
          "bosu":       { "type": "integer", "description": "보수월액" },
          "pension":    { "type": "boolean", "description": "국민연금 대상" },
          "health":     { "type": "boolean", "description": "건강보험 대상" },
          "employment": { "type": "boolean", "description": "고용보험 대상" }
        }
      }
    }
  }
}
```

### 2-4. 상실신고서 결과

```jsonschema
{
  "title": "LossReport",
  "type": "object",
  "properties": {
    "ok":    { "type": "boolean" },
    "count": { "type": "integer" },
    "file":  { "type": "string" },
    "entries": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name":           { "type": "string" },
          "term_date":      { "type": "string", "format": "date" },
          "loss_date":      { "type": "string", "format": "date", "description": "상실일 = 퇴사일+1" },
          "compensation":   { "type": "integer", "description": "보수총액" },
          "loss_reason":    { "type": "string" }
        }
      }
    }
  }
}
```

### 2-5. LLM 분석 결과 (llm-* 명령)

```jsonschema
{
  "title": "LLMAnalysisResult",
  "type": "object",
  "properties": {
    "ok":       { "type": "boolean" },
    "analysis": { "type": "string", "description": "LLM 분석 텍스트 (정화됨)" },
    "anomalies": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "token":    { "type": "string" },
          "category": { "type": "string" },
          "severity": { "type": "string", "enum": ["info", "warning", "critical"] },
          "message":  { "type": "string" }
        }
      }
    }
  }
}
```

---

## 3. REST API 엔드포인트 후보 (CLI → HTTP)

현 CLI 명령을 REST로 노출할 때의 매핑:

### 3-1. 급여 처리 (Payroll)

| Method | Endpoint | CLI Command | Auth | Description |
|--------|----------|-------------|------|-------------|
| GET | `/api/v1/sites` | (routing.yaml) | API key | 사업장 목록 |
| GET | `/api/v1/sites/{key}` | (routing.yaml) | API key | 사업장 상세 |
| POST | `/api/v1/payroll/{key}/prepare` | step1 | API key | 월 파일 생성 |
| POST | `/api/v1/payroll/{key}/attendance` | step2 | API key | 근태 반영 |
| GET | `/api/v1/payroll/{key}/summary` | payroll-summary | API key | 급여 요약 |
| GET | `/api/v1/payroll/{key}/detail/roster` | payroll-detail-roster | API key | 직원 명부 |
| GET | `/api/v1/payroll/{key}/detail/insurance` | payroll-detail-insurance | API key | 보험 상세 |
| GET | `/api/v1/payroll/{key}/detail/anomalies` | payroll-detail-anomalies | API key | 이상 감지 |
| POST | `/api/v1/payroll/{key}/validate` | payroll-validate | API key | 급여 검증 |

### 3-2. 보험 신고 (Insurance Reports)

| Method | Endpoint | CLI Command | Auth | Description |
|--------|----------|-------------|------|-------------|
| POST | `/api/v1/insurance/{key}/acquisition` | insurance-acq | API key | 취득신고서 |
| POST | `/api/v1/insurance/{key}/loss` | insurance-loss | API key | 상실신고서 |
| POST | `/api/v1/insurance/{key}/daily` | insurance-daily | API key | 근로내용확인 |

### 3-3. 세무/회계 (Tax/Accounting)

| Method | Endpoint | CLI Command | Auth | Description |
|--------|----------|-------------|------|-------------|
| POST | `/api/v1/tax/{key}/split` | step0 (tax_split) | API key | 세무분리 |
| POST | `/api/v1/tax/{key}/convert` | tax-convert | API key | 세무대장 변환 |
| POST | `/api/v1/tax/{key}/severance` | severance-calc | API key | 퇴직금 계산 |
| POST | `/api/v1/tax/{key}/health-settlement` | health-settlement | API key | 건보 정산 |

### 3-4. AI 분석 (LLM via RunPod)

| Method | Endpoint | CLI Command | Auth | Description |
|--------|----------|-------------|------|-------------|
| POST | `/api/v1/ai/attendance` | llm-attendance | API key | 근태 분석 |
| POST | `/api/v1/ai/tax-settlement` | llm-tax-settlement | API key | 중도퇴사 정산 |
| POST | `/api/v1/ai/health-settlement` | llm-health-settlement | API key | 건보 정산 분석 |
| POST | `/api/v1/ai/month-compare` | llm-month-compare | API key | 전월 비교 |
| POST | `/api/v1/ai/insurance-check` | llm-insurance-check | API key | 보험 규칙 체크 |
| GET | `/api/v1/ai/health` | llm-health | — | LLM 상태 체크 |

### 3-5. 유틸리티

| Method | Endpoint | CLI Command | Auth | Description |
|--------|----------|-------------|------|-------------|
| POST | `/api/v1/consent/{key}` | consent-create | API key | 외국인 동의서 |
| POST | `/api/v1/master-db/{key}/rebuild` | build-master-db | API key | Master DB 재구축 |

### 3-6. 공통 Query Parameters

```
?year=2026&month=4      # 대상 연월
&employee_token=emp_0001 # 특정 직원 (선택)
&names=김철수,박영희      # 대상 직원명 (선택)
&bosu=1800000            # 보수월액 (취득신고용)
```

### 3-7. 공통 Response Envelope

```json
{
  "ok": true,
  "job_id": "job-20260425-143000",
  "data": { ... },       // 명령별 결과
  "warnings": [],        // 비치명적 경고
  "errors": []           // 치명적 오류
}
```

---

## 4. Privacy Broker 경계: PII 흐름 분석

### 4-1. 아키텍처

```
┌─────────────────────┐     sanitized JSON    ┌────────────────┐
│  Claude / Codex     │ ◄──────────────────── │ Privacy Broker │
│  (LLM / API Client) │ ────────────────────► │ (진입점)        │
│  PII 접근 불가       │     site_key + params  │                │
└─────────────────────┘                       └───────┬────────┘
                                                      │ dispatch()
                                              ┌───────▼────────┐
                                              │    Workers     │
                                              │ (PII 처리 허용) │
                                              │                │
                                              │ ┌─ gen_consent  │
                                              │ ├─ gen_insurance │
                                              │ ├─ payroll_runner│
                                              │ ├─ accounting   │
                                              │ └─ secure_llm   │
                                              └───────┬────────┘
                                                      │ direct file I/O
                                              ┌───────▼────────┐
                                              │  Excel Files   │
                                              │  private.yaml  │
                                              │  Master_DB.csv │
                                              └────────────────┘
```

### 4-2. PII 종류별 접근 시점

| PII 유형 | 어디에 존재 | 누가 접근 | 언제 필요 | API 노출 |
|---------|-----------|----------|----------|---------|
| **주민번호** (13자리) | Excel, private.yaml | Worker only | 신고서 생성, 연령 판단, Master DB | **절대 불가** — `[REDACTED]` |
| **계좌번호** | Excel | Worker only | 급여 이체, 신고서 | **절대 불가** |
| **전화번호** | Excel | Worker only | 신고서 (현재 미사용) | **절대 불가** |
| **이름** (실명) | Excel | Worker → Broker 마스킹 | 전 과정 | `name_masked` (김OO) |
| **급여 금액** | Excel | Worker → Broker | 전 과정 | 비식별 집계로만 |
| **입퇴사일** | Excel | Worker → Broker | 보험 판단, 정산 | **허용** (PII 아님) |
| **사업장 경로** | private.yaml | Worker only | 파일 탐색 | site_key로 간접 참조 |
| **관리번호** (4대보험) | private.yaml | Worker only | 신고서 헤더 | **절대 불가** |

### 4-3. 단계별 PII 필요도

| 단계 | PII 필요? | 상세 |
|------|----------|------|
| **사업장 선택** | ❌ | site_key (ASCII) + routing.yaml (public) |
| **파일 탐색** | 🟡 경로만 | private.yaml의 base_path → Worker 내부 |
| **직원 목록 읽기** | ✅ 전체 | 주민번호(연령판단), 이름, 입퇴사일, 보험여부 |
| **보험 판단** | ✅ 주민번호 | 만60세/65세 판단 = 주민번호 앞 7자리 |
| **보수총액 계산** | ✅ 주민번호 | Master DB CSV 키 = 주민번호_ID |
| **신고서 작성** | ✅ 전체 | 주민번호, 이름, 보수 → 엑셀 템플릿 |
| **결과 반환** | ❌ | 정화된 JSON만 (sanitize 함수) |
| **LLM 분석** | ✅ → RunPod | secure_llm이 전용 인스턴스로 전송 |

### 4-4. 정화 규칙 (sanitize)

```python
PII_PATTERNS = [
    r"\d{6}-[1-8]\d{6}",                     # 주민번호
    r"\d{3}-\d{4}-\d{4,7}(-\d{2})?",         # 계좌번호
    r"\b\d{3}-\d{3,4}-\d{4}\b",              # 전화번호
    r"[a-zA-Z0-9._%+-]+@[...]+\.[...]{2,}",  # 이메일
]
# 모든 매치 → "[REDACTED]"
```

### 4-5. SaaS 전환 시 PII 전략

| 현재 (Local CLI) | SaaS (Frappe HR) |
|-----------------|-----------------|
| PII = Excel 파일 (로컬) | PII = MariaDB (서버) |
| privacy_broker = 프로세스 경계 | Frappe permission system + RLS |
| sanitize() = regex 정화 | API response serializer |
| site_key = 파일시스템 라우팅 | Company/Branch DocType |
| employee_token = Worker 내부 생성 | Employee.name (Frappe 자동) |
| private.yaml = 로컬 파일 | Site config + secrets manager |

**핵심 전환 포인트:**
1. `주민번호` → Frappe `Employee.kr_resident_id` (encrypted field)
2. `routing.yaml` → Frappe `Company` + `Branch` DocType
3. `Worker` 로직 → Frappe `Server Script` or `Custom App`
4. `sanitize()` → Frappe API `allow_guest` + field-level permissions
5. `Master_DB.csv` → Frappe `Salary Slip` history query

---

## 5. Worker 목록 및 기능

| Worker | 파일 | CLI Command | 기능 |
|--------|------|-------------|------|
| gen_consent | `workers/gen_consent.py` | consent-create | 외국인 고용보험 동의서 PDF |
| gen_insurance_report | `workers/gen_insurance_report.py` | insurance-acq/loss/daily, build-master-db | 4대보험 신고서 + Master DB |
| payroll_runner | `workers/payroll_runner.py` | payroll-summary/detail-*/validate | 급여 요약/상세/검증 |
| accounting_runner | `workers/accounting_runner.py` | tax-convert, severance-calc, health-settlement | 세무변환, 퇴직금, 건보정산 |
| jecheon_runner | `workers/jecheon_runner.py` | (제천 전용) | 커스텀 리더 |
| secure_llm | `workers/secure_llm.py` | llm-* | RunPod LLM 경유 분석 |

---

## 6. 재사용 가능 모듈 (SaaS 전환 후보)

### 6-1. 그대로 재사용 가능 (Pure Logic)

| 모듈 | 위치 | 이유 |
|------|------|------|
| `utils.py` 전체 | `src/utils.py` | 날짜/주민번호/이름 유틸 — I/O 무관 |
| 4대보험 판단 | `insurance.py` | assess_insurance() — 순수 함수 |
| 연령 판단 | `utils.is_over_60`, `get_birth_year` | 주민번호 → 나이 계산 |
| 사업소득자 감지 | `engine._read_ledger_info` 내 | 3% 세율 판별 로직 |

### 6-2. 어댑터 필요 (I/O 변환)

| 모듈 | 변환 내용 |
|------|----------|
| `readers.py` 전체 | Excel 읽기 → Frappe DocType 읽기 |
| `config.py` | YAML → Frappe Company settings |
| `engine.py` Step 3~5 | 신고서 Excel 생성 → Frappe Report 생성 |

### 6-3. 대체 필요 (Windows 전용)

| 모듈 | 이유 | 대체 |
|------|------|------|
| Step 0 (세무분리) | win32com 의존 | Frappe 워크플로우 |
| PDF 출력 | win32com ExportAsFixedFormat | Frappe Print Format → PDF |
| Excel 수식 실행 | win32com Calculate | Frappe server-side 계산 |
