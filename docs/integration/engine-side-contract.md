# Engine-Side Contract — Frappe HRMS Integration

> 급여자동화 엔진 × Frappe HRMS 통합 계약서
> 작성: 2026-04-25 | 메인테이너: 급여자동화 엔진 측
> 전제: 기존 운영 중단 0%, privacy_broker 경계 유지, 인터페이스 도출 단계

---

## 1. 입력 인터페이스 정의 (현재)

### 1-1. 사업장 설정 (YAML → JSON Schema)

`config/{사업장}.yaml` → `LocationConfig.from_yaml()` → dataclass

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "LocationConfig",
  "type": "object",
  "required": ["company", "location", "paths"],
  "properties": {
    "company":     { "type": "string", "example": "(주)맥주와친구들" },
    "location":    { "type": "string", "example": "상봉점" },
    "reader_type": {
      "type": "string",
      "enum": ["type_a", "type_b", "type_c", "generic", "jecheon"],
      "description": "type_a=근태체크3시트, type_b/c=임금대장기반, generic=YAML좌표만"
    },
    "paths": {
      "type": "object",
      "required": ["base"],
      "properties": {
        "base":          { "type": "string", "description": "급여파일 루트 (PII — private.yaml 참조)" },
        "templates_dir": { "type": "string", "description": "신고서 템플릿 디렉토리" }
      }
    },
    "files": {
      "type": "object",
      "properties": {
        "prefix": { "type": "string", "description": "엑셀 파일명 접두어" }
      }
    },
    "workers": {
      "type": "object",
      "properties": {
        "alias_map": {
          "type": "object",
          "additionalProperties": { "type": "string" },
          "description": "근태이름↔정직원이름 매핑"
        }
      }
    },
    "reports": {
      "type": "object",
      "properties": {
        "job_code":          { "type": "string", "default": "532" },
        "standard_hours":    { "type": "string", "default": "40" },
        "contract_type":     { "type": "string", "default": "2" },
        "default_bosu":      { "type": "integer", "default": 1800000 },
        "loss_reason_code":  { "type": "string", "default": "11" },
        "loss_detail_code":  { "type": "string" }
      }
    },
    "wage_ledger": {
      "type": "object",
      "description": "임금대장 컬럼좌표 (Master DB/보수총액용)",
      "properties": {
        "sheet":      { "type": "string" },
        "data_row":   { "type": "integer" },
        "name":       { "type": "integer" },
        "jumin":      { "type": "integer" },
        "hire_date":  { "type": "integer" },
        "quit_date":  { "type": "integer" },
        "total_wage": { "type": "integer" },
        "tax":        { "type": "integer" }
      }
    },
    "staff_source": {
      "type": "object",
      "description": "직원현황 시트 컬럼좌표 (type_b/c)",
      "properties": {
        "sheet": { "type": "string" }, "data_row": { "type": "integer" },
        "name": { "type": "integer" }, "jumin": { "type": "integer" },
        "hire_date": { "type": "integer" }, "quit_date": { "type": "integer" },
        "salary": { "type": "integer" }, "insurance": { "type": "integer" },
        "bank": { "type": "integer" }, "account": { "type": "integer" },
        "salary_unit": { "type": "number", "default": 1, "description": "급여 단위 배수 (만원→원 환산)" },
        "insurance_default": { "type": "string", "description": "보험 컬럼 없을 때 기본값" }
      }
    },
    "generic_reader": {
      "type": "object",
      "description": "범용 리더 (신규 사업장 코드 수정 불필요)",
      "properties": {
        "sheet": { "type": "string" },
        "data_row": { "type": "integer" },
        "columns": { "type": "object", "description": "키명→열번호" },
        "defaults": { "type": "object" },
        "exclude_rules": { "type": "array" }
      }
    },
    "tax_split": {
      "type": "object",
      "description": "세무분리 설정 (win32com — Step 0)"
    },
    "insurance_from_ledger": {
      "type": "object",
      "description": "임금대장 기반 4대보험 판단 override"
    },
    "calc_engine": {
      "type": "object",
      "description": "급여계산엔진 설정 (payroll_calc.py용)",
      "properties": {
        "wage_table": { "type": "object" },
        "tax_table_sheet": { "type": "string", "default": "세액표(1203)" }
      }
    }
  }
}
```

### 1-2. Excel 입력 → 통일 dict (EmployeeRecord)

모든 reader (`read_kitchen_staff`, `read_hall_staff`, `read_staff_source`,
`read_part_source`, `read_generic`)가 반환하는 공통 구조:

```json
{
  "title": "EmployeeRecord",
  "type": "object",
  "properties": {
    "성명":     { "type": "string" },
    "파트":     { "type": "string", "enum": ["주방", "홀", "파트", ""] },
    "근무타입": { "type": "string", "description": "주6풀, 주5, 찬모 등" },
    "직급":     { "type": "string" },
    "주민번호": { "type": "string", "description": "⚠ PII — 13자리" },
    "은행명":   { "type": "string", "description": "⚠ PII" },
    "계좌번호": { "type": "string", "description": "⚠ PII" },
    "연락처":   { "type": "string", "description": "⚠ PII" },
    "입사일":   { "type": ["string","null"], "format": "date" },
    "퇴사일":   { "type": ["string","null"], "format": "date" },
    "4대보험":  { "type": "string", "description": "유/무/X/F/미가입/프리랜서" },
    "4대보험입사일": { "type": ["string","null"], "description": "보험 가입 기준일 (파트→직원 전환)" },
    "급여":     { "type": "integer" },
    "추가금":   { "type": "integer", "default": 0 },
    "공제금":   { "type": "integer", "default": 0 },
    "비고":     { "type": "string" }
  }
}
```

### 1-3. Reader별 입력 소스 매핑

| Reader | reader_type | Excel 시트 | 시작행 | 특징 |
|--------|------------|-----------|--------|------|
| `read_kitchen_staff` | type_a | 주방직원 | 5 | 파트 컬럼 있음 |
| `read_hall_staff` | type_a | 홀직원 | 5 | 파트='홀' 고정 |
| `read_attendance` | type_a | 근태계산 | 5 | 근무일수/비고 |
| `read_staff_source` | type_b/c | YAML지정 | YAML지정 | salary_unit 적용 |
| `read_part_source` | type_b | YAML지정 | YAML지정 | 보험='X' 기본 |
| `read_generic` | generic | YAML지정 | YAML지정 | 컬럼좌표만으로 동작 |

### 1-4. 급여계산엔진 입력 (payroll_calc.py)

```json
{
  "title": "EmployeeInput",
  "type": "object",
  "properties": {
    "name":           { "type": "string" },
    "jumin_id":       { "type": "string" },
    "wage_type":      { "type": "string", "description": "조견표 키 (주6풀 등)" },
    "contract_wage":  { "type": "integer" },
    "additional":     { "type": "integer" },
    "bonus":          { "type": "integer" },
    "advance":        { "type": "integer" },
    "work_days":      { "type": "integer" },
    "absence_days":   { "type": "number" },
    "deduct_hours":   { "type": "number" },
    "hire_date":      { "type": "string" },
    "quit_date":      { "type": "string" },
    "group":          { "type": "string", "enum": ["executive","regular","part_time"] },
    "insurance_flag": { "type": "boolean" },
    "pension_exempt": { "type": "boolean" },
    "employ_exempt":  { "type": "boolean" },
    "mid_entry":      { "type": "boolean" },
    "mid_quit":       { "type": "boolean" },
    "dependents":     { "type": "integer", "default": 1 }
  }
}
```

---

## 2. 출력 인터페이스 정의 (현재)

### 2-1. 급여계산 결과 (EmployeePayroll)

`payroll_calc.py` → `EmployeePayroll` dataclass:

```json
{
  "title": "EmployeePayroll",
  "type": "object",
  "properties": {
    "name":          { "type": "string" },
    "group":         { "type": "string" },

    "_comment_earnings": "── 수당 분해 ──",
    "base_pay":      { "type": "integer", "description": "기본급" },
    "overtime1":     { "type": "integer", "description": "연장수당1" },
    "overtime2":     { "type": "integer", "description": "연장수당2" },
    "night_pay":     { "type": "integer", "description": "야간수당" },
    "extra_pay":     { "type": "integer", "description": "추가수당 (역산)" },
    "leave_pay":     { "type": "integer", "description": "연차수당" },
    "additional":    { "type": "integer", "description": "추가금" },
    "bonus":         { "type": "integer", "description": "상여금" },

    "_comment_work": "── 근무/공제 ──",
    "work_days":     { "type": "integer" },
    "absence_days":  { "type": "integer" },
    "absence_deduct":{ "type": "integer", "description": "휴무공제" },
    "deduct_hours":  { "type": "number" },
    "time_deduct":   { "type": "integer", "description": "시간공제" },
    "gross":         { "type": "integer", "description": "임금총액" },

    "_comment_deductions": "── 세금/보험 공제 ──",
    "income_tax":    { "type": "integer", "description": "소득세 (간이세액표)" },
    "resident_tax":  { "type": "integer", "description": "지방소득세 = 소득세×10%" },
    "pension":       { "type": "integer", "description": "국민연금" },
    "health":        { "type": "integer", "description": "건강보험" },
    "ltc":           { "type": "integer", "description": "장기요양" },
    "employment":    { "type": "integer", "description": "고용보험" },
    "other_deduct":  { "type": "integer", "description": "기타공제" },

    "_comment_totals": "── 합계 ──",
    "total_deduct":  { "type": "integer", "description": "공제액 합계" },
    "net_pay":       { "type": "integer", "description": "실지급액" },

    "_comment_meta": "── 메타 ──",
    "hourly_rate":   { "type": "integer", "description": "통상시급" },
    "contract_wage": { "type": "integer", "description": "계약임금" },
    "wage_type":     { "type": "string" },
    "jumin_id":      { "type": "string", "description": "⚠ PII" },
    "hire_date":     { "type": "string" },
    "quit_date":     { "type": "string" }
  }
}
```

### 2-2. 4대보험 판단 결과 (insurance.py)

`assess_insurance()` 반환:

```json
{
  "title": "InsuranceAssessment",
  "type": "object",
  "properties": {
    "국민연금":  { "type": "integer", "description": "공제액 (0=미공제)" },
    "건강보험":  { "type": "integer" },
    "장기요양":  { "type": "integer" },
    "고용보험":  { "type": "integer" },
    "판단사유": {
      "type": "object",
      "properties": {
        "국민연금": { "type": "string", "example": "만62세 → 60세 이상 미공제" },
        "건강보험": { "type": "string" },
        "장기요양": { "type": "string" },
        "고용보험": { "type": "string" }
      }
    },
    "flags": {
      "type": "object",
      "properties": {
        "만60세이상": { "type": "boolean" },
        "외국인":     { "type": "boolean" },
        "중도입사":   { "type": "boolean" },
        "퇴사월":     { "type": "boolean" },
        "건보정산":   { "type": "object", "description": "퇴사 시 보수총액 정산 결과" }
      }
    }
  }
}
```

### 2-3. 파이프라인 Step 결과

| Step | 함수 | 반환형 | 핵심 필드 |
|------|------|--------|----------|
| 0 | `step0_tax_split` | dict | `status`, `emp_count`, `part_count`, `daily_workers` |
| 1 | `step1_copy_and_prepare` | str\|None | 생성된 파일 경로 |
| 2 | `step2_fill_regular` | bool | 성공/실패 |
| 3 | `step3_acquisition_report` | bool | 성공/실패 (파일 생성) |
| 4 | `step4_loss_report` | bool | 성공/실패 (파일 생성) |
| 5 | `step5_daily_worker_report` | bool | 성공/실패 (파일 생성) |

### 2-4. Privacy Broker 정화 후 최종 출력

```json
{
  "title": "BrokerResponse",
  "type": "object",
  "required": ["ok", "job_id"],
  "properties": {
    "ok":       { "type": "boolean" },
    "job_id":   { "type": "string", "pattern": "^job-\\d{8}-\\d{6}$" },
    "code":     { "type": "string", "description": "에러 코드 (실패 시)" },
    "message":  { "type": "string", "description": "정화된 메시지" },
    "data":     { "type": "object", "description": "명령별 결과 (PII 제거됨)" },
    "hint":     { "type": "string", "description": "상세는 logs/secure/ 참조" }
  }
}
```

### 2-5. 중도퇴사 연말정산 결과 (severance.py — calc_mid_year_settlement)

> 근거: seojaehong/hrms@6749897cae:docs/korea/04-year-end-settlement.md §6

```json
{
  "title": "MidYearSettlementExport",
  "type": "object",
  "description": "중도퇴사 연말정산 7단계 계산 결과",
  "properties": {
    "_step1": "── Step 1~2 ──",
    "총급여":          { "type": "integer", "description": "연간 급여합계 - 비과세" },
    "근로소득공제":     { "type": "integer", "description": "구간표 적용 (docs/korea/03 §5)" },
    "근로소득금액":     { "type": "integer", "description": "총급여 - 근로소득공제" },

    "_step3_4": "── Step 3~4: 소득공제 ──",
    "선택방법":        { "type": "string", "enum": ["A", "B"], "description": "유불리 자동 비교 결과" },
    "인적공제":        { "type": "integer", "const": 1500000, "description": "본인 기본공제 150만" },
    "국민연금공제":     { "type": "integer", "description": "당해 국민연금 기납부액" },
    "보험료합계":       { "type": "integer", "description": "건강+장기+고용 (Method A/B 판단 기준)" },
    "보험료특별소득공제": {
      "type": "integer",
      "description": "Method A: 보험료합계 적용 (§52①). Method B: 0원. ⚠ 이 차이가 유불리의 핵심"
    },
    "소득공제합계":     { "type": "integer" },

    "_step5_6": "── Step 5~6: 세액 ──",
    "과세표준":        { "type": "integer", "description": "근로소득금액 - 소득공제합계 (0 이상)" },
    "산출세액":        { "type": "integer", "description": "기본세율 적용 (docs/korea/03 §4)" },
    "근로소득세액공제":  { "type": "integer", "description": "docs/korea/03 §6 구간표" },
    "표준세액공제":     {
      "type": "integer",
      "description": "Method B: min(130,000, 산출세액-근로소득세액공제). Method A: 0. ⚠ §59의4⑨"
    },
    "세액공제합계":     { "type": "integer" },
    "결정세액":        { "type": "integer", "description": "산출세액 - 세액공제합계 (0 이상)" },
    "결정지방소득세":   { "type": "integer", "description": "결정세액 × 10%" },

    "_step7": "── Step 7: 차감징수 ──",
    "기납부소득세":     {
      "type": "integer",
      "description": "⚠ CRITICAL: 퇴직월 이전까지의 소득세 합계. 퇴직월 소득세는 정산결과 자체이므로 절대 포함 금지. (docs/korea/04 §6-5 사고 사례 참조)"
    },
    "기납부지방소득세":  { "type": "integer" },
    "차감징수소득세":   { "type": "integer", "description": "10원 올림 (ceil). ⚠ 퇴직소득세(floor)와 반대 방향" },
    "차감징수지방소득세": { "type": "integer" },
    "차감징수합계":     { "type": "integer", "description": "양수=추가납부, 음수=환급" },

    "_comparison": "── Method 비교 ──",
    "Method_A_결정세액": { "type": "integer", "description": "보험료공제 적용 시 결정세액" },
    "Method_B_결정세액": { "type": "integer", "description": "표준세액공제 적용 시 결정세액" }
  }
}
```

**Method A vs B 자동 판단 규칙** (docs/korea/04 §6-3 인용):
```
보험료합 = 건강 + 장기 + 고용보험
절세효과_A = 보험료합 × 한계세율
절세효과_B = 130,000 (표준세액공제)
→ 결정세액이 작은 쪽 선택 (금액 기반, 세율 근사 아님)
```

**검증 이력**: 32건 PASS (올웨이즈샤브 28건 + 다이닝원 4건)
- 이승준(3,240만) = Method A (고소득 → 보험료공제 유리)
- 나머지 31건 = Method B (저소득 → 표준세액공제 유리)

**Validation Rule**:
```python
assert abs(차감징수소득세) <= 기납부소득세 or 차감징수소득세 >= 0
# 환급액은 기납부를 초과할 수 없음
```

### 2-6. 퇴직금 계산 결과 (severance.py — calc_severance_pay)

> 근거: seojaehong/hrms@6749897cae:docs/korea/05-severance.md

```json
{
  "title": "SeverancePayExport",
  "type": "object",
  "description": "퇴직금 계산 결과 (고용노동부 기준 3개월 평균임금)",
  "properties": {
    "_dates": "── 날짜 ──",
    "입사일":    { "type": "string", "format": "date" },
    "퇴사일":    { "type": "string", "format": "date", "description": "마지막 근무일" },
    "퇴직일":    { "type": "string", "format": "date", "description": "⚠ 퇴사일 + 1일 (docs/korea/05 §2)" },
    "재직일수":   { "type": "integer", "description": "퇴직일 - 입사일" },

    "_3month": "── 3개월 평균임금 산정 ──",
    "3개월_시작": { "type": "string", "format": "date", "description": "퇴직일 역산 3개월" },
    "3개월_종료": { "type": "string", "format": "date" },
    "3개월_총일수": { "type": "integer", "description": "3개월간 총 역일수 (calendar days)" },
    "임금총액_A":   { "type": "integer", "description": "3개월간 임금총액 (일할계산 포함)" },
    "상여금가산_B":  { "type": "integer", "description": "연간상여금 × 3/12" },
    "연차수당가산_C": { "type": "integer", "description": "연차수당일급 × 미사용일수 × 3/12" },
    "평균임금산정기초액": { "type": "integer", "description": "A + B + C" },
    "1일평균임금":  { "type": "number", "description": "기초액 / 3개월_총일수 (소수점)" },
    "1일통상임금":  { "type": "integer", "description": "통상임금 (비교용)" },
    "적용임금종류":  { "type": "string", "enum": ["평균임금", "통상임금"], "description": "둘 중 큰 쪽 적용" },
    "적용1일임금":  { "type": "number" },

    "_result": "── 퇴직금 ──",
    "퇴직금":     { "type": "integer", "description": "적용1일임금 × 30 × (재직일수/365) — 원 단위 절사" }
  }
}
```

### 2-7. 퇴직소득세 결과 (severance.py — calc_severance_income_tax)

> 근거: seojaehong/hrms@6749897cae:docs/korea/05-severance.md §4

```json
{
  "title": "SeveranceTaxExport",
  "type": "object",
  "description": "퇴직소득세 계산 결과",
  "properties": {
    "퇴직소득":        { "type": "integer", "description": "= 퇴직금" },
    "근속연수":        { "type": "integer", "description": "1년 미만 올림" },
    "공제적용근속연수":  { "type": "integer", "description": "2012년 이후 입사: 근속연수와 동일" },
    "근속연수공제":     { "type": "integer", "description": "5년이하 100만×N, 10년이하 500만+200만×(N-5), ..." },
    "환산급여":        { "type": "integer", "description": "(퇴직소득 - 근속연수공제) × 12 / 근속연수" },
    "환산급여공제":     { "type": "integer", "description": "800만이하 전액, 7000만이하 800만+60%, ..." },
    "과세표준":        { "type": "integer", "description": "환산급여 - 환산급여공제" },
    "환산산출세액":     { "type": "integer", "description": "기본세율 적용" },
    "퇴직소득산출세액":  { "type": "integer", "description": "환산세액 × 근속연수 / 12" },
    "소득세":          { "type": "integer", "description": "⚠ 10원 절사 (floor) — 연말정산(ceil)과 반대" },
    "지방소득세":       { "type": "integer", "description": "소득세 × 10% → 10원 절사" },
    "세금합계":        { "type": "integer" }
  }
}
```

**Edge Cases** (docs/korea/05 §6 인용):

| 케이스 | 엔진 처리 | 비고 |
|--------|----------|------|
| 재직 1년 미만 | `calc_severance_pay` → return 0 (퇴직금 없음) | 법정 최소 요건 |
| 파트→정직원 전환 | 커스텀 퇴직금 (전체급여/12) → 별도 산정서 | docs/korea/05 §6-1 |
| DAY(퇴직일)=1 | 퇴사일이 전월 말일 → 3개월 기간 시프트 | docs/korea/05 §6-3 |
| DC형 퇴직연금 | 엔진 미처리 — 퇴직연금 사업자가 계산 | 현 사업장 전부 DB형/퇴직금 |
| 중간정산 | 엔진 미처리 — 수동 진행 (빈도 극히 낮음) | 향후 Frappe에서 이력 관리 가능 |

### 2-8. 퇴직 통합 Export (퇴직금 + 퇴직소득세 + 중도퇴사 연말정산)

```json
{
  "title": "TerminationSettlementExport",
  "type": "object",
  "description": "퇴직 시 통합 정산 결과 — 3개 계산의 합본",
  "properties": {
    "employee_token": { "type": "string", "description": "비식별 ID (broker 경유)" },
    "site_key":       { "type": "string" },
    "settlement_date": { "type": "string", "format": "date" },
    "severance":       { "$ref": "#SeverancePayExport" },
    "severance_tax":   { "$ref": "#SeveranceTaxExport" },
    "mid_year_tax":    { "$ref": "#MidYearSettlementExport" },
    "net_severance":   {
      "type": "integer",
      "description": "퇴직금 실수령 = 퇴직금 - 퇴직소득세 - 퇴직지방소득세"
    },
    "final_salary_adjustment": {
      "type": "integer",
      "description": "마지막 급여 차감징수세액 (연말정산 결과)"
    }
  }
}
```

---

## 3. API 노출 방식 — 3옵션 비교

### Option A: CLI + 파일 Export/Import

```
Frappe → (HTTP/webhook) → privacy_broker.py CLI → 결과 JSON → Frappe
         또는 파일시스템 공유 폴더 (NFS/SMB)
