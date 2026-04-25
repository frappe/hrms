# 07. 근로시간 및 가산수당 (Working Hours & Overtime)

> Frappe HRMS Korea — Working Hours Specification
> Status: Draft | Phase: 1 (MVP)

---

## 1. Legal Limits (근로기준법)

| Item | Limit | Reference |
|------|-------|-----------|
| Daily standard | 8 hours | §50① |
| Weekly standard | 40 hours | §50① |
| Weekly overtime cap | 12 hours | §53① |
| **Weekly maximum** | **52 hours** | §50+§53 |
| Night work definition | 22:00 ~ 06:00 | §56 |

---

## 2. Premium Rates (가산수당)

Applies to workplaces with **5 or more employees**.

| Type | Korean | Premium | Total Pay Rate |
|------|--------|---------|---------------|
| Overtime | 연장근로 | +50% | 150% |
| Night work | 야간근로 | +50% | 150% |
| Holiday ≤ 8h | 휴일근로 | +50% | 150% |
| Holiday > 8h | 휴일근로 초과 | +100% | 200% |

### Stacking Rules

Premiums **stack** when multiple conditions apply:

| Scenario | Calculation | Total |
|----------|-------------|-------|
| Regular overtime | base × 1.5 | 150% |
| Night work (regular hours) | base × 1.5 | 150% |
| **Overtime + Night** | base + 50% + 50% | **200%** |
| Holiday work | base × 1.5 | 150% |
| **Holiday + Overtime** | base + 50% + 50% | **200%** |
| **Holiday + Night** | base + 50% + 50% | **200%** |
| **Holiday + Overtime + Night** | base + 50% + 50% + 50% | **250%** |

---

## 3. 통상시급 (Ordinary Hourly Wage)

Base for all premium calculations:

```
통상시급 = 월 통상임금 / 월 소정근로시간

월 소정근로시간 (209h):
= (주 소정근로 40h + 주휴 8h) × (365일 / 7일) / 12개월
= 48 × 52.14... / 12
= 208.857... ≈ 209시간
```

### What's Included in 통상임금

| Included | Excluded |
|----------|----------|
| 기본급 | 실적급/인센티브 |
| 정기적 고정수당 | 비정기 상여금 |
| 근속수당 (고정) | 실비변상 (교통비 등) |
| 직책수당 | 연장/야간/휴일수당 (순환 참조 방지) |

---

## 4. 주휴수당 (Weekly Holiday Pay)

### Eligibility

- Works **15 hours or more per week** on a regular basis
- Fulfilled the prescribed work days of that week

### Calculation

```
주휴수당 = 1일 통상임금

For hourly workers:
  주휴수당 = 통상시급 × (주 소정근로시간 / 5일)
  
Example: 주 40h worker
  주휴수당 = 통상시급 × 8h
  
Example: 주 20h worker  
  주휴수당 = 통상시급 × 4h
```

> **Lesson Learned**: 주 15시간 미만 단시간 근로자에게 주휴수당을
> 지급하면 과지급. 반드시 주 소정근로시간 체크 필요.

---

## 5. Overtime Calculation Example

```python
def calc_overtime_pay(hourly_rate, overtime_hours, night_hours=0, 
                      holiday_hours=0, holiday_overtime_hours=0):
    """
    Calculate premium pay for various work types.
    """
    pay = 0
    
    # Regular overtime (연장)
    pay += hourly_rate * 1.5 * overtime_hours
    
    # Night work premium (야간) — additional 50% on top of base/OT
    pay += hourly_rate * 0.5 * night_hours
    
    # Holiday work
    pay += hourly_rate * 1.5 * min(holiday_hours, 8)
    if holiday_hours > 8:
        pay += hourly_rate * 2.0 * (holiday_hours - 8)
    
    return int(pay)
```

---

## 6. Special Categories

### 5인 미만 사업장 (Under 5 employees)

| Item | Applied? |
|------|----------|
| 52시간 제한 | **No** |
| 연장/야간/휴일 가산 | **No** (법정 가산 없음) |
| 주휴수당 | **Yes** |
| 연차휴가 | **Yes** (15일) |

### 관리감독자 (Supervisory positions)

- Exempt from working hour limits and overtime pay
- Must meet strict legal criteria (not just title-based)

### 유연근무제

| Type | Korean | Max Hours |
|------|--------|-----------|
| Flex time (2-week) | 2주 탄력근무 | Avg 40h/week |
| Flex time (3-month) | 3개월 탄력근무 | Avg 40h/week, max 52h/week |
| Selective work | 선택근무제 | 정산기간 평균 40h |

---

## 7. Frappe Integration

### Attendance + Overtime Tracking

```
Employee Check-in/out → Attendance record
  → Calculate: regular hours, overtime, night, holiday
  → Feed into Salary Slip as hours-based components
```

### Salary Components

| Component | Formula |
|-----------|---------|
| 연장수당 | `hourly_rate * 1.5 * overtime_hours` |
| 야간수당 | `hourly_rate * 0.5 * night_hours` |
| 휴일수당 | `hourly_rate * 1.5 * holiday_hours_within_8 + hourly_rate * 2.0 * holiday_hours_over_8` |
| 주휴수당 | `hourly_rate * weekly_holiday_hours` (auto if weekly hours ≥ 15) |
