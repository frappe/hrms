# Frappe Side Contract for Korea Payroll Integration

> 상태: 설계 고정 초안
> 범위: Frappe HRMS 측 API/데이터 계약만 정의한다. 구현/DB 반영/한국화 UI 작업은 포함하지 않는다.

## 1. 결론

- Frappe HRMS는 **직원/조직/부서/근태/휴가**의 HR 백본이다.
- 외부 급여엔진은 **한국 급여 룰/계산식/4대보험/원천세**의 SoT다.
- Frappe는 급여 결과를 **import 받아 Salary Slip 및 한국 확장 계층에 표시/감사**한다.
- **PII(주민번호/계좌/외국인등록번호/주소)는 어떤 이유로도 Frappe 계약에 포함하지 않는다.**
- 사업장 마스터는 양방향 sync 대상이지만 **충돌 시 YAML 우선**이다.

---

## 2. 범위와 비범위

### 포함
1. 직원 마스터 export API
2. 근태/휴가 export API
3. 사업장 마스터 sync API
4. 급여 결과 import API
5. Custom Doctype 설계
6. `docs/korea/` 정합성 체크 표

### 제외
1. 한국화 UI/번역 작업
2. 실제 DB schema migration 실행
3. PII 신규 필드 검토
4. 외부 급여엔진 내부 규칙 정의

---

## 3. SoT 분할

| 영역 | SoT | Frappe 역할 |
|---|---|---|
| 직원/조직/부서 | Frappe | 생성/수정/조회/권한 |
| 근태/출퇴근/휴가 | Frappe | 입력/승인/월별 집계 export |
| 사업장(법인/사업자번호) | Frappe ↔ 급여엔진 | 양방향 sync, 충돌 시 YAML 우선 |
| 급여 룰/계산식 | 외부 급여엔진 | Frappe 비소유 |
| 4대보험/원천세 계산 | 외부 급여엔진 | 결과 수신만 수행 |
| 급여 결과 | 외부 급여엔진 | Salary Slip push 및 감사 추적 |
| PII | 외부 secure store / privacy broker | Frappe 저장 금지 |

---

## 4. 공통 보안/인증 규칙

### 4.1 인증 방식
- 1차는 **Frappe API Key / API Secret 기반 토큰 인증** 사용
- 헤더 예시
  - `Authorization: token <api_key>:<api_secret>`
- 운영 권고
  - 통합 전용 Integration User 별도 생성
  - 최소 권한 부여
  - IP allowlist 적용 가능 시 적용

### 4.2 공통 응답 원칙
- 모든 API는 JSON만 반환
- 시간은 ISO 8601 또는 Frappe datetime 문자열 중 하나로 고정
- 페이지네이션 필드 제공
- 변경분 추출용 `modified_after` 지원 권장

### 4.3 PII 금지 규칙
아래 필드는 **모든 요청/응답/캐시/감사 문서에서 금지**.
- 주민등록번호 전문
- 주민등록번호 앞자리/뒷자리 조합 복원 가능한 값
- 외국인등록번호 전문
- 계좌번호 전문
- 주소 전문

허용되는 값은 다음만 가능.
- employee ID
- employee number
- employee name
- branch/site ID
- masked display value가 필요할 경우에도 본 계약에서는 기본 제외

---

## 5. 직원 마스터 export API

### 5.1 목적
외부 급여엔진이 급여 계산 전에 최신 직원 기준정보를 pull 한다.

### 5.2 엔드포인트
- Method: `GET`
- Path: `/api/method/hrms.api.korea_integration.export_employee_master`

### 5.3 요청 파라미터

| name | type | required | 설명 |
|---|---|---|---|
| employee_id | string | no | 특정 직원 단건 조회 |
| company | string | no | 회사 필터 |
| branch | string | no | 사업장 필터 |
| modified_after | string(date-time) | no | 증분 조회 |
| include_inactive | boolean | no | 퇴사/비활성 포함 여부 |
| page | integer | no | 기본 1 |
| page_size | integer | no | 기본 100, 최대 500 |

### 5.4 포함 필드
- 사번(employee_number)
- 이름(employee_name)
- 입사일(date_of_joining)
- 퇴사일(relieving_date)
- 부서(department)
- 사업장(branch / worksite)
- 직급(designation)
- 근무형태(employment_type)
- 외국인 비자 구분(visa_status_code 등 비민감 분류코드)

### 5.5 절대 포함 금지
- 주민번호
- 계좌
- 주소
- 외국인등록번호

### 5.6 OpenAPI 3.x

