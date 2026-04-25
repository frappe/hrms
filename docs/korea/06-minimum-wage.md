# 06. 최저임금 (Minimum Wage)

> Frappe HRMS Korea — Minimum Wage Specification
> Status: Draft | Phase: 1 (MVP)

---

## 1. Current Rates

### 2026

| Metric | Amount | Basis |
|--------|--------|-------|
| Hourly | **10,320 KRW** | 최저임금법 |
| Daily (8h) | 82,560 KRW | 10,320 × 8 |
| Monthly (209h) | **2,156,880 KRW** | 10,320 × 209 |

### Rate History

| Year | Hourly | Monthly (209h) | Change |
|------|--------|----------------|--------|
| 2024 | 9,860 | 2,060,740 | +2.5% |
| 2025 | 10,030 | 2,096,270 | +1.7% |
| 2026 | 10,320 | 2,156,880 | +2.9% |

---

## 2. 209-Hour Basis

```
주 40시간 + 주휴 8시간 = 48시간/주
월 환산: 48 × (365/7) / 12 = 208.857... ≈ 209시간
```

---

## 3. Minimum Wage Compliance Check

### 3-1. What's Included

| Included | Excluded |
|----------|----------|
| 기본급 | 상여금 (비정기적) |
| 고정 수당 (매월 지급) | 식대 (현물급식 대체) |
| | 연장/야간/휴일수당 |
| | 숙박비, 교통비 (실비변상) |

> Starting from 2019, bonuses exceeding 25% of minimum wage monthly amount
> and welfare benefits exceeding 7% are included in the calculation.

### 3-2. Validation Logic

```python
def validate_minimum_wage(base_pay, fixed_allowances, year, monthly_hours=209):
    """
    Check if pay meets minimum wage.
    
    Args:
        base_pay: 기본급
        fixed_allowances: 매월 고정 지급 수당 합계
        year: 급여 연도
        monthly_hours: 소정근로시간 + 주휴 (default 209)
    """
    min_wage = get_minimum_wage(year)  # hourly
    min_monthly = min_wage * monthly_hours
    
    eligible_pay = base_pay + fixed_allowances
    
    if eligible_pay < min_monthly:
        shortfall = min_monthly - eligible_pay
        return False, shortfall
    return True, 0
```

### 3-3. Part-time Workers

```
월 최저임금 = 시급 × 주 소정근로시간 × (365/7) / 12

Example: 주 20시간 근무
  = 10,320 × (20 + 주휴4) × 52.14 / 12
  = 10,320 × 24 × 4.345
  = 1,076,371원
```

---

## 4. Frappe Implementation

### Custom Validation Hook

```python
# In salary_slip.py (Korea override)
def validate(self):
    if self.company_country == 'South Korea':
        is_valid, shortfall = validate_minimum_wage(
            self.base_pay,
            self.fixed_allowances,
            self.posting_date.year
        )
        if not is_valid:
            frappe.throw(
                f"급여가 최저임금에 미달합니다. "
                f"부족액: {shortfall:,.0f}원"
            )
```

### Configuration

Store minimum wage rates as a DocType or in `rates.py`:

```python
MINIMUM_WAGE = {
    2024: 9860,
    2025: 10030,
    2026: 10320,
}
```