```

| 항목 | 평가 |
|------|------|
| 변경량 | **최소** — 현 CLI 그대로 유지 |
| 안전성 | **최고** — 기존 운영 zero impact |
| 성능 | 프로세스 기동 오버헤드 (~2초) |
| 확장성 | 낮음 — 동시 처리 불가 (파일 잠금) |
| 운영 | 배치 스크립트 스케줄 필요 |
| 멱등성 | 파일 존재 체크로 자연 보장 |

### Option B: FastAPI 얇은 REST 래퍼 ⭐ 추천

```
Frappe → HTTP POST → FastAPI wrapper → privacy_broker.dispatch() → JSON
```

```python
# api_wrapper.py (신규 파일 ~100줄)
from fastapi import FastAPI, HTTPException
from privacy_broker import dispatch, load_routing, setup_logging, build_parser
import argparse

app = FastAPI(title="Payroll Engine API", version="1.0")

@app.post("/api/v1/{command}")
async def execute(command: str, body: dict):
    routing = load_routing()
    broker_log, secure_log = setup_logging()
    args = argparse.Namespace(**body, command=command)
    result = dispatch(command, args, routing, broker_log, secure_log)
    return result
```

| 항목 | 평가 |
|------|------|
| 변경량 | **소** — 신규 파일 1개 (api_wrapper.py), 기존 코드 변경 0 |
| 안전성 | **높음** — dispatch() 재사용, broker 경계 유지 |
| 성능 | 프로세스 상주 → 응답 ~500ms |
| 확장성 | uvicorn workers로 수평 확장 |
| 운영 | systemd/docker로 서비스화 |
| 멱등성 | job_id 기반 중복 방지 구현 필요 |

### Option C: Celery/큐 기반 비동기

```
Frappe → Redis/RabbitMQ → Celery worker → privacy_broker.dispatch() → 결과 저장
                                                                    ↓