```yaml
openapi: 3.1.0
info:
  title: Frappe HRMS Korea Integration API
  version: 1.0.0
paths:
  /api/method/hrms.api.korea_integration.export_employee_master:
    get:
      summary: Export employee master data for external Korea payroll engine
      security:
        - frappeToken: []
      parameters:
        - in: query
          name: employee_id
          schema: { type: string }
        - in: query
          name: company
          schema: { type: string }
        - in: query
          name: branch
          schema: { type: string }
        - in: query
          name: modified_after
          schema: { type: string, format: date-time }
        - in: query
          name: include_inactive
          schema: { type: boolean, default: false }
        - in: query
          name: page
          schema: { type: integer, minimum: 1, default: 1 }
        - in: query
          name: page_size
          schema: { type: integer, minimum: 1, maximum: 500, default: 100 }
      responses:
        '200':
          description: Employee master export response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EmployeeMasterExportResponse'
components:
  securitySchemes:
    frappeToken:
      type: apiKey
      in: header
      name: Authorization
```

### 5.7 JSON Schema

```json
{
  "$id": "https://winners.example/schemas/employee-master-export-response.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EmployeeMasterExportResponse",
  "type": "object",
  "required": ["data", "meta"],
  "properties": {
    "data": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "employee_id",
          "employee_number",
          "employee_name",
          "date_of_joining",
          "department",
          "branch",
          "designation",
          "employment_type",
          "employment_category",
          "status",
          "modified"
        ],
        "properties": {
          "employee_id": { "type": "string" },
          "employee_number": { "type": "string" },
          "employee_name": { "type": "string" },
          "company": { "type": "string" },
          "branch": { "type": "string" },
          "department": { "type": "string" },
          "designation": { "type": "string" },
          "employment_type": {
            "type": "string",
            "enum": ["정규직", "일용직", "파트타임", "계약직", "기타"]
          },
          "employment_category": {
            "type": "string",
            "enum": ["regular", "daily", "part_time", "contract", "foreign_worker", "other"]
          },
          "visa_status_code": {
            "type": ["string", "null"],
            "description": "외국인 비자 분류코드. 번호/등록정보는 포함하지 않음"
          },
          "date_of_joining": { "type": "string", "format": "date" },
          "relieving_date": { "type": ["string", "null"], "format": "date" },
          "status": { "type": "string" },
          "modified": { "type": "string", "format": "date-time" }
        },
        "additionalProperties": false,
        "not": {
          "anyOf": [
            { "required": ["resident_registration_number"] },
            { "required": ["foreigner_registration_number"] },
            { "required": ["bank_account_number"] },
            { "required": ["address"] }
          ]
        }
      }
    },
    "meta": {
      "type": "object",
      "required": ["page", "page_size", "has_more"],
      "properties": {
        "page": { "type": "integer" },
        "page_size": { "type": "integer" },
        "has_more": { "type": "boolean" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

---

## 6. 근태/휴가 export API

### 6.1 목적
월별 급여 계산에 필요한 출퇴근/휴가/시간외·야간·휴일 시간을 외부 급여엔진으로 전달한다.

### 6.2 설계 원칙
- 원본 입력은 Frappe가 관리
- export는 **월별 기간 기준**으로 수행
- 시간외/야간/휴일 시간은 `docs/korea/07 근로시간 기준`을 따르는 계산 기준 필드로 분리
- 휴가는 leave type 기준으로 구분

### 6.3 엔드포인트
- Method: `GET`
- Path: `/api/method/hrms.api.korea_integration.export_time_and_leave`

### 6.4 요청 파라미터

| name | type | required | 설명 |
|---|---|---|---|
| company | string | no | 회사 필터 |
| branch | string | no | 사업장 필터 |
| employee_id | string | no | 특정 직원 |
| from_date | string(date) | yes | 시작일 |
| to_date | string(date) | yes | 종료일 |
| modified_after | string(date-time) | no | 증분 조회 |
| page | integer | no | 기본 1 |
| page_size | integer | no | 기본 100 |

### 6.5 반환 범위
1. 월별 출퇴근 원장
2. 연차/병가/경조사 사용 내역
3. 시간외 근로 시간
4. 야간 근로 시간
5. 휴일 근로 시간

### 6.6 OpenAPI 3.x

```yaml
openapi: 3.1.0
info:
  title: Frappe HRMS Korea Integration API
  version: 1.0.0
paths:
  /api/method/hrms.api.korea_integration.export_time_and_leave:
    get:
      summary: Export monthly attendance and leave for external Korea payroll engine
      security:
        - frappeToken: []
      parameters:
        - in: query
          name: company
          schema: { type: string }
        - in: query
          name: branch
          schema: { type: string }
        - in: query
          name: employee_id
          schema: { type: string }
        - in: query
          name: from_date
          required: true
          schema: { type: string, format: date }
        - in: query
          name: to_date
          required: true
          schema: { type: string, format: date }
        - in: query
          name: modified_after
          schema: { type: string, format: date-time }
        - in: query
          name: page
          schema: { type: integer, minimum: 1, default: 1 }
        - in: query
          name: page_size
          schema: { type: integer, minimum: 1, maximum: 500, default: 100 }
      responses:
        '200':
          description: Time and leave export response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TimeAndLeaveExportResponse'
