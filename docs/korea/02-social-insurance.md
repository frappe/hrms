# 02. 4대보험 (Social Insurance)

> Frappe HRMS Korea — Social Insurance Specification
> Status: Draft | Phase: 1 (MVP) + Phase 2 (Lifecycle)

---

## 1. Overview

Korea's mandatory social insurance system consists of 4 programs.
Employers must calculate, deduct, and remit both employee and employer shares.

---

## 2. Rate Table — 2026

| Insurance | Korean | Total | Employee | Employer | Base |
|-----------|--------|-------|----------|----------|------|
| National Pension | 국민연금 | 9.5% | 4.75% | 4.75% | 기준소득월액 |
| Health Insurance | 건강보험 | 7.19% | 3.595% | 3.595% | 보수월액 (= 과세급여) |
| Long-term Care | 장기요양 | 13.14% of HI | 50% | 50% | 건강보험료 기준 |
| Employment Ins. (UI) | 고용보험-실업급여 | 1.8% | 0.9% | 0.9% | 과세급여 |
| Employment Ins. (Stab) | 고용보험-고용안정 | 0.25~0.85% | 0% | 100% | 과세급여 |
| Industrial Accident | 산재보험 | avg 1.47% | 0% | 100% | 과세급여 |

### Rate History (for multi-year support)

| Year | 국민연금 | 건강보험 | 장기요양 | 고용보험(근로자) |
|------|---------|---------|---------|----------------|
| 2024 | 4.5% | 3.545% | 12.95% | 0.9% |
| 2025 | 4.5% | 3.545% | 12.81% | 0.9% |
| 2026 | 4.75% | 3.595% | 13.14% | 0.9% |

> **Implementation**: Store rates with `effective_from` dates. Lookup by payroll month.

---

## 3. National Pension (국민연금) — Detail

### 3-1. 기준소득월액 Thresholds

| Period | Upper (상한) | Lower (하한) |
|--------|-------------|-------------|
| 2026.01 ~ 2026.06 | 6,370,000 | 400,000 |
| 2026.07 ~ 2027.06 | 6,590,000 | 410,000 |

```python
def calc_national_pension(gross, period):
    upper, lower = get_thresholds(period)
    base = max(min(gross, upper), lower)
    return floor_10(base * 0.0475)
```

### 3-2. NPS-Notified Amount (공단 고지액)

**Critical Lesson**: For the first month of pension contribution (중도입사 다음달),
the NPS uses the **취득신고 보수월액** to calculate the contribution, NOT the actual salary.
The amount is fixed until the next annual reconciliation.

```
First contribution = 취득신고 보수월액 × 4.75%  (hardcoded per employee)
Subsequent months = same fixed amount until NPS adjusts
```

> **Frappe Field**: `kr_pension_notified_amount` on Employee doctype

### 3-3. Age Exemption (만 60세)

```
Exempt from: month AFTER the month containing 60th birthday
Example: Born 1966.03.15 → turns 60 in March 2026 → exempt from April 2026
```

---

## 4. Health Insurance (건강보험) — Detail

### 4-1. Calculation
```python
def calc_health_insurance(gross):
    return floor_10(gross * 0.03595)
```

### 4-2. Long-term Care (장기요양)
```python
def calc_longterm_care(health_insurance):
    return floor_10(health_insurance * 0.1314)
```

### 4-3. Year-end Settlement (보수총액 정산) — Phase 2

Triggered on: employee termination or annual settlement

```
월평균보수 = 보수총액 / 산정월수
산출보험료 = 월평균보수 × 3.595% × 납부월수
장기요양산출 = (월평균보수 × 3.595%) × 13.14% × 납부월수
정산액 = 산출보험료 - 기납부 합계
```

**Critical Distinction**: 산정월수 vs 납부월수

| Situation | 산정월수 | 납부월수 |
|-----------|---------|---------|
| 1일 입사 | 근무월수 | 근무월수 |
| **중도입사** | **근무월수** | **근무월수 - 1** |

> **Lesson Learned**: 입사월에는 보험료를 내지 않지만, 보수총액 산정에는 입사월 임금 포함.
> This single rule caused multiple settlement errors before we caught it.

**Annual Boundary Rule**: Settlement is **per calendar year**. Never aggregate across years.
```
Example: Hired 2025.11.28, Terminated 2026.02.28
  → 2025 settlement: Nov-Dec (separate)
  → 2026 settlement: Jan-Feb only
```

