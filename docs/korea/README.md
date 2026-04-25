# Frappe HRMS — Korea Payroll Localization

> Korean payroll, tax, and social insurance module for Frappe HRMS
> 프로젝트 리더: 공인노무사 서재홍 | 노무법인 위너스

---

## Why This Exists

Frappe HRMS has regional modules for India and UAE, but **none for Korea**.
Korean payroll has unique complexity:

- **4대보험** with mid-month hire/term rules, age exemptions, and year-end settlement
- **간이세액표** (simplified tax table) based withholding — not bracket-based
- **퇴직금** (severance) legally mandated with average-wage calculation
- **연말정산** (year-end settlement) with 7-step computation and Method A/B comparison
- **일용직** (daily workers) with entirely separate tax treatment

This project builds `hrms/regional/south_korea/` — a production-grade Korean payroll module
informed by **2+ years of real multi-site payroll automation** (11+ business locations, 100+ employees/month).

---

## Lessons Learned (시행착오 교훈)

These are hard-won rules from real payroll processing. **Every item below caused at least one real error.**

| # | Lesson | Impact |
|---|--------|--------|
| 1 | Mid-month hire: only 고용보험 deducted in first month | Wrong insurance deductions for every new hire |
| 2 | National pension uses NPS-notified amount, not formula | Mismatch with government records |
| 3 | Health insurance year-end settlement is **per calendar year** | Cross-year aggregation = wrong settlement |
| 4 | 산정월수 ≠ 납부월수 for mid-month hires | Settlement amount wrong |
| 5 | Age 60 pension exemption starts **month after** birthday month | One month early/late exemption |
| 6 | Employment insurance age-65 exemption depends on **hire date**, not current age | Wrong exemption for long-tenured workers |
| 7 | Mid-year termination tax: Method A vs B must be auto-compared | Choosing wrong method = overpaying tax |
| 8 | 기납부세액 must NOT include termination month's tax | Double-counting = wrong refund |
| 9 | Severance date = last working day + 1 | Off-by-one in service days |
| 10 | All calculated values must be Excel formulas, never hardcoded | Audit trail breaks with hardcoded values |
| 11 | Rounding differs by item: 고용보험=floor, 퇴직소득세=floor, 연말정산=ceil | Mixed rounding = 10~100원 errors |
| 12 | Foreign worker F-4 visa: voluntary insurance, no retroactive enrollment | Illegal retroactive deductions |
| 13 | 사업소득자 (3.3% tax) must be filtered out of 4대보험 processing | Wrong insurance filings |
| 14 | Daily worker tax: de minimis rule (< 1,000원 = no tax) | Overcharging low-wage daily workers |
| 15 | 주휴수당 only applies to 15+ hours/week | Wrong pay for part-timers |

---

## Architecture

```
hrms/regional/south_korea/
├── __init__.py
├── setup.py                    # Korea-specific setup (tax tables, insurance rates)
├── utils.py                    # Shared Korean payroll utilities
├── tax/
│   ├── simplified_tax_table.py # 간이세액표 lookup engine
│   ├── income_tax.py           # 소득세 withholding
│   ├── year_end_settlement.py  # 연말정산 7-step engine
│   ├── severance_tax.py        # 퇴직소득세
│   └── daily_worker_tax.py     # 일용직 세금
├── insurance/
│   ├── social_insurance.py     # 4대보험 계산 엔진
│   ├── rates.py                # 연도별 요율 관리
│   ├── exemptions.py           # 연령/비자별 면제 로직
│   └── settlement.py           # 건보 보수총액 정산
├── severance/
│   ├── calculator.py           # 퇴직금 계산 (3개월 평균임금)
│   └── service_period.py       # 재직일수/근속연수 계산
├── salary/
│   ├── components.py           # 한국 급여 구성요소 정의
│   ├── nontaxable.py           # 비과세 항목 관리
│   └── minimum_wage.py         # 최저임금 검증
├── foreign_worker/
│   ├── tax.py                  # 19% 단일세율 옵션
│   └── insurance.py            # 비자별 보험 적용
└── reports/
    ├── payslip_kr.py           # 한국식 급여명세서
    ├── withholding_report.py   # 원천징수이행상황신고서
    └── insurance_report.py     # 4대보험 취득/상실 신고서
```

---

## Implementation Roadmap

### Phase 1: Core Payroll Engine (MVP)
> Goal: 기본급 → 실지급액 자동 산출

