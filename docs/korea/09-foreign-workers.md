# 09. 외국인 근로자 (Foreign Workers)

> Frappe HRMS Korea — Foreign Worker Specification
> Status: Draft | Phase: 3 (Advanced)

---

## 1. Tax Options

Foreign workers in Korea can choose between two tax methods:

| Method | Korean | Description |
|--------|--------|-------------|
| Progressive | 종합과세 누진세율 | Same as Korean workers (6~45%), all deductions available |
| **Flat rate** | **단일세율 19%** | Applied to total salary, NO deductions allowed |

### 1-1. 19% Flat Tax

```
소득세 = 총급여 × 19% (비과세 미분리, 공제 없음)
지방소득세 = 소득세 × 10%
```

- Originally limited to first 5 years of employment in Korea
- **Extended to lifetime application** (no expiration) under recent amendments
- Worker should compare both methods and choose the more favorable one

### 1-2. When to Choose Each

| Salary Level | Recommended |
|-------------|-------------|
| Low (< ~35M/year) | Progressive (lower effective rate with deductions) |
| High (> ~50M/year) | Compare both (flat may be lower) |
| Very high | Flat 19% (progressive rates reach 38%+) |

### 1-3. Implementation

```python
def calc_foreign_worker_tax(employee, gross_pay, taxable_pay, dependents):
    """Calculate tax for foreign worker with method comparison."""
    
    if not employee.kr_foreign_flat_tax:
        # Progressive method (same as Korean)
        return calc_monthly_tax(taxable_pay, dependents)
    
    # Flat 19% method
    flat_tax = int(gross_pay * 0.19)
    flat_local = int(flat_tax * 0.1)
    return flat_tax, flat_local
```

---

## 2. Social Insurance Rules

### 2-1. By Insurance Type

| Insurance | Rule | Notes |
|-----------|------|-------|
| **산재보험** | **Mandatory for all** | No exceptions |
| **건강보험** | **Mandatory** | Enrolled as workplace subscriber (직장가입자) |
| **국민연금** | **Reciprocity** (상호주의) | Depends on bilateral agreements |
| **고용보험** | **By visa type** | See §2-2 below |

### 2-2. Employment Insurance by Visa

| Category | Visa Types | Coverage |
|----------|-----------|----------|
| **Mandatory** | F-2 (Resident), F-5 (Permanent), F-6 (Marriage immigrant) | 당연적용 |
| **Voluntary** | F-4 (Overseas Korean) | Employee must apply; **no retroactive enrollment** |
| **Voluntary** | E-9, H-2, most work visas | Employee must apply |
| **Exempt** | Diplomatic, government visas | Not applicable |

> **Lesson Learned**: F-4 임의가입은 소급 불가.
> 근로자가 가입 희망하면 그 시점부터만 적용.
> 과거 기간 소급 공제하면 불법.

### 2-3. National Pension — Bilateral Agreements

Korea has social security agreements with ~30+ countries.
Workers from these countries may be exempt from national pension:

```
Agreement countries (partial list):
USA, Canada, Germany, UK, France, Japan, China, Australia, etc.

Workers from agreement countries:
- Can be exempt if covered by home country pension
- Must submit Certificate of Coverage (가입증명서)
```

---

## 3. Employee Configuration

### Frappe Custom Fields

| Field | Type | Purpose |
|-------|------|---------|
| `kr_is_foreign` | Check | Foreign worker flag |
| `kr_visa_type` | Select | F-2/F-4/F-5/F-6/E-9/H-2/etc. |
| `kr_foreign_flat_tax` | Check | Use 19% flat rate |
| `kr_pension_agreement` | Check | Has bilateral pension agreement |
| `kr_foreign_employ_exempt` | Check | Employment insurance not enrolled |

### Insurance Assessment Override

```python
def apply_foreign_rules(insurance_result, employee):
    """Override insurance assessment for foreign workers."""
    
    # National pension — bilateral agreement
    if employee.kr_pension_agreement:
        insurance_result['national_pension'] = False
    
    # Employment insurance — by visa
    visa = employee.kr_visa_type
    
    mandatory_visas = ['F-2', 'F-5', 'F-6']
    voluntary_visas = ['F-4', 'E-9', 'H-2']
    
    if visa in mandatory_visas:
        insurance_result['employment_insurance'] = True
    elif visa in voluntary_visas:
        # Only if employee has opted in
        insurance_result['employment_insurance'] = not employee.kr_foreign_employ_exempt
    else:
        insurance_result['employment_insurance'] = False
```

---

## 4. Filing Differences

### 외국인 고용보험 가입 동의서

- Required for voluntary enrollment (F-4, E-9, H-2)
- PDF form with employee signature + stamp
- Must be filed BEFORE first premium deduction

### 원천징수영수증

- For flat-rate foreign workers: different form code
- Must specify whether flat rate or progressive was used

---

## 5. Edge Cases

### 5-1. Visa Change During Employment

If an employee's visa changes (e.g., E-9 → F-5):
- Insurance rules change from the date of visa change
- Must update employee record and recalculate

### 5-2. Dual Status Year

If a foreign worker becomes a resident (F-5) mid-year:
- Year-end settlement covers the full year
- Insurance rules change from visa change date
- May need to switch from flat tax to progressive (or vice versa)

### 5-3. 재외동포 (F-4) — Special Notes

- Most F-4 holders are Korean-ethnicity foreigners
- They often prefer progressive taxation (eligible for all deductions)
- Employment insurance is voluntary — must explicitly opt in
- Health/pension may have special rules depending on stay duration