components:
  securitySchemes:
    frappeToken:
      type: apiKey
      in: header
      name: Authorization
```

### 6.7 JSON Schema

```json
{
  "$id": "https://winners.example/schemas/time-and-leave-export-response.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TimeAndLeaveExportResponse",
  "type": "object",
  "required": ["data", "meta"],
  "properties": {
    "data": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "employee_id",
          "period",
          "attendance_records",
          "leave_records",
          "work_time_summary"
        ],
        "properties": {
          "employee_id": { "type": "string" },
          "period": {
            "type": "object",
            "required": ["from_date", "to_date"],
            "properties": {
              "from_date": { "type": "string", "format": "date" },
              "to_date": { "type": "string", "format": "date" }
            },
            "additionalProperties": false
          },
          "attendance_records": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [
                "attendance_id",
                "attendance_date",
                "status",
                "regular_hours",
                "overtime_hours",
                "night_hours",
                "holiday_hours"
              ],
              "properties": {
                "attendance_id": { "type": "string" },
                "attendance_date": { "type": "string", "format": "date" },
                "status": { "type": "string" },
                "shift_type": { "type": ["string", "null"] },
                "in_time": { "type": ["string", "null"], "format": "date-time" },
                "out_time": { "type": ["string", "null"], "format": "date-time" },
                "regular_hours": { "type": "number" },
                "overtime_hours": { "type": "number" },
                "night_hours": { "type": "number" },
                "holiday_hours": { "type": "number" },
                "modified": { "type": ["string", "null"], "format": "date-time" }
              },
              "additionalProperties": false
            }
          },
          "leave_records": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [
                "leave_application_id",
                "leave_type",
                "from_date",
                "to_date",
                "total_leave_days",
                "status"
              ],
              "properties": {
                "leave_application_id": { "type": "string" },
                "leave_type": {
                  "type": "string",
                  "description": "예: 연차, 병가, 경조사"
                },
                "from_date": { "type": "string", "format": "date" },
                "to_date": { "type": "string", "format": "date" },
                "half_day": { "type": "boolean" },
                "half_day_date": { "type": ["string", "null"], "format": "date" },
                "total_leave_days": { "type": "number" },
                "status": { "type": "string" },
                "modified": { "type": ["string", "null"], "format": "date-time" }
              },
              "additionalProperties": false
            }
          },
          "work_time_summary": {
            "type": "object",
            "required": [
              "regular_hours_total",
              "overtime_hours_total",
              "night_hours_total",
              "holiday_hours_total"
            ],
            "properties": {
              "regular_hours_total": { "type": "number" },
              "overtime_hours_total": { "type": "number" },
              "night_hours_total": { "type": "number" },
              "holiday_hours_total": { "type": "number" }
            },
            "additionalProperties": false
          }
        },
        "additionalProperties": false
      }
    },
    "meta": {
      "type": "object",
      "required": ["page", "page_size", "has_more"],
      "properties": {
        "page": { "type": "integer" },
        "page_size": { "type": "integer" },
        "has_more": { "type": "boolean" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

### 6.8 시간 필드 해석 규칙
- `regular_hours`: 소정근로 시간
- `overtime_hours`: 연장근로 시간
- `night_hours`: 22:00~06:00 기준 야간근로 시간
- `holiday_hours`: 휴일근로 시간

> 위 필드 의미는 `docs/korea/07 근로시간 기준`의 정의에 종속된다.

---

## 7. 사업장 마스터 sync API (양방향)

### 7.1 목적
사업장(법인/사업자번호/운영단위) 기준정보를 Frappe와 외부 급여엔진 사이에서 동기화한다.

### 7.2 충돌 해결 룰
- **YAML 우선**
- Frappe 변경과 YAML 변경이 충돌하면 YAML을 canonical source로 간주
- Frappe는 충돌 시 `conflict_detected` 상태와 마지막 적용 이력만 남긴다

### 7.3 Frappe → 급여엔진 알림 API

#### 의미
신규 사업장 생성 또는 핵심 메타 변경 시 외부 급여엔진에 알린다.

- Method: `POST`
- Path: `/api/method/hrms.api.korea_integration.notify_worksite_master_change`

#### JSON Schema (request)

```json
{
  "$id": "https://winners.example/schemas/worksite-master-notify-request.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "WorksiteMasterNotifyRequest",
  "type": "object",
  "required": ["event_type", "worksite"],
  "properties": {
    "event_type": {
      "type": "string",
      "enum": ["created", "updated", "deactivated"]
    },
    "worksite": {
      "type": "object",
      "required": ["company", "branch", "business_registration_number", "effective_from"],
      "properties": {
        "company": { "type": "string" },
        "branch": { "type": "string" },
        "business_registration_number": { "type": "string" },
        "worksite_code": { "type": ["string", "null"] },
        "effective_from": { "type": "string", "format": "date" },
        "status": { "type": ["string", "null"] },
        "modified": { "type": ["string", "null"], "format": "date-time" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

### 7.4 급여엔진 → Frappe 반영 API

#### 의미
YAML 기준 사업장 변경을 Frappe가 수신해 동기화한다.

- Method: `POST`
- Path: `/api/method/hrms.api.korea_integration.apply_worksite_master_from_yaml`

#### OpenAPI 3.x

```yaml
openapi: 3.1.0
info:
  title: Frappe HRMS Korea Integration API
  version: 1.0.0
paths:
  /api/method/hrms.api.korea_integration.apply_worksite_master_from_yaml:
    post:
      summary: Apply YAML-priority worksite master changes from external payroll engine
      security:
        - frappeToken: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/WorksiteYamlSyncRequest'
      responses:
        '200':
          description: Worksite sync result
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WorksiteYamlSyncResponse'
components:
  securitySchemes:
    frappeToken:
      type: apiKey
      in: header
      name: Authorization
```

#### JSON Schema (request/response)

```json
{
  "$id": "https://winners.example/schemas/worksite-yaml-sync-request.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "WorksiteYamlSyncRequest",
  "type": "object",
  "required": ["yaml_version", "items"],
  "properties": {
    "yaml_version": { "type": "string" },
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["company", "branch", "business_registration_number", "effective_from"],
        "properties": {
          "company": { "type": "string" },
          "branch": { "type": "string" },
          "business_registration_number": { "type": "string" },
          "worksite_code": { "type": ["string", "null"] },
          "status": { "type": ["string", "null"] },
          "effective_from": { "type": "string", "format": "date" },
          "effective_to": { "type": ["string", "null"], "format": "date" },
          "source_modified": { "type": ["string", "null"], "format": "date-time" }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

```json
{
  "$id": "https://winners.example/schemas/worksite-yaml-sync-response.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "WorksiteYamlSyncResponse",
  "type": "object",
  "required": ["applied", "conflicts", "yaml_version"],
  "properties": {
    "yaml_version": { "type": "string" },
    "applied": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["company", "branch", "action"],
        "properties": {
          "company": { "type": "string" },
          "branch": { "type": "string" },
          "action": { "type": "string", "enum": ["created", "updated", "ignored"] }
        },
        "additionalProperties": false
      }
    },
    "conflicts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["company", "branch", "resolution"],
        "properties": {
          "company": { "type": "string" },
          "branch": { "type": "string" },
          "resolution": { "type": "string", "enum": ["yaml_wins"] },
          "detail": { "type": ["string", "null"] }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

---

## 8. 급여 결과 import API

### 8.1 목적
외부 급여엔진 계산 결과를 Frappe Salary Slip으로 push 한다.

### 8.2 원칙
- employee는 **ID만 식별자**로 사용
- 지급월 단위 결과를 수신
- 항목은 과세/비과세를 구분
- 4대보험 공제/원천세/실지급액 포함
- **PII 없음**

### 8.3 엔드포인트
- Method: `POST`
- Path: `/api/method/hrms.api.korea_integration.import_payroll_result`

### 8.4 OpenAPI 3.x

```yaml
openapi: 3.1.0
info:
  title: Frappe HRMS Korea Integration API
  version: 1.0.0
paths:
  /api/method/hrms.api.korea_integration.import_payroll_result:
    post:
      summary: Import payroll result from external Korea payroll engine
      security:
        - frappeToken: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PayrollResultImportRequest'
      responses:
        '200':
          description: Payroll import result
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PayrollResultImportResponse'
components:
  securitySchemes:
    frappeToken:
      type: apiKey
      in: header
      name: Authorization
```

### 8.5 JSON Schema (request)

```json
{
  "$id": "https://winners.example/schemas/payroll-result-import-request.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PayrollResultImportRequest",
  "type": "object",
  "required": [
    "run_id",
    "employee_id",
    "pay_year_month",
    "taxable_items",
    "non_taxable_items",
    "social_insurance_deductions",
    "withholding_tax",
    "net_pay"
  ],
  "properties": {
    "run_id": { "type": "string" },
    "employee_id": { "type": "string" },
    "pay_year_month": {
      "type": "string",
      "pattern": "^[0-9]{4}-(0[1-9]|1[0-2])$"
    },
    "salary_slip_external_ref": { "type": ["string", "null"] },
    "taxable_items": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["code", "label", "amount"],
        "properties": {
          "code": { "type": "string" },
          "label": { "type": "string" },
          "amount": { "type": "number" }
        },
        "additionalProperties": false
      }
    },
    "non_taxable_items": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["code", "label", "amount"],
        "properties": {
          "code": { "type": "string" },
          "label": { "type": "string" },
          "amount": { "type": "number" }
        },
        "additionalProperties": false
      }
    },
    "social_insurance_deductions": {
      "type": "object",
      "required": [
        "national_pension",
        "health_insurance",
        "long_term_care_insurance",
        "employment_insurance"
      ],
      "properties": {
        "national_pension": { "type": "number" },
        "health_insurance": { "type": "number" },
        "long_term_care_insurance": { "type": "number" },
        "employment_insurance": { "type": "number" }
      },
      "additionalProperties": false
    },
    "withholding_tax": {
      "type": "object",
      "required": ["income_tax", "local_income_tax"],
      "properties": {
        "income_tax": { "type": "number" },
        "local_income_tax": { "type": "number" }
      },
      "additionalProperties": false
    },
    "gross_pay": { "type": ["number", "null"] },
    "total_deduction": { "type": ["number", "null"] },
    "net_pay": { "type": "number" },
    "ruleset_version": { "type": ["string", "null"] },
    "engine_version": { "type": ["string", "null"] }
  },
  "additionalProperties": false,
  "not": {
    "anyOf": [
      { "required": ["resident_registration_number"] },
      { "required": ["foreigner_registration_number"] },
      { "required": ["bank_account_number"] },
      { "required": ["address"] }
    ]
  }
}
```

### 8.6 JSON Schema (response)

```json
{
  "$id": "https://winners.example/schemas/payroll-result-import-response.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PayrollResultImportResponse",
  "type": "object",
  "required": ["status", "employee_id", "pay_year_month"],
  "properties": {
    "status": { "type": "string", "enum": ["received", "updated", "rejected"] },
    "employee_id": { "type": "string" },
    "pay_year_month": { "type": "string" },
    "salary_slip": { "type": ["string", "null"] },
    "korea_calc_reference": { "type": ["string", "null"] },
    "message": { "type": ["string", "null"] }
  },
  "additionalProperties": false
}
```

### 8.7 연말정산 결과 import API

#### 목적
- 외부 급여엔진이 계산한 연말정산 결과를 Frappe Salary Slip에 반영한다.
- **7단계 계산 로직 자체는 engine-side SoT**로 유지한다.
- Frappe는 결과 수신, 링크, 감사 추적만 수행한다.

#### 엔드포인트
- Method: `POST`
- Path: `/api/method/hrms.api.korea_integration.import_year_end_settlement_result`

#### JSON Schema (request)

```json
{
  "$id": "https://winners.example/schemas/year-end-settlement-import-request.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "YearEndSettlementImportRequest",
  "type": "object",
  "required": [
    "run_id",
    "employee_id",
    "settlement_year",
    "settlement_kind",
    "applied_pay_year_month",
    "prepaid_tax",
    "determined_tax",
    "adjustment_tax"
  ],
  "properties": {
    "run_id": { "type": "string" },
    "employee_id": { "type": "string" },
    "settlement_year": { "type": "integer", "minimum": 2000 },
    "settlement_kind": {
      "type": "string",
      "enum": ["annual_february", "mid_year_termination"]
    },
    "applied_pay_year_month": {
      "type": "string",
      "pattern": "^[0-9]{4}-(0[1-9]|1[0-2])$"
    },
    "salary_slip_external_ref": { "type": ["string", "null"] },
    "prepaid_tax": { "type": "number", "description": "기납부세액" },
    "determined_tax": { "type": "number", "description": "결정세액" },
    "adjustment_tax": { "type": "number", "description": "차감징수세액" },
    "local_income_tax": { "type": ["number", "null"] },
    "engine_version": { "type": ["string", "null"] },
    "ruleset_version": { "type": ["string", "null"] },
    "note": { "type": ["string", "null"] }
  },
  "additionalProperties": false,
  "not": {
    "anyOf": [
      { "required": ["resident_registration_number"] },
      { "required": ["foreigner_registration_number"] },
      { "required": ["bank_account_number"] },
      { "required": ["address"] }
    ]
  }
}
```

#### JSON Schema (response)

```json
{
  "$id": "https://winners.example/schemas/year-end-settlement-import-response.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "YearEndSettlementImportResponse",
  "type": "object",
  "required": ["status", "employee_id", "settlement_year", "applied_pay_year_month"],
  "properties": {
    "status": { "type": "string", "enum": ["received", "updated", "rejected"] },
    "employee_id": { "type": "string" },
    "settlement_year": { "type": "integer" },
    "applied_pay_year_month": { "type": "string" },
    "salary_slip": { "type": ["string", "null"] },
    "korea_calc_reference": { "type": ["string", "null"] },
    "message": { "type": ["string", "null"] }
  },
  "additionalProperties": false
}
```

### 8.8 퇴직금 결과 import API

#### 목적
- 외부 급여엔진이 계산한 퇴직금/퇴직소득세 결과를 Frappe로 수신한다.
- **평균임금, 근속연수 산정, 퇴직소득세 계산은 engine-side SoT**로 유지한다.
- Frappe는 별도 `Korea Severance Slip` 문서로 반영/감사한다.

#### 엔드포인트
- Method: `POST`
- Path: `/api/method/hrms.api.korea_integration.import_severance_result`

#### JSON Schema (request)

```json
{
  "$id": "https://winners.example/schemas/severance-result-import-request.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SeveranceResultImportRequest",
  "type": "object",
  "required": [
    "run_id",
    "employee_id",
    "retirement_date",
    "average_wage",
    "service_years",
    "severance_pay",
    "severance_income_tax",
    "net_pay"
  ],
  "properties": {
    "run_id": { "type": "string" },
    "employee_id": { "type": "string" },
    "retirement_date": { "type": "string", "format": "date" },
    "linked_salary_slip": { "type": ["string", "null"] },
    "average_wage": { "type": "number", "description": "평균임금" },
    "service_years": { "type": "number", "description": "근속연수" },
    "severance_pay": { "type": "number", "description": "퇴직금" },
    "severance_income_tax": { "type": "number", "description": "퇴직소득세" },
    "local_income_tax": { "type": ["number", "null"] },
    "net_pay": { "type": "number", "description": "실지급액" },
    "engine_version": { "type": ["string", "null"] },
    "ruleset_version": { "type": ["string", "null"] },
    "note": { "type": ["string", "null"] }
  },
  "additionalProperties": false,
  "not": {
    "anyOf": [
      { "required": ["resident_registration_number"] },
      { "required": ["foreigner_registration_number"] },
      { "required": ["bank_account_number"] },
      { "required": ["address"] }
    ]
  }
}
```

#### JSON Schema (response)

```json
{
  "$id": "https://winners.example/schemas/severance-result-import-response.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SeveranceResultImportResponse",
  "type": "object",
  "required": ["status", "employee_id", "retirement_date"],
  "properties": {
    "status": { "type": "string", "enum": ["received", "updated", "rejected"] },
    "employee_id": { "type": "string" },
    "retirement_date": { "type": "string", "format": "date" },
    "korea_severance_slip": { "type": ["string", "null"] },
    "korea_calc_reference": { "type": ["string", "null"] },
    "message": { "type": ["string", "null"] }
  },
  "additionalProperties": false
}
```

---

## 9. Custom Doctype 설계

### 9.1 Korea Salary Slip Extension

#### 목적
- `docs/korea/01 한국 명세서 양식 기준`에 맞는 한국형 표시/확장 계층
- 표준 `Salary Slip`을 완전 대체하지 않고 링크 확장으로 유지

#### 권장 주요 필드
| fieldname | type | 설명 |
|---|---|---|
| salary_slip | Link(Salary Slip) | 표준 Salary Slip 연결 |
| employee | Link(Employee) | 직원 |
| pay_year_month | Data | 지급월 YYYY-MM |
| taxable_total | Currency | 과세 항목 합계 |
| non_taxable_total | Currency | 비과세 항목 합계 |
| national_pension | Currency | 국민연금 |
| health_insurance | Currency | 건강보험 |
| long_term_care_insurance | Currency | 장기요양보험 |
| employment_insurance | Currency | 고용보험 |
| income_tax | Currency | 소득세 |
| local_income_tax | Currency | 지방소득세 |
| net_pay | Currency | 실지급액 |
| extension_status | Select | draft / synced / overridden |
| external_run_id | Data | 외부 엔진 실행 ID |
| ruleset_version | Data | 룰 버전 |

#### child table 권장
- `Korea Salary Slip Extension Item`
  - code
  - label
  - tax_category (`taxable`, `non_taxable`, `deduction`)
  - amount
  - display_order

### 9.2 Korea Calc Reference

#### 목적
- 외부 엔진 호출 결과 캐시
- 수신 페이로드 요약 저장
- 감사/추적/재동기화 기준 문서

#### 권장 주요 필드
| fieldname | type | 설명 |
|---|---|---|
| run_id | Data | 외부 실행 ID |
| employee | Link(Employee) | 직원 |
| pay_year_month | Data | 지급월 |
| payload_hash | Data | 중복 감지 |
| request_payload_json | Long Text | 요청 요약 또는 hash 중심 |
| response_payload_json | Long Text | 수신 원문(JSON) |
| import_status | Select | received / mapped / rejected |
| linked_salary_slip | Link(Salary Slip) | 연결 문서 |
| linked_extension | Link(Korea Salary Slip Extension) | 연결 확장 |
| validation_message | Long Text | 검증 결과 |
| synced_at | Datetime | 반영 시각 |

### 9.3 Korea Severance Slip

#### 목적
- 퇴직금/퇴직소득세 결과를 표준 Salary Slip과 분리해 저장한다.
- 퇴직자 단위 audit trail과 재전송 기준 문서로 사용한다.

#### 권장 주요 필드
| fieldname | type | 설명 |
|---|---|---|
| employee | Link(Employee) | 직원 |
| retirement_date | Date | 퇴직일 |
| linked_salary_slip | Link(Salary Slip) | 퇴직월 급여 Slip 연결(있을 때만) |
| average_wage | Currency | 평균임금 |
| service_years | Float | 근속연수 |
| severance_pay | Currency | 퇴직금 |
| severance_income_tax | Currency | 퇴직소득세 |
| local_income_tax | Currency | 지방소득세 |
| net_pay | Currency | 실지급액 |
| external_run_id | Data | 외부 엔진 실행 ID |
| ruleset_version | Data | 룰 버전 |
| linked_calc_reference | Link(Korea Calc Reference) | 원본 payload 연결 |

### 9.4 PII 금지 적용 결과

1. `docs/korea/10-frappe-customization.md`의 `kr_resident_id` 저장 제안은 **본 계약에서 reject** 한다.
2. Employee 확장 필드에는 주민번호/외국인등록번호/계좌/주소 전문을 저장하지 않는다.
3. 엔진 측 식별 보강이 필요할 때는 **privacy_broker 경유 일회성 조회 패턴**을 사용한다.
   - Frappe → privacy broker: `employee_id`, `employee_number`, `company`, `lookup_purpose`
   - privacy broker → engine/Frappe: `broker_lookup_id`, `subject_match_status`, `expires_at`
   - 주민번호 원문/부분값/복원 가능한 토큰은 Frappe에 저장하지 않는다.
4. `Korea Calc Reference`에는 broker lookup 결과가 필요하면 `broker_lookup_id`와 성공/실패 상태만 남긴다.

### 9.5 표준 Salary Slip vs Korea Salary Slip 충돌 룰

1. **한국 급여 결과 값은 외부 엔진이 우선**
2. 표준 `Salary Slip`의 계산 필드와 `Korea Salary Slip Extension` 값이 다르면
   - 표시 기준: `Korea Salary Slip Extension`
   - 감사 기준: `Korea Calc Reference`
3. 표준 `Salary Slip`은 회계/링크/기본 문서 역할 유지
4. 한국형 명세서 출력은 `Korea Salary Slip Extension` 기반으로 렌더링
5. 충돌 상태는 `extension_status=overridden` 또는 별도 경고 플래그로 표기

---

## 10. Frappe 측 구현 경계 메모

### 권장 엔드포인트 파일
- `hrms/api/korea_integration.py`

### 권장 구현 함수
- `export_employee_master()`
- `export_time_and_leave()`
- `notify_worksite_master_change()`
- `apply_worksite_master_from_yaml()`
- `import_payroll_result()`
- `import_year_end_settlement_result()`
- `import_severance_result()`

### 기존 레포 구조와의 연결 포인트
- Employee 조회: ERPNext Employee + HRMS override 사용 가능
- Attendance/Leave 조회: `hrms/api/__init__.py`의 패턴 재사용 가능
- Company/Branch 조회: `Company`, `Branch`, regional setup 연결
- Salary Slip 연결: `hrms/payroll/doctype/salary_slip/*` 확장 계층 활용

---

## 11. docs/korea/ 와의 정합성 체크 표

> 실파일 확인 기준: `origin/feature/korea-payroll-docs` 브랜치의 `docs/korea/README.md` + `01`~`10` 문서.

| docs/korea 항목 | 핵심 주제 | 본 계약 반영 위치 | 정합성 판단 |
|---|---|---|---|
| `docs/korea/README.md` | 전체 로드맵, 단계별 우선순위, Korea 모듈 범위 | §1 결론, §2 범위와 비범위, §3 SoT 분할 | **부분 정합** — 계약 범위는 맞지만 README의 Phase 2~4 계산/신고 범위 전체를 아직 담지 않음 |
| `docs/korea/01-salary-structure.md` | 과세/비과세/공제 급여 구성요소 | §8 `import_payroll_result`, §9 `Korea Salary Slip Extension`, §10 `Korea Calc Reference` | **정합** — 명세서 표시·과세/비과세·공제 구조와 직접 연결 |
| `docs/korea/02-social-insurance.md` | 4대보험 요율·면제·정산 규칙 | §8 `import_payroll_result`, §10 `Korea Calc Reference` | **부분 정합** — 결과 수신 필드는 있으나 요율표/면제판정/연말정산 입력 계약은 없음 |
| `docs/korea/03-income-tax.md` | 간이세액표·맞춤 원천징수·지방소득세 | §8 `import_payroll_result`, §10 `Korea Calc Reference` | **부분 정합** — 원천세 결과 수신은 있으나 간이세액표 lookup 변수와 지방소득세 세분 필드가 비어 있음 |
| `docs/korea/04-year-end-settlement.md` | 연말정산 7단계 계산 | §8.7 `import_year_end_settlement_result`, §9.2 `Korea Calc Reference` | **정합** — Frappe 측 범위인 결과 import 계약을 추가했고, 7단계 계산은 engine-side SoT로 분리 |
| `docs/korea/05-severance.md` | 퇴직금·퇴직소득세 계산 | §8.8 `import_severance_result`, §9.3 `Korea Severance Slip`, §9.2 `Korea Calc Reference` | **정합** — Frappe 측 범위인 severance 결과 import·별도 slip·audit 연결을 반영했고 계산 로직은 engine-side SoT로 분리 |
| `docs/korea/06-minimum-wage.md` | 최저임금 검증·209시간 기준 | 직접 반영 없음 | **불일치/누락** — minimum wage compliance 검증 결과를 주고받는 계약 부재 |
| `docs/korea/07-working-hours.md` | 근로시간·가산수당·주휴수당 | §6 `export_time_and_leave` | **부분 정합** — 시간 분리 필드는 있으나 주휴수당/통상시급 산정 입력은 명시되지 않음 |
| `docs/korea/08-daily-workers.md` | 일용직 세금·보험·분기 신고 | §5 `export_employee_master`, §8 `import_payroll_result` | **부분 정합** — 일용직 구분 enum은 있으나 일급·분기신고·de minimis 규칙용 계약 필드 없음 |
| `docs/korea/09-foreign-workers.md` | 외국인 단일세율·비자별 보험 예외 | §5 `export_employee_master` | **부분 정합** — `visa_status_code`는 있으나 flat tax/연금협정/고용보험 opt-in 필드가 없음 |
| `docs/korea/10-frappe-customization.md` | 커스텀 필드, Salary Slip 확장, 훅/리포트 | §9 Custom Doctype 설계 전반, §9.4 PII 금지 적용 결과 | **부분 정합** — 확장 방향은 유지하되 `kr_resident_id` 저장 제안은 reject하고 privacy_broker 일회성 조회 패턴으로 대체 |

| 어긋난/누락 항목 | 관련 docs/korea 문서 | 영향 범위 | 우선순위 |
|---|---|---|---|
| 4대보험 요율표·면제판정·보수총액정산 입력 계약 없음 | `02-social-insurance.md` | 보험 계산근거를 Frappe에서 추적/감사하기 어려움 | 중간 |
| 간이세액표 lookup 변수·지방소득세 세분 필드 없음 | `03-income-tax.md` | 소득세 계산 근거와 결과 검증 포인트 부족 | 중간 |
| 최저임금 검증 결과 계약 없음 | `06-minimum-wage.md` | 계산 후 compliance check 전달 경로 없음 | 중간 |
| 일용직 전용 일급/분기신고 payload 없음 | `08-daily-workers.md` | 일용직을 일반 근로자와 구분 처리하기 어려움 | 중간 |
| 외국인 flat tax/연금협정/임의가입 상태 필드 없음 | `09-foreign-workers.md` | 외국인 예외 규칙을 계약 레벨에서 재현 불가 | 중간 |
| 주휴수당·통상시급 산정 입력 필드 없음 | `07-working-hours.md` | 근로시간 export만으로 가산수당 산정 근거가 불완전 | 낮음 |

---

## 12. 권고

지금 단계에서는 Frappe 측 계약에서 **높음 우선순위 3건을 닫았고**, 다음은 중간 우선순위 정리로 가는 것이 맞다.

1. `docs/korea/02-social-insurance.md` 기준 요율표·면제판정·보수총액정산 입력 계약 추가
2. `docs/korea/03-income-tax.md` 기준 간이세액표 lookup 변수·지방소득세 세분 필드 추가
3. `docs/korea/06-minimum-wage.md` 기준 compliance 결과 import contract 추가
4. 실제 구현 전 PII 차단 테스트 케이스와 privacy_broker 경유 로그 정책 확정

이상으로 Frappe 측 계약 범위는 현재 사이클 기준으로 문서 고정한다.
