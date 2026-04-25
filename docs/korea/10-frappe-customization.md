# 10. Frappe HR 커스터마이징 가이드

> Frappe HRMS Korea — Integration & Customization Specification
> Status: Draft | Phase: 4 (Integration)

---

## 1. Frappe HR Architecture Overview

```
Frappe Framework
└── HRMS App
    ├── hr/          → Employee lifecycle, leave, attendance
    ├── payroll/     → Salary structure, slips, payroll entry
    └── regional/    → Country-specific modules
        ├── india/   → India tax (existing)
        ├── united_arab_emirates/ → UAE (existing)
        └── south_korea/  → 🆕 Korea module (this project)
```

### Key DocTypes to Customize

| DocType | Korean | Purpose |
|---------|--------|---------|
| Employee | 직원 | Add Korean-specific fields |
| Salary Component | 급여 구성요소 | Korean earning/deduction types |
| Salary Structure | 급여 구조 | Korean payroll template |
| Salary Slip | 급여명세서 | Korean calculation hooks |
| Payroll Entry | 급여 처리 | Batch processing with Korean rules |

---

## 2. Custom Fields on Employee

| Field Group | Field Name | Type | Purpose |
|-------------|-----------|------|---------|
| **Tax** | `kr_dependents_count` | Int | 간이세액표 가족수 |
| | `kr_withholding_rate` | Select | 80/100/120% |
| **Insurance** | `kr_pension_notified_amount` | Currency | 국민연금 공단 고지액 |
| | `kr_pension_exempt` | Check | 만60세 면제 |
| | `kr_employ_ins_exempt` | Check | 만65세 입사 면제 |
| **Foreign** | `kr_is_foreign` | Check | 외국인 여부 |
| | `kr_visa_type` | Select | 비자 유형 |
| | `kr_foreign_flat_tax` | Check | 19% 단일세율 |
| | `kr_pension_agreement` | Check | 연금 협정국 |
| | `kr_foreign_employ_exempt` | Check | 고용보험 미가입 |
| **Severance** | `kr_severance_eligible` | Check | 퇴직금 지급 대상 |

#### 주민번호 처리 (PII 경계)

주민등록번호(주민번호 13자리)는 Frappe DocType 에 저장하지 않는다.
- Password/Encrypted 필드 포함 — 어떤 형태로도 Frappe DB 저장 금지
- 필요 시 외부 privacy_broker 의 일회성 조회 API 만 사용
- 호출 시 감사 로그 자동 기록 (privacy_broker 정책)

근거:
- 본 통합 PR #3 §9.4 "PII 금지 적용 결과"
- privacy_broker 경계 = Frappe 외부 시스템 원칙 (PM 결재)
- Codex 어댑서리얼 [P1] 보강

---

## 3. Salary Components (Korea Template)

### Earnings

| Component | Type | Tax | Formula | Phase |
|-----------|------|-----|---------|-------|
| 기본급 (Base Pay) | Fixed | Taxable | Amount | 1 |
| 연장수당 (Overtime) | Formula | Taxable | `hourly_rate * 1.5 * OT_hours` | 1 |
| 야간수당 (Night) | Formula | Taxable | `hourly_rate * 0.5 * night_hours` | 1 |
| 휴일수당 (Holiday) | Formula | Taxable | See [07](07-working-hours.md) | 1 |
| 주휴수당 (Weekly Holiday) | Formula | Taxable | `hourly_rate * weekly_rest_hours` | 1 |
| 식대 (Meal) | Fixed | **Non-taxable** | 200,000 (capped) | 1 |
| 자가운전보조금 | Fixed | **Non-taxable** | 200,000 (capped) | 1 |
| 상여금 (Bonus) | Variable | Taxable | Per policy | 2 |

### Deductions

pension_base = `kr_pension_notified_amount` (취득신고 보수월액).
taxable_pay = 보수월액 = 과세급여 (총급여 - 비과세소득).

| Component | Type | Formula | Phase |
|-----------|------|---------|-------|
| 국민연금 | Formula | `kr_national_pension(pension_base)` | 1 |
| 건강보험 | Formula | `kr_health_insurance(taxable_pay)` | 1 |
| 장기요양 | Formula | `kr_longterm_care(health_ins)` | 1 |
| 고용보험 | Formula | `kr_employment_insurance(taxable_pay)` | 1 |
| 소득세 | Formula | `kr_income_tax(taxable, deps, withholding_rate)` | 1 |
| 지방소득세 | Formula | `income_tax * 0.1` | 1 |

---

## 4. Hook Architecture

### salary_slip Hooks

```python
# hrms/regional/south_korea/salary_slip.py

def before_calculate(doc, method):
    """Pre-calculation setup for Korean payroll."""
    if doc.company_country != 'South Korea':
        return
    
    # Load employee Korean-specific data
    doc.kr_data = get_kr_employee_data(doc.employee)
    
    # Determine insurance applicability
    doc.kr_insurance = assess_insurance(
        doc.kr_data, doc.start_date.year, doc.start_date.month
    )

def on_calculate(doc, method):
    """Post-calculation adjustments."""
    if doc.company_country != 'South Korea':
        return
    
    # Validate minimum wage
    validate_minimum_wage_compliance(doc)
    
    # Apply rounding rules
    apply_kr_rounding(doc)

def validate(doc, method):
    """Final validation."""
    if doc.company_country != 'South Korea':
        return
    
    # Cross-check: net pay should be positive
    if doc.net_pay < 0:
        frappe.throw("실지급액이 음수입니다. 공제 항목을 확인하세요.")
```

