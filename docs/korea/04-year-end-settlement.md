# 04. 연말정산 (Year-end Tax Settlement)

> Frappe HRMS Korea — Year-end Settlement Specification
> Status: Draft | Phase: 3 (Advanced) + Phase 2 (Mid-year Termination)

---

## 1. Overview

Year-end settlement (연말정산) reconciles the actual tax liability against
taxes withheld monthly. It's the most complex part of Korean payroll.

### Timing

| Situation | When |
|-----------|------|
| Continuing employee | February payroll of next year |
| **Mid-year termination** | Final payroll month (Phase 2) |

---

## 2. 7-Step Calculation

```
Step 1: 총급여액    = Annual gross - Non-taxable income
Step 2: 근로소득금액 = 총급여액 - 근로소득공제
Step 3: 차감소득금액 = 근로소득금액 - 인적공제 - 연금보험료 - 특별소득공제
Step 4: 과세표준    = 차감소득금액 - 기타 소득공제
Step 5: 산출세액    = 과세표준 × 기본세율
Step 6: 결정세액    = 산출세액 - 세액감면 - 세액공제
Step 7: 차감징수세액 = 결정세액 - 기납부세액
```

---

## 3. Step-by-step Detail

### Step 1: 총급여액

```
총급여 = Σ(monthly gross from Jan to Dec or hire to term)
비과세 = Σ(식대, 자가운전보조금, etc. within caps)
총급여액 = 총급여 - 비과세
```

### Step 2: 근로소득공제

See [03-income-tax.md](03-income-tax.md) §5 for the deduction table.

### Step 3: 소득공제 (Income Deductions)

| Category | Items | Amount |
|----------|-------|--------|
| 인적공제 (Personal) | Self, spouse, dependents | 1,500,000/person |
| 연금보험료 | National pension paid | Actual amount |
| 특별소득공제 | Health/LTC/employment insurance | Actual amount |
| | Housing fund interest | Per limits |

### Step 4: 기타 소득공제

| Item | Deduction |
|------|-----------|
| 개인연금저축 | Up to 720,000/year |
| 주택마련저축 | Up to 3,000,000/year |
| 신용카드 사용 | 15~40% of excess over 25% of total pay |

### Step 5: 산출세액

Apply basic tax brackets from [03-income-tax.md](03-income-tax.md) §4.

### Step 6: 세액공제 (Tax Credits)

| Credit | Calculation |
|--------|-------------|
| 근로소득세액공제 | See [03-income-tax.md](03-income-tax.md) §6 |
| 자녀세액공제 | 150,000~300,000/child |
| 보장성보험 | 납입액 × 12% (max 1,000,000 base) |
| 의료비 | (지출 - 총급여×3%) × 15% |
| 교육비 | 납입액 × 15% |
| 기부금 | 15~30% |
| 월세 | 납입액 × 15~17% |
| 표준세액공제 | 130,000 (if no itemized claims) |

### Step 7: 차감징수세액

```
차감징수 = 결정세액 - 기납부세액
if 차감징수 > 0: 추가 납부 (additional payment)
if 차감징수 < 0: 환급 (refund)
```

---

## 4. Rounding

| Item | Rule |
|------|------|
| 근로소득공제 | 원단위 |
| 산출세액 | 원단위 |
| **차감징수세액 (소득세)** | **10원 올림 (ceil)** |
| 지방소득세 | 소득세 × 10% |

```python
import math

def ceil_10(amount):
    """10원 단위 올림"""
    if amount >= 0:
        return math.ceil(amount / 10) * 10
    else:  # 환급 (refund) — negative
        return -math.ceil(abs(amount) / 10) * 10
```

---

## 5. Data Flow (Frappe Integration)

```
Monthly Salary Slips (Jan~Dec)
  → Aggregate: total pay, non-taxable, insurance paid, tax withheld
  → Apply: personal info, deduction receipts (from Hometax)
  → Calculate: 7-step engine
  → Output: 차감징수세액 applied to February payslip
```

---

## 6. Mid-year Termination Tax (중도퇴사 연말정산) — Phase 2

### 6-1. Scope

Only these deductions apply (no itemized special credits):