Frappe ← polling/webhook ← 결과 조회 ←──────────────────────────────
```

| 항목 | 평가 |
|------|------|
| 변경량 | **중** — Celery + 메시지 브로커 인프라 |
| 안전성 | 높음 — 비동기 격리 |
| 성능 | 최고 — 대량 배치 병렬 처리 |
| 확장성 | 최고 — worker 무한 확장 |
| 운영 | 복잡 — Redis + Celery 모니터링 |
| 멱등성 | task_id 기반 자연 보장 |

### 추천: **Option B (FastAPI)**

이유:
1. **변경 최소**: `api_wrapper.py` 1개 추가, 기존 코드 0줄 수정
2. **broker 경계 유지**: `dispatch()` 함수를 HTTP 진입점으로 감싸는 것뿐
3. **점진적 확장**: A→B는 자연스러운 진화, B→C는 나중에 필요 시 전환
4. **win32com 제약**: Step 0(세무분리)은 Windows 전용 → API 서버도 Windows → Celery 부적합
5. **현 규모(20개 사업장)**: 동시성 이슈 없음, 큐 인프라는 과도

---

## 4. Privacy Broker 경계 매핑

### 4-1. 계산 단계별 PII 필요도

```
┌───────────────────────────────────────────────────────────────┐
│                    PII-FREE ZONE (Frappe 측)                  │
│                                                               │
│  사업장 선택 → site_key (ASCII)                              │
│  요율 조회   → RATES dict (공개 데이터)                      │
│  최저임금    → MINIMUM_WAGE[year] (공개 데이터)              │
│  세율표     → TAX_BRACKETS (공개 데이터)                     │
│  단수처리    → floor10(), ceil10() (순수 함수)                │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│              BROKER BOUNDARY (privacy_broker.py)              │
├───────────────────────────────────────────────────────────────┤
│                    PII ZONE (Worker 내부)                     │
│                                                               │
│  직원 목록 읽기  → 주민번호, 이름, 계좌 (Excel)              │
│  연령 판단      → 주민번호 앞6자리 (생년)                    │
│  보험 판단      → 주민번호 + 입사일                          │
│  보수총액 계산  → 주민번호 = Master DB CSV 키                │
│  신고서 작성    → 주민번호 + 이름 + 보수 (Excel 템플릿)      │
│  급여이체 준비  → 계좌번호 + 실지급액                        │
│  PDF 출력      → 전체 PII (win32com Excel→PDF)               │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 4-2. 항목별 PII 매핑