---

## 5. Employment Insurance (고용보험) — Detail

### 5-1. Calculation
```python
def calc_employment_insurance(gross):
    return floor_10(gross * 0.009)
```

### 5-2. Employer-side Rates (고용안정/직업능력개발)

| Company Size | Rate |
|-------------|------|
| < 150 employees | 0.25% |
| 150 ~ 999 (priority support) | 0.45% |
| 1,000+ (priority support) | 0.65% |
| 1,000+ (non-priority) | 0.85% |

### 5-3. Age 65 Exemption

```
IF hire_date >= employee's 65th birthday:
    employment_insurance = 0  # Exempt
ELSE:
    employment_insurance = normal  # Even after turning 65
```

> **Lesson Learned**: This is hire-date-based, NOT current-age-based.
> An employee hired at 64 continues paying even at 70.

---

## 6. Mid-month Hire/Termination Rules

### 6-1. Mid-month Hire (1일 외 입사)

| Insurance | First Month | Second Month |
|-----------|-------------|-------------|
| 국민연금 | **0** | NPS notified amount |
| 건강보험 | **0** | gross × 3.595% |
| 장기요양 | **0** | health × 13.14% |
| 고용보험 | **Deducted** | gross × 0.9% |

### 6-2. 1일 입사 (Standard)

All 4 insurances deducted from first month.

### 6-3. Mid-month Termination

| Insurance | Termination Month |
|-----------|-------------------|
| 국민연금 | **Deducted normally** |
| 건강/장기 | **Deducted + year-end settlement** |
| 고용보험 | **Deducted** |

### 6-4. Same-month Hire+Termination (당월입퇴사)

| Insurance | Deduction |
|-----------|-----------|
| 국민연금/건강/장기 | **0 (not deducted)** |
| 고용보험 | **Deducted** |

---

## 7. Rounding Rules (단수처리)

| Item | Rule | Code |
|------|------|------|
| 국민연금 | 원단위 (NPS determines) | Per NPS notification |
| 건강보험 | 10원 절사 | `floor(x / 10) * 10` |
| 장기요양 | 10원 절사 | `floor(x / 10) * 10` |
| 고용보험 | 10원 절사 | `floor(x / 10) * 10` |

```python
def floor_10(amount):
    """10원 단위 절사 (floor to nearest 10 KRW)"""
    return int(amount // 10) * 10
```

---

## 8. Determination Logic (자동 판단)

```python
def assess_insurance(employee, pay_year, pay_month):
    """Determine which insurances apply for this employee in this month."""
    
    result = {
        'national_pension': True,
        'health_insurance': True,
        'longterm_care': True,
        'employment_insurance': True,
    }
    
    # 1. Age-based exemptions
    if is_over_60_next_month(employee.birthday, pay_year, pay_month):
        result['national_pension'] = False
    
    if is_over_65_at_hire(employee.birthday, employee.hire_date):
        result['employment_insurance'] = False
    
    # 2. Mid-month hire (first month)
    if is_mid_month_hire(employee.hire_date, pay_year, pay_month):
        result['national_pension'] = False
        result['health_insurance'] = False
        result['longterm_care'] = False
        # employment_insurance remains True
    
    # 3. Same-month hire+term
    if is_same_month_hire_term(employee.hire_date, employee.term_date, pay_year, pay_month):
        result['national_pension'] = False
        result['health_insurance'] = False
        result['longterm_care'] = False
        # employment_insurance remains True
    
    # 4. Foreign worker exemptions
    if employee.is_foreign:
        apply_foreign_rules(result, employee.visa_type)
    
    return result
```

---

## 9. Filing Reports (신고서)

### 취득신고서 (Acquisition Report)
- Filed when: New hire
- Key fields: 주민번호, 취득일, 보수월액, 업종코드
- 국민연금 만60세↑ → pension fields blank
- 취득월 납부여부: 1일 입사=1(희망), 중도입사=2(미희망)

### 상실신고서 (Loss Report)
- Filed when: Termination
- 상실일 = 퇴사일 + 1일
- 보수총액: 입사일 이후 총 급여 합산
- 상실사유코드: `11` + full text

### 보수총액 정산 (Annual Reconciliation)
- Filed when: Every February (annual) or on termination
- Per calendar year basis only
