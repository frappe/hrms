# 05. 퇴직금 (Severance Pay)

> Frappe HRMS Korea — Severance Pay Specification
> Status: Draft | Phase: 2 (Lifecycle)

---

## 1. Legal Basis

Under the **Employee Retirement Benefit Security Act** (근로자퇴직급여보장법),
employers must pay severance to any employee with **1 year or more** of continuous service.

---

## 2. Key Definitions

| Term | Korean | Definition |
|------|--------|------------|
| Retirement date | 퇴직일 | Last working day + 1 |
| Service days | 재직일수 | 퇴직일 - 입사일 |
| Service years | 근속연수 | For tax purposes (year + fraction) |
| Average wage | 평균임금 | (3-month wages + bonus + leave) / 3-month calendar days |
| Ordinary wage | 통상임금 | Fixed contractual wage (fallback if higher) |

> **Lesson Learned**: 퇴직일 = 마지막 근무일 + 1. This is a universal rule
> that many systems get wrong, causing off-by-one in service days.

---

## 3. Calculation

### 3-1. 3-Month Wage Components

```
A = 퇴직전 3개월간 임금총액
    - Retroactive 3 months from 퇴직일
    - For partial months: pro-rate (일할계산)
    
B = 상여금 가산 = 연간상여금 × (3/12)

C = 연차수당 가산 = (연차수당 일급 × 미사용일수) × (3/12)
```

### 3-2. Average Wage

```
1일 평균임금 = (A + B + C) / 퇴직전 3개월간 총일수(calendar days)
```

### 3-3. Severance Pay

```
퇴직금 = 1일 평균임금 × 30 × (재직일수 / 365)
```

### 3-4. Ordinary Wage Fallback

```python
if average_daily_wage < ordinary_daily_wage:
    severance = ordinary_daily_wage * 30 * (service_days / 365)
```

---

## 4. Severance Income Tax (퇴직소득세)

### 4-1. Calculation Flow

```
① 퇴직소득 = 퇴직금
② 근속연수공제:
   - 5년 이하: 1,000,000 × 근속연수
   - 10년 이하: 5,000,000 + 2,000,000 × (근속연수 - 5)
   - 20년 이하: 15,000,000 + 2,500,000 × (근속연수 - 10)
   - 20년 초과: 40,000,000 + 3,000,000 × (근속연수 - 20)

③ 환산급여 = (퇴직소득 - 근속연수공제) × 12 / 근속연수

④ 환산급여공제:
   - 8,000,000 이하: 환산급여 × 100%
   - 70,000,000 이하: 8,000,000 + (환산급여 - 8,000,000) × 60%
   - 100,000,000 이하: 45,200,000 + (환산급여 - 70,000,000) × 55%
   - 300,000,000 이하: 61,700,000 + (환산급여 - 100,000,000) × 45%
   - 300,000,000 초과: 151,700,000 + (환산급여 - 300,000,000) × 35%

⑤ 과세표준 = 환산급여 - 환산급여공제
⑥ 환산세액 = 과세표준 × 기본세율 (03-income-tax.md §4)
⑦ 퇴직소득세 = 환산세액 × 근속연수 / 12
⑧ 지방소득세 = 퇴직소득세 × 10%
```

### 4-2. Rounding

```
퇴직소득세: 10원 절사 (floor)
지방소득세: 10원 절사 (floor)
```

> **Critical**: 퇴직소득세 = floor, 연말정산 차감징수 = ceil.
> 반드시 구분해서 적용할 것.

### 4-3. Verification

> **PM Rule**: 국세청 퇴직소득세 엑셀 프로그램으로 반드시 2차검증.
> 엔진 계산은 참고용만. 세법 개정(근속연수공제 변경 등)으로
> 엔진이 틀릴 수 있음. 5~10건 크로스체크 후에만 자동화 전환 가능.

---

## 5. Implementation

```python
def calc_severance(hire_date, last_work_date, monthly_wages, annual_bonus=0, unused_leave_pay=0):
    """
    Calculate severance pay.
    
    Args:
        hire_date: 입사일
        last_work_date: 마지막 근무일
        monthly_wages: list of (month_start, month_end, wage) for last 3 months
        annual_bonus: 연간 상여금
        unused_leave_pay: 미사용 연차수당 (일급 × 일수)
    """
    retirement_date = last_work_date + timedelta(days=1)
    service_days = (retirement_date - hire_date).days
    
    if service_days < 365:
        return 0  # Less than 1 year
    
    # 3-month period
    period_end = retirement_date
    period_start = retirement_date - relativedelta(months=3)
    total_calendar_days = (period_end - period_start).days
    
    # A: 3-month wages (with pro-ration for partial months)
    wage_total = sum(prorate_wage(w, period_start, period_end) for w in monthly_wages)
    
    # B: Bonus proration
    bonus_addition = annual_bonus * 3 / 12
    
    # C: Leave pay proration
    leave_addition = unused_leave_pay * 3 / 12
    
    # Average daily wage
    avg_daily = (wage_total + bonus_addition + leave_addition) / total_calendar_days
    
    # Severance
    severance = avg_daily * 30 * service_days / 365
    
    return int(severance)
```

---

## 6. Edge Cases

### 6-1. 파트→정직원 전환

When an employee transitions from part-time to full-time with significant wage change,
the 3-month average may not reflect their overall compensation fairly.

**Custom severance by agreement**:
```
퇴직금 = 전체 급여 합산 / 12
```
This requires a separate agreement document.

### 6-2. Short 3-month Period

If the employee hasn't worked a full 3 months before retirement,
use the actual period from hire to retirement.

### 6-3. DAY(퇴직일)=1 (First of Month)

When 퇴직일 falls on the 1st of a month, it means 퇴사일 was the last day
of the previous month. The 3-month calculation period shifts accordingly.

> **Lesson Learned**: Our Excel template (xlsm) has formulas that shift columns
> when 퇴직일 is the 1st. This edge case must be explicitly tested.