| 계산 항목 | 필요한 PII | PII 용도 | 대체 가능? |
|----------|-----------|---------|-----------|
| **소득세 (간이세액표)** | 없음 (과세급여+가족수) | — | ✅ PII-free |
| **소득세 (기본세율)** | 없음 (과세표준) | — | ✅ PII-free |
| **국민연금 요율 계산** | 없음 (과세급여) | — | ✅ PII-free |
| **국민연금 면제 판단** | 주민번호 앞6 | 만60세 판단 | ❌ 생년월일 필수 |
| **국민연금 고지액** | 없음 (고정액) | — | ✅ PII-free |
| **건강보험 계산** | 없음 (과세급여) | — | ✅ PII-free |
| **건보 보수총액 정산** | 주민번호 | Master DB 키 | ❌ 개인 식별 필수 |
| **고용보험 면제 판단** | 주민번호 앞6 + 입사일 | 만65세@입사 판단 | ❌ 생년월일 필수 |
| **외국인 19% 단일세율** | 주민번호 7번째 자리 | 외국인 여부 | ⚠ visa_type으로 대체 가능 |
| **외국인 보험 면제** | 비자 유형 | 고용보험 판단 | ⚠ 비자는 PII가 아닌 속성 |
| **퇴직금 3개월 평균** | 없음 (급여 데이터) | — | ✅ PII-free |
| **퇴직소득세** | 없음 (퇴직금+근속연수) | — | ✅ PII-free |
| **중도퇴사 연말정산** | 없음 (급여합계+보험료) | — | ✅ PII-free |
| **취득/상실 신고서** | 주민번호 전체 + 이름 | 신고 양식 기재 | ❌ 법적 필수 |
| **급여 이체** | 계좌번호 + 이름 | 은행 API | ❌ 금융 필수 |
| **사업소득자 감지** | 없음 (세금/급여 비율) | — | ✅ PII-free |

