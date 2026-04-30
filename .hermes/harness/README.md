# Frappe/HRMS Launch Harness

## 목적
이 하네스는 `/home/ubuntu/worktrees/hrms-prA-korea-calc-reference` 기준으로 한국형 Frappe/HRMS를 **유료 구독 가능한 출시 수준**까지 밀기 위한 PM 실행체계다.

여기서 기본 출시 정의는 다음이다.
- **1차 출시 형태:** 셀프서브 결제가 아니라 **수동 유료 온보딩 가능한 managed subscription**
- 고객은 계약/청구는 수동으로 진행하되, 제품은 실제 운영 가능한 payroll/worksite/integration/runtime 품질을 갖춘다.
- `privacy_broker` 라이브 연동과 셀프서브 결제는 1차 범위 밖이다.

## 이번 주 Definition of Done
1. Frappe 런타임 health와 Korea API smoke가 매일 근거 기반으로 추적된다.
2. `Korea Calc Reference`, `Korea Insurance Rates`, `Korea Tax Table`, `Korea Salary Slip Extension`, `Korea Severance Slip`의 repo/runtime 상태가 일치한다.
3. 한국형 급여 핵심 테스트 묶음이 반복 통과한다.
4. 런칭 blocker가 `되는 것 / 안 되는 것 / 남은 것`으로 분리되어 문서화된다.
5. 최소 1개 고객을 수동 유료 온보딩할 수 있는 운영 보드와 회고 루프가 돌아간다.

## 이번 주 우선순위
1. **정확성 P0** — 국민연금 상한, 내국인 만65세 고용보험 면제 같은 런칭 저지 이슈 분리
2. **경계면 안정성** — Frappe ↔ 엔진 ↔ YAML worksite sync ↔ import contract drift 제거
3. **운영 출시성** — 수동 billing/onboarding/provisioning/runbook을 제품 수준으로 고정

## 운영 원칙
- 작은 안전 범위로 수정하고 즉시 테스트/런타임 검증한다.
- repo truth와 runtime truth를 항상 분리해서 본다.
- 외부 엔진 이슈와 Frappe boundary 이슈를 섞지 않는다.
- 증거 없는 주장은 `미검증`으로 둔다.
- paid launch는 당분간 **manual high-touch onboarding**을 기본값으로 둔다.

## 주요 산출물
- `.hermes/harness/launch-week.yaml`
- `.hermes/harness/prompts/*.md`
- `.hermes/harness/runs/*-snapshot.json`
- `.hermes/harness/runs/*-board.md`
- `scripts/korea_launch_harness.py`

## 실행 명령
```bash
python3 scripts/korea_launch_harness.py
```

## 현재 판단
- 런타임 health/ping과 Korea 테스트 묶음은 강한 양호 신호다.
- 하지만 paid subscription 제품으로 보려면 아직 **운영 온보딩/과금 posture**가 셀프서브가 아니라 수동형으로 고정되어야 한다.
- 외부 엔진의 P0 정확성 갭은 이 repo 안에서 해결 불가한 항목이 있어, PM 레벨에서 별도 트랙으로 밀어야 한다.