| # | Deliverable | Spec Doc | Priority |
|---|-------------|----------|----------|
| 1 | Salary Structure (급여구조) | [01-salary-structure.md](01-salary-structure.md) | P0 |
| 2 | Social Insurance (4대보험) | [02-social-insurance.md](02-social-insurance.md) | P0 |
| 3 | Income Tax Withholding (소득세) | [03-income-tax.md](03-income-tax.md) | P0 |
| 6 | Minimum Wage (최저임금) | [06-minimum-wage.md](06-minimum-wage.md) | P0 |
| 7 | Working Hours & Overtime (근로시간) | [07-working-hours.md](07-working-hours.md) | P0 |

### Phase 2: Hire/Termination Lifecycle
> Goal: 입퇴사 전 과정 자동 처리

| # | Deliverable | Spec Doc | Priority |
|---|-------------|----------|----------|
| 2+ | Mid-month Insurance Rules | [02-social-insurance.md](02-social-insurance.md) §4-5 | P1 |
| 5 | Severance Pay (퇴직금) | [05-severance.md](05-severance.md) | P1 |
| 4- | Mid-year Termination Tax | [04-year-end-settlement.md](04-year-end-settlement.md) §6 | P1 |

### Phase 3: Annual Settlement & Advanced
> Goal: 연말정산 + 특수 근로자

| # | Deliverable | Spec Doc | Priority |
|---|-------------|----------|----------|
| 4 | Year-end Settlement (연말정산) | [04-year-end-settlement.md](04-year-end-settlement.md) | P2 |
| 8 | Daily Workers (일용직) | [08-daily-workers.md](08-daily-workers.md) | P2 |
| 9 | Foreign Workers (외국인) | [09-foreign-workers.md](09-foreign-workers.md) | P2 |

### Phase 4: Integration & Reports
> Goal: 전자신고 + 리포트

| # | Deliverable | Spec Doc | Priority |
|---|-------------|----------|----------|
| 10 | Frappe Customization & Integration | [10-frappe-customization.md](10-frappe-customization.md) | P3 |
| - | Electronic Filing (전자신고) | TBD | P3 |
| - | Korean Payslip Format | TBD | P3 |

---

## Spec Documents

| # | Title | File | Status |
|---|-------|------|--------|
| 01 | 급여 구조 (Salary Structure) | [01-salary-structure.md](01-salary-structure.md) | Draft |
| 02 | 4대보험 (Social Insurance) | [02-social-insurance.md](02-social-insurance.md) | Draft |
| 03 | 소득세 (Income Tax) | [03-income-tax.md](03-income-tax.md) | Draft |
| 04 | 연말정산 (Year-end Settlement) | [04-year-end-settlement.md](04-year-end-settlement.md) | Draft |
| 05 | 퇴직금 (Severance Pay) | [05-severance.md](05-severance.md) | Draft |
| 06 | 최저임금 (Minimum Wage) | [06-minimum-wage.md](06-minimum-wage.md) | Draft |
| 07 | 근로시간 (Working Hours) | [07-working-hours.md](07-working-hours.md) | Draft |
| 08 | 일용직 (Daily Workers) | [08-daily-workers.md](08-daily-workers.md) | Draft |
| 09 | 외국인 (Foreign Workers) | [09-foreign-workers.md](09-foreign-workers.md) | Draft |
| 10 | Frappe 커스터마이징 | [10-frappe-customization.md](10-frappe-customization.md) | Draft |

---

## Quality Standards

Every calculation module must meet these criteria before release:

- [ ] **3건 이상 실데이터 크로스체크** — real payroll data verification
- [ ] **단수처리 정확** — rounding rules per item type
- [ ] **중도입퇴사 테스트** — mid-month hire/term edge cases
- [ ] **연령면제 테스트** — age-based exemption boundaries
- [ ] **국세청/공단 프로그램 대조** — cross-verify with official tools

---

## Contributing

1. Each spec doc is the single source of truth for that domain
2. Code changes must reference the spec doc section
3. Rate changes (annual) go in `insurance/rates.py` with effective dates
4. All monetary calculations: round rules documented inline

---

## Legal References

| Source | URL | Purpose |
|--------|-----|---------|
| 근로기준법 | law.go.kr | 근로시간, 수당, 퇴직금 |
| 소득세법 | law.go.kr | 세율, 공제, 연말정산 |
| 국민연금법 | law.go.kr | 요율, 상한/하한 |
| 국민건강보험법 | law.go.kr | 건보/장기요양 요율 |
| 고용보험법 | law.go.kr | 고용보험 요율, 면제 |
| 근로자퇴직급여보장법 | law.go.kr | 퇴직금 계산 |
| 국세청 간이세액표 | nts.go.kr | 월별 원천징수 |