### 4-3. PII-free 계산 분리 가능 범위

```
PII-free로 Frappe에 노출 가능한 계산:
  ✅ 소득세 (간이세액표 lookup — 과세급여 + 가족수만 필요)
  ✅ 4대보험 요율 계산 (과세급여 × 요율)
  ✅ 단수처리 (floor10, ceil10)
  ✅ 최저임금 검증
  ✅ 퇴직금 계산 (급여 데이터 → 금액)
  ✅ 퇴직소득세 계산
  ✅ 중도퇴사 연말정산 Method A/B 비교

PII 필수 (broker 경유 필수):
  ❌ 연령 기반 면제 판단 (주민번호 → 생년)
  ❌ 외국인 판별 (주민번호 7번째 자리)
  ❌ 보수총액 정산 (주민번호 = DB 키)
  ❌ 신고서 생성 (주민번호+이름 기재)
  ❌ 급여이체 (계좌번호)
```

### 4-4. 감사 로그 패턴

```
# broker.audit.log (비식별 — 외부 노출 가능)
2026-04-25 14:30:00 | job-20260425-143000 | cmd=insurance-acq | site=bupyeong
2026-04-25 14:30:05 | job-20260425-143000 | ok=True | code=SUCCESS

# worker.secure.log (PII 포함 — 로컬 전용, 외부 전송 금지)
2026-04-25 14:30:01 | job-20260425-143000 | 김철수 870923-1*** → 취득신고 생성
2026-04-25 14:30:02 | job-20260425-143000 | TOKEN_MAP | {"emp_001":"김철수","emp_002":"박영희"}
```

