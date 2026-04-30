# Manual Paid Onboarding Runbook

## 목적
이 문서는 한국형 Frappe/HRMS를 **셀프서브 결제 없이도 유료 구독으로 운영 가능한 managed pilot** 형태로 출시하기 위한 운영 표준이다.

## 근거
- `docs/prd/PRD-korea-hrms-integration.md:104-111` — 1차는 1개 사업장 파일럿 후 전 사업장 확대가 범위다.
- `docs/prd/PRD-korea-hrms-integration.md:146-152` — 신규 사업장 추가는 Company/Branch 생성 → YAML 생성 → sync → 첫 달 1원 단위 검증 흐름이다.
- `hrms/subscription_utils.py:30-59` — 플랜별 직원 수 기준(Basic 25 / Essential 50 / Professional 100)과 add-on 계산 로직이 이미 있다.

## 출시 정의
- **허용:** 수기 견적, 수기 청구, 수기 프로비저닝, 첫 달 shadow close, PM 동행 운영.
- **아직 미포함:** 셀프서브 결제, 카드 자동 과금, 고객 셀프 프로비저닝 포털.
- 즉, 첫 출시의 "유료 구독 가능"은 **고객이 돈을 내고 월 단위로 계속 쓰게 만들 수 있는 운영 체계**를 뜻한다.

## 플랜 운영 기준
- Basic: 활성 직원 25명까지
- Essential: 활성 직원 50명까지
- Professional: 활성 직원 100명까지
- 초과분은 `get_add_on_details(plan)` 기준으로 직원 add-on 수량을 산정한다.

## 온보딩 순서
1. 고객사명, 담당자, 월 활성 직원 수, 사업장 수를 수집한다.
2. 플랜을 Basic / Essential / Professional 중 하나로 확정한다.
3. 첫 청구는 외부 수기 청구서로 발행한다.
4. Frappe에 Company/Branch를 생성한다.
5. 사업장 YAML을 만든다.
6. `apply_worksite_master_from_yaml`로 사업장 sync를 검증한다.
7. 직원 2~5명 샘플로 employee/time export와 결과 import를 파일럿 검증한다.
8. 첫 달은 엔진 결과와 기존 급여 결과를 1원 단위로 대사한다.
9. 이상 없으면 전 직원/전 사업장으로 확대한다.

## 월간 운영 체크리스트
- 활성 직원 수와 플랜 한도를 비교한다.
- add-on 인원 수를 확정한다.
- 급여 마감 전 employee master / time&leave export smoke를 확인한다.
- 급여 import 후 Salary Slip / Korea Salary Slip Extension / Print Format 출력까지 확인한다.
- 이슈가 있으면 해당 월은 자동확장 없이 PM 수동 승인으로만 진행한다.

## 첫 고객 출하 기준
- 런타임 ping 정상
- Korea 핵심 테스트 통과
- authenticated Korea API smoke 정상
- 사업장 sync 정상
- 샘플 사업장 1곳 shadow close 완료
- 청구/갱신 담당자와 월 운영 캘린더 확정

## 보류 항목
- self-serve checkout
- 자동 결제 실패 회수(dunning)
- 멀티테넌트 셀프 프로비저닝
- 고객용 billing portal
