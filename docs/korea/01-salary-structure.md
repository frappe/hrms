# 01. 급여 구조 (Salary Structure)

> Frappe HRMS Korea — Salary Component Specification
> Status: Draft | Phase: 1 (MVP)

---

## 1. Overview

Korean payroll consists of **taxable** and **non-taxable** components.
The distinction directly affects income tax calculation and year-end settlement.

```
총급여 (Gross Pay)
├── 과세 소득 (Taxable)
│   ├── 기본급 (Base Pay)
│   ├── 연장수당 (Overtime Allowance)
│   ├── 야간수당 (Night Work Allowance)
│   ├── 휴일수당 (Holiday Work Allowance)
│   ├── 직책수당 (Position Allowance)
│   ├── 근속수당 (Seniority Allowance)
│   └── 상여금 (Bonus)
└── 비과세 소득 (Non-taxable)
    ├── 식대 (Meal Allowance)
    ├── 자가운전보조금 (Vehicle Subsidy)
    ├── 육아수당 (Childcare Allowance)
    └── 연구보조비 (R&D Allowance)
```

---

## 2. Taxable Components (과세 항목)

### 2-1. 기본급 (Base Pay)

- Fixed monthly amount per employment contract
- Must meet minimum wage threshold (see [06-minimum-wage.md](06-minimum-wage.md))
- Basis for overtime calculation (통상시급)

### 2-2. 법정 수당 (Statutory Allowances)

| Component | Korean | Calculation | Reference |
|-----------|--------|-------------|-----------|
| Overtime | 연장수당 | 통상시급 × 1.5 × 연장시간 | 근로기준법 §56①1 |
| Night Work | 야간수당 | 통상시급 × 0.5 × 야간시간 | 근로기준법 §56②  |
| Holiday Work (≤8h) | 휴일수당 | 통상시급 × 1.5 × 시간 | 근로기준법 §56②2 |
| Holiday Work (>8h) | 휴일수당 | 통상시급 × 2.0 × 초과시간 | 근로기준법 §56②3 |
| Weekly Holiday | 주휴수당 | 1일분 통상임금 | 근로기준법 §55 |

**통상시급 (Ordinary Hourly Wage):**
```
통상시급 = 월 통상임금 / 209시간
209시간 = (주 40시간 + 주휴 8시간) × (365/7) / 12
```

### 2-3. 약정 수당 (Contractual Allowances)

Company-specific; configured per Salary Structure in Frappe:
- 직책수당 (Position Allowance)
- 근속수당 (Seniority Allowance)
- 기술수당 (Technical Allowance)
- 가족수당 (Family Allowance)

### 2-4. 상여금 (Bonus)

- Periodic bonuses (quarterly, annual, etc.)
- Affects severance pay calculation (연간 상여금 × 3/12 가산)
- Must be tracked separately for severance accrual

---

## 3. Non-taxable Components (비과세 항목)

### Monthly Limits

| Component | Korean | Monthly Limit | Tax Law Reference | Conditions |
|-----------|--------|--------------|-------------------|------------|
| Meal Allowance | 식대 | 200,000 | 소득세법 §12③ | No in-kind meal provided |
| Vehicle Subsidy | 자가운전보조금 | 200,000 | 소득세법 시행령 §12 | Employee-owned vehicle for work |
| Childcare | 육아수당 | 200,000/child | 소득세법 §12③ | Child age ≤ 6 |
| R&D Allowance | 연구보조비 | 200,000 | 조특법 §16 | Qualified researcher |
| Production OT | 생산직 초과근로수당 | 200,000/month (annual cap 2.4M) | 소득세법 §12③ | Total salary ≤ 30M, production worker |

### Implementation Notes

```python
# Frappe Salary Component configuration
{
    "component_name": "Meal Allowance",
    "component_name_kr": "식대",
    "type": "Earning",
    "is_tax_applicable": False,  # Non-taxable
    "monthly_cap": 200000,       # Custom field
    "excess_taxable": True,      # Amount over cap becomes taxable
}
```

**Critical Rule**: If the actual amount exceeds the monthly cap, the excess is taxable.
Example: 식대 250,000원 → 200,000 non-taxable + 50,000 taxable.

---

## 4. Deduction Components (공제 항목)

| Component | Korean | Type | Calculation |
|-----------|--------|------|-------------|
| National Pension | 국민연금 | Insurance | See [02-social-insurance.md](02-social-insurance.md) |
| Health Insurance | 건강보험 | Insurance | See [02-social-insurance.md](02-social-insurance.md) |
| Long-term Care | 장기요양보험 | Insurance | See [02-social-insurance.md](02-social-insurance.md) |
| Employment Insurance | 고용보험 | Insurance | See [02-social-insurance.md](02-social-insurance.md) |
| Income Tax | 소득세 | Tax | See [03-income-tax.md](03-income-tax.md) |
| Local Income Tax | 지방소득세 | Tax | 소득세 × 10% |

---

## 5. Gross-to-Net Calculation Flow

```
Step 1: Calculate Gross
  총급여 = 기본급 + Σ수당 + 상여금

Step 2: Separate Non-taxable
  과세급여 = 총급여 - Σ비과세(within caps)

Step 3: Calculate Insurance (based on 과세급여 or 총급여 depending on item)
  4대보험 = f(과세급여, age, hire_date, insurance_type)

Step 4: Calculate Tax
  소득세 = 간이세액표(과세급여, 가족수)
  지방소득세 = 소득세 × 10%

Step 5: Net Pay
  실지급액 = 총급여 - 4대보험 - 소득세 - 지방소득세
```

---

## 6. Frappe Implementation

### Salary Structure Template (Korea Standard)

| # | Component | Type | Formula/Amount | Tax | Stat |
|---|-----------|------|----------------|-----|------|
| 1 | 기본급 | Earning | Fixed | Y | - |
| 2 | 연장수당 | Earning | `hourly_rate * 1.5 * overtime_hours` | Y | Y |
| 3 | 야간수당 | Earning | `hourly_rate * 0.5 * night_hours` | Y | Y |
| 4 | 휴일수당 | Earning | `hourly_rate * 1.5 * holiday_hours` | Y | Y |
| 5 | 식대 | Earning | Fixed (200,000) | N | - |
| 6 | 국민연금 | Deduction | `kr_national_pension()` | - | Y |
| 7 | 건강보험 | Deduction | `kr_health_insurance()` | - | Y |
| 8 | 장기요양 | Deduction | `kr_longterm_care()` | - | Y |
| 9 | 고용보험 | Deduction | `kr_employment_insurance()` | - | Y |
| 10 | 소득세 | Deduction | `kr_income_tax()` | - | Y |
| 11 | 지방소득세 | Deduction | `income_tax * 0.1` | - | Y |

### Custom Fields on Employee DocType

| Field | Type | Purpose |
|-------|------|---------|
| `kr_dependents_count` | Int | 간이세액표 조회용 공제대상 가족수 |
| `kr_withholding_rate` | Select (80/100/120) | 맞춤형 원천징수 비율 |
| `kr_visa_type` | Data | 외국인 비자 유형 |
| `kr_foreign_flat_tax` | Check | 19% 단일세율 선택 여부 |
| `kr_pension_notified_amount` | Currency | 국민연금 공단 고지액 |

---

## 7. Pro-ration Rules (일할계산)

### Mid-month Hire
```
일할 급여 = 월급여 × (근무일수 / 해당월 총일수)
```

### Mid-month Termination
```
일할 급여 = 월급여 × (근무일수 / 해당월 총일수)
```

> **Lesson Learned**: Some companies use calendar days, others use working days.
> The system must support both modes as a company-level setting.