| Category | Items | Applied? |
|----------|-------|----------|
| 인적공제 | Self (150만) | **Always** |
| 연금보험료 | National pension paid | **Always** |
| 특별소득공제 | Health/LTC/employment insurance | **Method A only** |
| 근로소득세액공제 | Earned income credit | **Always** |
| 표준세액공제 | 130,000원 | **Method B only** |
| 보장성보험/의료비/교육비 | Itemized credits | **NOT applied** |

### 6-2. Method A vs Method B (핵심)

| | Method A | Method B |
|--|---------|---------|
| 소득공제 | 인적 + 국민연금 + **건강+장기+고용** | 인적 + 국민연금 |
| 표준세액공제 | 0 | min(130,000, 산출세액 - 근로소득세액공제) |
| Best for | **High earners** | **Low earners** |

### 6-3. Auto-determination Logic

```python
def determine_method(insurance_premiums, marginal_rate):
    """
    Compare tax savings: insurance deduction vs standard credit.
    
    insurance_premiums = health + longterm_care + employment
    marginal_rate = tax rate at employee's bracket
    """
    savings_a = insurance_premiums * marginal_rate  # Method A savings
    savings_b = 130_000  # Method B savings (standard credit)
    
    return 'A' if savings_a > savings_b else 'B'
```

### 6-4. Calculation Flow

```python
def mid_year_tax_settlement(employee, salary_data):
    # ① 총급여 = sum of pay - non-taxable
    total_pay = sum(s.taxable for s in salary_data)
    
    # ② 근로소득공제
    earned_deduction = calc_earned_income_deduction(total_pay)
    earned_income = total_pay - earned_deduction
    
    # ③ 소득공제 - calculate both methods
    pension_paid = sum(s.national_pension for s in salary_data)
    insurance_paid = sum(s.health + s.longterm + s.employment for s in salary_data)
    
    # Method A: personal + pension + all insurance
    deduction_a = 1_500_000 + pension_paid + insurance_paid
    # Method B: personal + pension only
    deduction_b = 1_500_000 + pension_paid
    
    # ④⑤ 과세표준 & 산출세액 for both
    for method, deduction in [('A', deduction_a), ('B', deduction_b)]:
        taxable = max(earned_income - deduction, 0)
        calculated_tax = calc_tax_by_bracket(taxable)
        
        # ⑥ 세액공제
        earned_credit = calc_earned_income_credit(calculated_tax, total_pay)
        if method == 'B':
            standard_credit = min(130_000, max(calculated_tax - earned_credit, 0))
        else:
            standard_credit = 0
        
        determined_tax = max(calculated_tax - earned_credit - standard_credit, 0)
    
    # Choose the method with lower determined_tax
    # ⑦ 차감징수 = determined_tax - prepaid_tax
    prepaid = sum(s.income_tax for s in salary_data[:-1])  # EXCLUDE termination month
    
    final_tax = ceil_10(determined_tax - prepaid)
    local_tax = int(final_tax * 0.1) if final_tax > 0 else ceil_10(final_tax * 0.1)
    
    return final_tax, local_tax
```

### 6-5. 기납부세액 (Prepaid Tax) — CRITICAL

```
기납부세액 = sum of income tax from ALL months BEFORE termination month
```

> **Lesson Learned (Incident)**: 퇴직월 소득세는 정산 결과 자체이므로
> 기납부에 절대 포함하면 안 됨. 2026.02 하나멜라민 차상화 건에서
> 퇴직월 포함으로 기납부 2개월분 → 잘못된 환급액 산출한 사고 있었음.

**Validation Rule**:
```python
# Refund amount can NEVER exceed prepaid tax
assert abs(refund) <= prepaid_tax, "Refund exceeds prepaid — calculation error"
```

---

## 7. Verified Test Cases (32건 검증 완료)

| Dataset | Count | Result |
|---------|-------|--------|
| 올웨이즈샤브 2025.07~12 | 28 | All Method B → PASS |
| 다이닝원 동백 | 4 | 3× Method B, 1× Method A (이승준 3,240만) → PASS |
| 올웨이즈샤브 2026.02 | 8 | 2 refunds, 6 zeros → PASS |
| 하나멜라민 | 1 | Method B, refund -127,220/-12,720 → PASS (after fix) |
