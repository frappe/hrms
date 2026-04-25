# 03. 소득세 (Income Tax Withholding)

> Frappe HRMS Korea — Income Tax Specification
> Status: Draft | Phase: 1 (MVP)

---

## 1. Overview

Korean employers withhold income tax monthly using the **Simplified Tax Table** (간이세액표),
published annually by the National Tax Service (국세청).

This is NOT a direct bracket calculation — it's a pre-computed lookup table
that factors in earned income deductions and basic personal exemptions.

---

## 2. Monthly Withholding — 간이세액표

### 2-1. Lookup Variables

| Variable | Korean | Source |
|----------|--------|--------|
| Monthly taxable pay | 과세급여 | 총급여 - 비과세소득 |
| Number of dependents | 공제대상 가족수 | Employee profile |

### 2-2. Withholding Options (맞춤형 원천징수)

| Option | Effect | Typical Use |
|--------|--------|-------------|
| 80% | Under-withhold | Prefers monthly cash flow |
| 100% | Standard | Default |
| 120% | Over-withhold | Prefers smaller year-end adjustment |

```python
def calc_monthly_tax(taxable_pay, dependents, rate_option=100):
    """
    Lookup 간이세액표 and apply withholding rate option.
    """
    base_tax = simplified_tax_table_lookup(taxable_pay, dependents)
    adjusted = int(base_tax * rate_option / 100)
    local_tax = int(adjusted * 0.1)
    return adjusted, local_tax
```

### 2-3. Tax Table Format

The NTS publishes the table as Excel/CSV. Structure:

| 월급여 하한 | 월급여 상한 | 가족1 | 가족2 | 가족3 | ... | 가족11 |
|------------|------------|-------|-------|-------|-----|--------|
| 1,060,000 | 1,080,000 | 0 | 0 | 0 | ... | 0 |
| ... | ... | ... | ... | ... | ... | ... |
| 10,000,000 | 10,020,000 | 1,845,670 | ... | ... | ... | ... |

### 2-4. Implementation Strategy

```python
# Option A: Direct table lookup (recommended for accuracy)
# Load NTS CSV into a database table with effective_year
# Binary search on salary range, then column lookup by dependents

# Option B: Formula approximation (NOT recommended)
# The NTS table incorporates complex deduction curves
# Formula approximation has 100~1000원 errors that compound
```

> **PM Decision**: Use Option A (direct table lookup). The NTS publishes
> updated tables every January. Import as a DocType or CSV fixture.

---

## 3. Local Income Tax (지방소득세)

```
지방소득세 = 소득세 × 10%
```

- Always calculated as exact 10% of income tax
- Reported separately to local government
- Withheld on same payslip

---

## 4. Basic Tax Rate Table (기본세율)

Used for: year-end settlement, severance tax, direct calculations.

| Taxable Income (과세표준) | Rate | Progressive Deduction (누진공제) |
|--------------------------|------|-------------------------------|
| 0 ~ 14,000,000 | 6% | 0 |
| 14,000,001 ~ 50,000,000 | 15% | 1,260,000 |
| 50,000,001 ~ 88,000,000 | 24% | 5,760,000 |
| 88,000,001 ~ 150,000,000 | 35% | 15,440,000 |
| 150,000,001 ~ 300,000,000 | 38% | 19,940,000 |
| 300,000,001 ~ 500,000,000 | 40% | 25,940,000 |
| 500,000,001 ~ 1,000,000,000 | 42% | 35,940,000 |
| 1,000,000,001+ | 45% | 65,940,000 |

```python
TAX_BRACKETS = [
    (14_000_000, 0.06, 0),
    (50_000_000, 0.15, 1_260_000),
    (88_000_000, 0.24, 5_760_000),
    (150_000_000, 0.35, 15_440_000),
    (300_000_000, 0.38, 19_940_000),
    (500_000_000, 0.40, 25_940_000),
    (1_000_000_000, 0.42, 35_940_000),
    (float('inf'), 0.45, 65_940_000),
]

def calc_tax_by_bracket(taxable_income):
    for upper, rate, deduction in TAX_BRACKETS:
        if taxable_income <= upper:
            return int(taxable_income * rate - deduction)
    return 0
```

---

## 5. Earned Income Deduction (근로소득공제)

Applied in year-end settlement (Step 2).

| Total Pay (총급여) | Deduction |
|-------------------|-----------|
| 0 ~ 5,000,000 | 총급여 × 70% |
| 5,000,001 ~ 15,000,000 | 3,500,000 + (총급여 - 5,000,000) × 40% |
| 15,000,001 ~ 45,000,000 | 7,500,000 + (총급여 - 15,000,000) × 15% |
| 45,000,001 ~ 100,000,000 | 12,000,000 + (총급여 - 45,000,000) × 5% |
| 100,000,001+ | 14,750,000 + (총급여 - 100,000,000) × 2% |

---

## 6. Earned Income Tax Credit (근로소득세액공제)

Applied in year-end settlement (Step 6).

| Calculated Tax (산출세액) | Credit |
|--------------------------|--------|
| 0 ~ 1,300,000 | 산출세액 × 55% |
| 1,300,001+ | 715,000 + (산출세액 - 1,300,000) × 30% |

**Cap by income level:**

| Total Pay | Cap |
|-----------|-----|
| ≤ 33,000,000 | 740,000 |
| ≤ 70,000,000 | 660,000 |
| > 70,000,000 | 500,000 |

---

## 7. Rounding

| Item | Rule |
|------|------|
| 소득세 (monthly withholding) | 원단위 (간이세액표 그대로) |
| 지방소득세 (monthly) | 원단위 |
| 연말정산 차감징수세액 | 10원 **올림** (ceil) |
| 퇴직소득세 | 10원 **절사** (floor) |

> **Lesson Learned**: Rounding direction differs between year-end settlement (ceil)
> and severance tax (floor). Mixing these up causes 10~20원 discrepancies
> that compound across employees.

---

## 8. 사업소득자 (Business Income Earner) Detection

Some workers are classified as independent contractors (사업소득자)
rather than employees (근로소득자). They pay 3.3% flat tax (3% income + 0.3% local).

```python
def is_business_income(total_wage, income_tax):
    """
    Detect business income earner by checking if tax ≈ 3% of wage.
    Tolerance: ±100 KRW (rounding differences).
    """
    expected = int(total_wage * 0.03)
    return total_wage > 0 and income_tax > 0 and abs(income_tax - expected) <= 100
```

> **Lesson Learned**: 사업소득자 must be excluded from 4대보험 processing.
> Failure to filter = wrong insurance filings + over-deduction.