### hooks.py Registration

```python
# In hrms/hooks.py or south_korea/hooks.py

doc_events = {
    "Salary Slip": {
        "before_validate": "hrms.regional.south_korea.salary_slip.before_calculate",
        "on_change": "hrms.regional.south_korea.salary_slip.on_calculate",
        "validate": "hrms.regional.south_korea.salary_slip.validate",
    }
}
```

---

## 5. Tax Table Management

### DocType: Korea Tax Table (간이세액표)

| Field | Type | Purpose |
|-------|------|---------|
| `year` | Int | Effective year |
| `salary_from` | Currency | 급여 하한 |
| `salary_to` | Currency | 급여 상한 |
| `dep_1` ~ `dep_11` | Currency | 가족수별 세액 |

### Data Import

```python
def import_tax_table(year, csv_path):
    """Import NTS simplified tax table from CSV."""
    # NTS publishes annually in January
    # CSV format: salary_from, salary_to, dep1, dep2, ..., dep11
    ...
```

---

## 6. Insurance Rate Configuration

### DocType: Korea Insurance Rates

| Field | Type |
|-------|------|
| `effective_from` | Date |
| `national_pension_rate` | Percent |
| `pension_upper_limit` | Currency |
| `pension_lower_limit` | Currency |
| `health_insurance_rate` | Percent |
| `longterm_care_rate` | Percent |
| `employment_insurance_rate` | Percent |
| `min_wage_hourly` | Currency |

---

## 7. Reports (한국 고유)

### Phase 1
- **급여명세서** (Payslip) — Korean format with 4대보험 breakdown
- **급여대장** (Payroll Register) — Monthly summary

### Phase 2
- **취득신고서** (Insurance Acquisition Report)
- **상실신고서** (Insurance Loss Report)
- **보수총액 정산** (Annual Insurance Settlement)

### Phase 4
- **원천징수이행상황신고서** (Withholding Tax Filing)
- **원천징수영수증** (Withholding Receipt)
- **일용근로소득 지급명세서** (Daily Worker Payment Statement)
- **퇴직소득 원천징수영수증** (Severance Tax Receipt)

---

## 8. Data Model Extensions

```
Employee (extended)
├── kr_tax_info (Section)
│   ├── dependents_count
│   ├── withholding_rate
│   └── foreign_flat_tax
├── kr_insurance_info (Section)
│   ├── pension_notified_amount
│   ├── pension_exempt
│   └── employ_ins_exempt
└── kr_foreign_info (Section)
    ├── visa_type
    ├── pension_agreement
    └── foreign_employ_exempt

Salary Slip (extended)
├── kr_insurance_detail (Section)
│   ├── national_pension
│   ├── health_insurance
│   ├── longterm_care
│   ├── employment_insurance
│   └── insurance_employer_total
├── kr_tax_detail (Section)
│   ├── income_tax
│   ├── local_income_tax
│   └── tax_method (간이세액표/19% flat)
└── kr_summary (Section)
    ├── taxable_pay
    ├── nontaxable_pay
    └── total_deductions

Korea Insurance Rate (new DocType)
Korea Tax Table (new DocType)
Korea Severance Calculation (new DocType)
```

---

## 9. Testing Strategy

### Unit Tests

```python
# Per spec document — minimum test cases

# 02-social-insurance: mid-month hire, same-month term, age exemptions
# 03-income-tax: tax table lookup accuracy (10 salary levels × 3 dep counts)
# 04-year-end-settlement: Method A vs B comparison (high/low income)
# 05-severance: 3-month average wage, service days calculation
# 08-daily-workers: de minimis rule, break-even point
# 09-foreign-workers: visa-based insurance, flat tax
```

### Integration Tests

```python
# End-to-end payroll run
# 1. Create employee with Korean fields
# 2. Create salary structure with Korean components
# 3. Run payroll entry
# 4. Verify: gross, 4대보험, tax, net pay
# 5. Verify: rounding rules applied correctly
```

### Real-data Validation

> **PM Rule**: Before any module goes live, verify against **minimum 3 real payroll records**
> from our existing automation system. This has caught every edge case so far.

---

## 10. Migration Path

### From Our Existing System

Our current system (`급여자동화/`) uses:
- Python + openpyxl + YAML configs
- Direct Excel file manipulation
- Per-site YAML configuration

Migration to Frappe:
1. YAML configs → Frappe Company/Branch settings
2. Excel readers → Frappe DocType imports
3. Engine calculations → Frappe salary component formulas + hooks
4. Excel output → Frappe print formats
5. Insurance reports → Frappe report builder

### Key Architectural Decisions

| Decision | Our System | Frappe Approach |
|----------|-----------|-----------------|
| Insurance calc | Per-employee Python function | Salary Component formula + hook |
| Tax lookup | Direct CSV/table scan | DocType with indexed query |
| Rate storage | Hardcoded in code | DocType with effective dates |
| Rounding | Utility function | Custom Jinja filter + hook |
| Reports | openpyxl direct write | Frappe Report Builder / Print Format |