---

## 5. Frappe Push 인터페이스

### 5-1. 계산 완료 후 Push 형식

엔진 계산 완료 → Frappe `Salary Slip` DocType에 push:

```json
{
  "title": "FrappeSalarySlipPush",
  "type": "object",
  "properties": {
    "employee":       { "type": "string", "description": "Frappe employee_id (HR-EMP-XXXX)" },
    "posting_date":   { "type": "string", "format": "date" },
    "company":        { "type": "string" },
    "branch":         { "type": "string" },

    "earnings": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "salary_component": { "type": "string" },
          "amount":           { "type": "integer" }
        }
      },
      "example": [
        { "salary_component": "기본급", "amount": 2156880 },
        { "salary_component": "연장수당", "amount": 162024 },
        { "salary_component": "야간수당", "amount": 45000 },
        { "salary_component": "식대", "amount": 200000 }
      ]
    },

    "deductions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "salary_component": { "type": "string" },
          "amount":           { "type": "integer" }
        }
      },
      "example": [
        { "salary_component": "국민연금", "amount": 209900 },
        { "salary_component": "건강보험", "amount": 85500 },
        { "salary_component": "장기요양", "amount": 11230 },
        { "salary_component": "고용보험", "amount": 21380 },
        { "salary_component": "소득세", "amount": 45670 },
        { "salary_component": "지방소득세", "amount": 4567 }
      ]
    },

    "gross_pay":     { "type": "integer" },
    "total_deduction": { "type": "integer" },
    "net_pay":       { "type": "integer" },

    "_engine_meta": {
      "type": "object",
      "description": "엔진 메타 (Frappe custom field에 저장)",
      "properties": {
        "engine_version":   { "type": "string" },
        "job_id":           { "type": "string" },
        "calculation_time": { "type": "string", "format": "date-time" },
        "insurance_reasons":{ "type": "object" }
      }
    }
  }
}
```

### 5-2. 실패 시 재시도/롤백

| 상황 | 정책 |
|------|------|
| Frappe API timeout | 3회 exponential backoff (1s, 5s, 15s) |
| Frappe validation error | 롤백 불필요 (push 실패 = 미반영) |
| 부분 push (10명 중 3명 실패) | 성공분 유지, 실패분만 재시도 |
| 중복 push | `job_id + employee + posting_date` 복합키로 멱등 보장 |
| 엔진 계산 오류 | push 안 함 → 수동 확인 후 재실행 |

**멱등성 보장 방법:**
```python
# Frappe 측 custom field: kr_engine_job_id
# Push 전 확인:
existing = frappe.get_all("Salary Slip", filters={
    "kr_engine_job_id": job_id,
    "employee": employee_id,
})
if existing:
    # 이미 push됨 → skip 또는 update
    pass
```

### 5-3. 사번 매핑 테이블

```json
{
  "title": "EmployeeMapping",
  "type": "object",
  "description": "privacy_broker 내부에서만 관리. Frappe→엔진 단방향 조회.",
  "properties": {
    "frappe_id":     { "type": "string", "example": "HR-EMP-00042" },
    "site_key":      { "type": "string", "example": "bupyeong" },
    "engine_token":  { "type": "string", "example": "emp_003", "description": "세션별 임시 토큰" },
    "jumin_hash":    { "type": "string", "description": "SHA256(주민번호) — 매핑 검증용" }
  }
}
```

**저장 위치**: `config/private/employee_mapping.yaml` (gitignore)

**매핑 흐름:**
```
1. Frappe에서 신규 Employee 생성 → HR-EMP-XXXX
2. 관리자가 매핑 등록: frappe_id ↔ site_key + jumin_hash
3. 엔진 실행 시: jumin → hash → frappe_id 조회 → push 대상 결정
4. jumin 자체는 매핑 테이블에 저장 안 함 (hash만)
```

---

## 6. docs/korea/ 갭 분석

### 범례
- ✅ **완료**: 운영 중, 실데이터 검증 완료
- ⚠ **부분**: 로직 존재하나 일부 누락/미검증
- ❌ **미구현**: 코드 없음

### 6-1. 02-social-insurance.md (4대보험)

