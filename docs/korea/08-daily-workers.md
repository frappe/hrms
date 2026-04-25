# 08. 일용직 (Daily Workers)

> Frappe HRMS Korea — Daily Worker Tax Specification
> Status: Draft | Phase: 3 (Advanced)

---

## 1. Definition

**일용근로자** (Daily worker): Workers hired on a daily basis or for less than 3 months.
Tax treatment is fundamentally different from regular employees.

---

## 2. Tax Calculation

### 2-1. Formula

```
① 과세 일급 = 일급 - 150,000 (근로소득공제)
② 산출세액 = 과세 일급 × 6%
③ 세액공제 = 산출세액 × 55% (근로소득세액공제)
④ 원천징수 = 산출세액 - 세액공제
⑤ 지방소득세 = 원천징수 × 10%
```

### 2-2. De Minimis Rule (소액부징수)

```
IF 원천징수 < 1,000:
    원천징수 = 0
    지방소득세 = 0
```

### 2-3. Break-even Point

```
At daily wage 187,000:
  과세 = 187,000 - 150,000 = 37,000
  산출세액 = 37,000 × 6% = 2,220
  세액공제 = 2,220 × 55% = 1,221
  원천징수 = 2,220 - 1,221 = 999 → < 1,000 → 비징수

∴ 일급 ≤ 187,000원 → 세금 0
```

---

## 3. Implementation

```python
def calc_daily_worker_tax(daily_wage):
    """
    Calculate tax for daily worker.
    
    Returns: (income_tax, local_tax)
    """
    # ① Basic deduction
    taxable = max(daily_wage - 150_000, 0)
    
    if taxable == 0:
        return 0, 0
    
    # ② Calculated tax
    calculated = int(taxable * 0.06)
    
    # ③ Earned income credit
    credit = int(calculated * 0.55)
    
    # ④ Withholding
    withholding = calculated - credit
    
    # De minimis
    if withholding < 1_000:
        return 0, 0
    
    # ⑤ Local tax
    local = int(withholding * 0.1)
    
    return withholding, local
```

### Examples

| Daily Wage | Taxable | Tax | Credit | Withholding | Local | Total |
|-----------|---------|-----|--------|-------------|-------|-------|
| 150,000 | 0 | 0 | 0 | 0 | 0 | **0** |
| 187,000 | 37,000 | 2,220 | 1,221 | 999 | 0 | **0** (de minimis) |
| 200,000 | 50,000 | 3,000 | 1,650 | 1,350 | 135 | **1,485** |
| 300,000 | 150,000 | 9,000 | 4,950 | 4,050 | 405 | **4,455** |
| 500,000 | 350,000 | 21,000 | 11,550 | 9,450 | 945 | **10,395** |

---

## 4. Insurance Rules

| Insurance | Applied? | Condition |
|-----------|----------|-----------|
| 산재보험 | **Always** | No exceptions |
| 고용보험 | **Yes** | 0.9% employee share |
| 국민연금 | Conditional | 1개월 이상 근무 + 8일 이상/월 |
| 건강보험 | Conditional | 1개월 이상 근무 |

> For contracts under 1 month: only 산재 + 고용보험.

---

## 5. Key Differences from Regular Employees

| Aspect | Regular (근로소득자) | Daily (일용근로자) |
|--------|---------------------|------------------|
| Tax table | 간이세액표 (complex) | Simple formula |
| Tax rate | 6~45% progressive | Fixed 6% |
| Deduction | 150만 인적공제 etc. | 15만/일 flat |
| Year-end settlement | Required | **Not required** (분리과세) |
| 4대보험 | Full 4 types | 산재 always, others conditional |
| Severance eligibility | 1년 이상 | Usually N/A (< 3 months) |

---

## 6. Reporting

### 일용근로소득 지급명세서

- Filed: **quarterly** (분기별)
- Due: month following quarter end
- Content: worker name, 주민번호, daily wages, tax withheld
- Electronic filing via Hometax

### 근로내용확인신고서

- Filed to: 고용보험 (Employment Insurance)
- Content: work dates, daily hours, daily wage
- Due: by 15th of following month

---

## 7. Frappe Implementation Notes

- Separate **Salary Structure** template for daily workers
- **Payroll Entry** should support daily/per-shift processing
- Tax calculation hook: use `calc_daily_worker_tax()` instead of 간이세액표
- Attendance: track by **day** with shift assignments
- Reports: quarterly aggregation for 지급명세서