| Spec 항목 | 현 엔진 | 파일 | 상세 |
|-----------|---------|------|------|
| 2026 요율 | ✅ | `insurance.py:32-37` | RATES dict 정확 |
| 국민연금 상한/하한 | ⚠ | `insurance.py` | 하한만, **상한 미구현** (6,370,000) |
| 건강보험 계산 | ✅ | `insurance.py:120-122` | `floor10(wage * 0.03595)` |
| 장기요양 계산 | ✅ | `insurance.py:125-127` | `floor10(health * 0.1314)` |
| 고용보험 계산 | ✅ | `insurance.py:130-132` | `floor10(wage * 0.009)` |
| 중도입사 첫달 규칙 | ✅ | `insurance.py:85-101` | 국연/건보/장기=0, 고용=공제 |
| 1일입사 규칙 | ✅ | `insurance.py:95-100` | 전체 공제 |
| 중도퇴사 규칙 | ✅ | `insurance.py:103-108` | 그대로 공제 |
| 당월입퇴사 | ⚠ | `engine.py` | 감지 로직 있으나 보험 판단에 미통합 |
| 만60세 국민연금 면제 | ✅ | `insurance.py:187-189` | `over_60` 체크 |
| 만65세 고용보험 면제 (입사기준) | ⚠ | `insurance.py` | 외국인만 `foreign_employ_exempt`, **내국인 65세 미구현** |
| 건보 보수총액 정산 | ✅ | `insurance.py` | `ytd_wages` 파라미터로 지원 |
| 산정월수≠납부월수 | ✅ | `insurance.py` | 중도입사 시 납부월수 -1 |
| 연단위 정산 경계 | ✅ | 메모리 문서 | 연도별 분리 규칙 |
| 외국인 비자별 고용보험 | ⚠ | `insurance.py:44-49` | `is_foreigner()` 있으나 비자별 세분화 미구현 |
| 고용안정 사업주 요율 | ❌ | — | 사업주측 미구현 (근로자 공제만) |
| 산재보험 | ❌ | — | 사업주 전액 → 급여 공제 대상 아님 |

### 6-2. 03-income-tax.md (소득세)

| Spec 항목 | 현 엔진 | 파일 | 상세 |
|-----------|---------|------|------|
| 간이세액표 조회 | ✅ | `payroll_calc.py:107-158` | Excel 세액표 시트에서 로드 |
| 맞춤형 원천징수 (80/100/120%) | ⚠ | `payroll_calc.py` | dependents 파라미터 있으나 배율 옵션 미노출 |
| 지방소득세 = 소득세×10% | ✅ | `payroll_calc.py:86` | `resident_tax` 필드 |
| 기본세율표 | ✅ | `severance.py` | 퇴직소득세용으로 구현 |
| 근로소득공제 구간표 | ✅ | `severance.py` | 연말정산용 |
| 근로소득세액공제 | ✅ | `severance.py` | 연말정산용 |
| 사업소득자 3% 감지 | ✅ | `engine.py:206-212` | `wage × 3% ±100원` 판별 |
| 고소득 1천만↑ 누진세 | ✅ | `payroll_calc.py:150-154` | `_calc_high_income_tax()` |

### 6-3. 04-year-end-settlement.md (연말정산)

| Spec 항목 | 현 엔진 | 파일 | 상세 |
|-----------|---------|------|------|
| 7단계 계산 | ⚠ | `severance.py` | 중도퇴사용만 구현 (계속근로자 미구현) |
| Method A vs B 자동 비교 | ✅ | `severance.py` | 32건 검증 완료 |
| 기납부세액 산정 | ✅ | `severance.py` | 퇴직월 제외 규칙 |
| 차감징수 10원 올림 | ✅ | `payroll_calc.py:28-29` | `ceil10()` |
| 계속근로자 연말정산 | ❌ | — | 미구현 (외부 홈택스 처리) |
| 특별세액공제 (의료/교육/기부) | ❌ | — | 중도퇴사 시 미적용 → 미구현 |
| 신용카드 소득공제 | ❌ | — | 미구현 |

### 6-4. 05-severance.md (퇴직금)

| Spec 항목 | 현 엔진 | 파일 | 상세 |
|-----------|---------|------|------|
| 퇴직일 = 퇴사일+1 | ✅ | `severance.py:34` | `last_work_date + timedelta(1)` |
| 3개월 평균임금 | ✅ | `severance.py:42-53` | A+B+C / 총일수 |
| 상여금 가산 (3/12) | ✅ | `severance.py:46` | `annual_bonus * 3 // 12` |
| 연차수당 가산 (3/12) | ✅ | `severance.py:49` | 구현 완료 |
| 통상임금 비교 | ✅ | `severance.py:57-59` | fallback 로직 |
| 퇴직소득세 계산 | ✅ | `severance.py` | 근속연수공제+환산 |
| 퇴직소득세 10원 절사 | ✅ | `payroll_calc.py:22-24` | `floor10()` |
| 국세청 프로그램 2차검증 | ✅ | 프로세스 | xlsm 프로그램 대조 |
| 커스텀 퇴직금 (합의) | ✅ | 운영 | 별도 산정서 생성 |

### 6-5. 06-minimum-wage.md (최저임금)

| Spec 항목 | 현 엔진 | 파일 | 상세 |
|-----------|---------|------|------|
| 2026 시급 10,320원 | ⚠ | `wage_table.py` | 조견표에 반영되나 **검증 로직 없음** |
| 월급 2,156,880원 | ⚠ | `wage_table.py` | 조견표 기본급으로 사용 중 |
| 미달 경고 | ❌ | — | 자동 검증/경고 미구현 |
| 파트타임 환산 | ❌ | — | 미구현 |

### 6-6. 07-working-hours.md (근로시간)

| Spec 항목 | 현 엔진 | 파일 | 상세 |
|-----------|---------|------|------|
| 통상시급 = 월급/209 | ✅ | `wage_table.py` | 조견표 시급 열 |
| 연장수당 ×1.5 | ✅ | `payroll_calc.py` | `overtime1`, `overtime2` |
| 야간수당 ×0.5 추가 | ✅ | `payroll_calc.py` | `night_pay` |
| 휴일수당 8h이내 ×1.5 | ⚠ | `payroll_calc.py` | 조견표 기반 고정 — 시간별 동적 계산 미구현 |
| 휴일수당 8h초과 ×2.0 | ❌ | — | 미구현 |
| 가산 중복 적용 | ❌ | — | 미구현 (조견표가 사전 계산) |
| 주휴수당 (주15h↑) | ⚠ | — | 조견표에 포함되나 15h 미만 판단 미구현 |
| 52시간 한도 검증 | ❌ | — | 미구현 |

### 6-7. 08-daily-workers.md (일용직)

| Spec 항목 | 현 엔진 | 파일 | 상세 |
|-----------|---------|------|------|
| 150,000 기본공제 | ⚠ | `engine.py` | 세무분리 시 일용 시트에 기재하나 세금 계산은 Excel 수식 의존 |
| 6% 세율 | ⚠ | — | Excel 수식 의존 (엔진 자체 계산 없음) |
| 55% 세액공제 | ⚠ | — | Excel 수식 의존 |
| 소액부징수 1,000원 | ⚠ | — | Excel 수식 의존 |
| 근로내용확인신고서 | ✅ | `engine.py:804-850` | 템플릿 기반 생성 |
| 고용보험 0.9% 적용 | ✅ | `engine.py:653` | `employ_insurance_rate` |
| 120만↑ 사업소득 전환 | ✅ | `engine.py:634-635` | threshold 기반 분류 |

### 6-8. 09-foreign-workers.md (외국인)

| Spec 항목 | 현 엔진 | 파일 | 상세 |
|-----------|---------|------|------|
| 외국인 판별 | ✅ | `insurance.py:44-49` | 주민번호 7번째 자리 (5,6,7,8) |
| 19% 단일세율 | ❌ | — | 미구현 |
| 비자별 고용보험 | ⚠ | `insurance.py` | `foreign_employ_exempt` 플래그만 (비자 세분화 없음) |
| F-4 임의가입/소급불가 | ⚠ | 운영 지식 | 코드화 안 됨 |
| 국민연금 상호주의 | ❌ | — | 미구현 |
| 고용보험 동의서 PDF | ✅ | `workers/gen_consent.py` | 빈양식+데이터+도장 |

---

### 6-9. 갭 우선순위 (운영 영향도 기준)

| 우선순위 | 갭 항목 | 영향도 | 이유 |
|---------|---------|--------|------|
| **P0** | 국민연금 상한 미구현 | 🔴 | 고소득자 과공제 (월 637만 이상) |
| **P0** | 내국인 65세 고용보험 면제 | 🔴 | 현재 외국인만 처리 → 내국인 누락 |
| **P1** | 당월입퇴사 보험 판단 통합 | 🟡 | 감지는 되나 assess_insurance 미연동 |
| **P1** | 외국인 비자별 고용보험 세분화 | 🟡 | F-2/F-5/F-6 의무 vs F-4 임의 구분 |
| **P1** | 최저임금 자동 검증 | 🟡 | 미달 시 무경고 |
| **P2** | 외국인 19% 단일세율 | 🟡 | 현재 수동 처리 |
| **P2** | 일용직 세금 엔진 자체 계산 | 🟡 | Excel 수식 의존 → SaaS 불가 |
| **P2** | 맞춤형 원천징수 80/120% | 🟢 | 100% 고정 운영 중 |
| **P3** | 휴일수당 8h 초과 ×2.0 | 🟢 | 조견표 사전 계산 |
| **P3** | 52시간 한도 검증 | 🟢 | 현 사업장 초과 없음 |
| **P3** | 계속근로자 연말정산 | 🟢 | 홈택스 외부 처리 |
| **P3** | 국민연금 상호주의 (외국인) | 🟢 | 현재 수동 판단 |
| **P3** | 산재보험/고용안정 사업주 요율 | 🟢 | 급여 공제 아님 |

---

## 부록 A: 현 엔진 모듈 맵

```
src/
├── config.py          LocationConfig (YAML → dataclass)
├── readers.py         Excel 시트 → list[dict] (6종 reader)
├── engine.py          Step 0~5 파이프라인 + Master DB
├── utils.py           날짜/주민번호/이름 유틸리티
├── insurance.py       assess_insurance() — 4대보험 판단+계산
├── severance.py       퇴직금 + 퇴직소득세 + 중도퇴사 연말정산
├── payroll_calc.py    급여계산엔진 (수당분해, 세액표, Gross→Net)
├── wage_table.py      급여조견표 로더 (Excel Sheet2 → dict)
└── excel_writer.py    Excel 셀 기입 (payroll_calc 결과 → Excel)

workers/
├── payroll_runner.py      급여 요약/상세 (비식별 조회)
├── gen_insurance_report.py 4대보험 신고서 생성
├── gen_consent.py          외국인 동의서 PDF
├── accounting_runner.py    세무변환/퇴직금/건보정산
├── jecheon_runner.py       제천 커스텀
└── secure_llm.py           RunPod LLM 경유

privacy_broker.py          중앙 진입점 (PII 정화)
config/public/routing.yaml 비식별 라우팅 (20개 사업장)
config/private/            PII 설정 (gitignore)
```

## 부록 B: 요율/상수 변경 시 수정 위치

| 변경 항목 | 수정 파일 | 변수 |
|----------|----------|------|
| 국민연금 요율 | `insurance.py:33` | `RATES['국민연금']` |
| 건강보험 요율 | `insurance.py:34` | `RATES['건강보험']` |
| 장기요양 요율 | `insurance.py:35` | `RATES['장기요양']` |
| 고용보험 요율 | `insurance.py:36` | `RATES['고용보험']` |
| 국민연금 상한/하한 | `insurance.py` | **미구현 → 추가 필요** |
| 최저임금 | `wage_table.py` | 조견표 Excel에 반영 |
| 소득세율 | `severance.py` | `TAX_BRACKETS` |
| 간이세액표 | Excel 파일 내 시트 | 매년 NTS CSV import |
