# Korea Phase 2 runtime gate + pilot smoke runbook

## 목적
- `feature/korea-payroll-docs`에 landed 된 Korea Phase 2 변경을 실제 docker 런타임에 안전하게 반영한다.
- 반영 후 `bench migrate`, `DocType exists`, `import/worksite API smoke`를 같은 순서로 검증한다.
- 부평/올샤 파일럿 진입 전, 어떤 항목이 이미 live이고 어떤 항목이 아직 repo-only 인지 분리해서 본다.

## 전제
- 실제 실행 런타임은 `docker-frappe-1:/home/frappe/frappe-bench`
- worktree 변경은 runtime에 자동 반영되지 않는다.
- 따라서 **PR 머지 = live 반영 완료**가 아니다.

## 이번 세션 기준 확인된 사실
### 현재 live health
- `curl -H 'Host: hrms.localhost' http://127.0.0.1:8000/api/method/ping`
- 결과: `{"message":"pong"}`

### 현재 live DocType 상태
- `Korea Calc Reference` → live 존재 확인
- `Korea Insurance Rates` → 아직 live 미반영
- `Korea Tax Table` → 아직 live 미반영

실행 근거:
```bash
sudo docker exec docker-frappe-1 bash -lc 'cd /home/frappe/frappe-bench && \
bench --site hrms.localhost execute frappe.db.exists --args "[""DocType"", ""Korea Calc Reference""]" && echo --- && \
bench --site hrms.localhost execute frappe.db.exists --args "[""DocType"", ""Korea Insurance Rates""]" && echo --- && \
bench --site hrms.localhost execute frappe.db.exists --args "[""DocType"", ""Korea Tax Table""]"'
```

### 현재 live app tree 상태
- container 내부 `/home/frappe/frappe-bench/apps/hrms`에는 `korea_calc_reference`만 확인됨
- `korea_insurance_rates`, `korea_tax_table`, `salary_slip/korea_salary_slip.py`는 아직 미배포 상태

## Gate 1. 배포 전 점검
1. base 브랜치 HEAD 확인
```bash
git fetch origin --prune
git log --oneline -3 origin/feature/korea-payroll-docs
```

2. live health 확인
```bash
curl -s -H 'Host: hrms.localhost' http://127.0.0.1:8000/api/method/ping
```
정상값: `{"message":"pong"}`

3. container 내부 상태 확인
```bash
sudo docker exec docker-frappe-1 bash -lc 'cd /home/frappe/frappe-bench/apps/hrms && git status --short'
```

## Gate 2. Hot-deploy 대상 최소 범위
이번 Phase 2 landed 범위에서 runtime 반영 대상 최소 세트:
- `hrms/setup.py`
- `hrms/hooks.py`
- `hrms/payroll/doctype/korea_calc_reference/*`
- `hrms/payroll/doctype/korea_insurance_rates/*`
- `hrms/payroll/doctype/korea_tax_table/*`
- `hrms/payroll/doctype/salary_slip/korea_salary_slip.py`

## Gate 3. 안전 배포 절차
1. container 내부 백업 디렉토리 생성
```bash
sudo docker exec docker-frappe-1 bash -lc 'mkdir -p /home/frappe/runtime-backups'
```

2. host에서 reviewed 파일만 tar 패키징
```bash
cd /home/ubuntu/worktrees/hrms-prA-korea-calc-reference
tar -cf /tmp/korea-phase2-runtime.tar \
  hrms/setup.py \
  hrms/hooks.py \
  hrms/payroll/doctype/korea_calc_reference \
  hrms/payroll/doctype/korea_insurance_rates \
  hrms/payroll/doctype/korea_tax_table \
  hrms/payroll/doctype/salary_slip/korea_salary_slip.py
```

3. container로 복사
```bash
sudo docker cp /tmp/korea-phase2-runtime.tar docker-frappe-1:/home/frappe/runtime-backups/korea-phase2-runtime.tar
```

4. container 내부 backup + extract
```bash
sudo docker exec docker-frappe-1 bash -lc '
set -e
TS=$(date +%Y%m%d-%H%M%S)
BK=/home/frappe/runtime-backups/$TS
mkdir -p "$BK"
cd /home/frappe/frappe-bench/apps/hrms
cp -a hrms/setup.py "$BK/" || true
cp -a hrms/hooks.py "$BK/" || true
cp -a hrms/payroll/doctype/korea_calc_reference "$BK/" || true
cp -a hrms/payroll/doctype/korea_insurance_rates "$BK/" || true
cp -a hrms/payroll/doctype/korea_tax_table "$BK/" || true
cp -a hrms/payroll/doctype/salary_slip/korea_salary_slip.py "$BK/" || true
cd /home/frappe/frappe-bench/apps/hrms
tar -xf /home/frappe/runtime-backups/korea-phase2-runtime.tar
'
```

5. python compile check
```bash
sudo docker exec docker-frappe-1 bash -lc 'cd /home/frappe/frappe-bench/apps/hrms && \
python -m py_compile \
  hrms/setup.py \
  hrms/hooks.py \
  hrms/payroll/doctype/korea_calc_reference/korea_calc_reference.py \
  hrms/payroll/doctype/korea_insurance_rates/korea_insurance_rates.py \
  hrms/payroll/doctype/korea_tax_table/korea_tax_table.py \
  hrms/payroll/doctype/salary_slip/korea_salary_slip.py'
```

6. migrate
```bash
sudo docker exec docker-frappe-1 bash -lc 'cd /home/frappe/frappe-bench && bench --site hrms.localhost migrate'
```

## Gate 4. migrate 후 필수 검증
### 4-1. DocType 등록 확인
```bash
sudo docker exec docker-frappe-1 bash -lc 'cd /home/frappe/frappe-bench && \
bench --site hrms.localhost execute frappe.db.exists --args "[""DocType"", ""Korea Calc Reference""]" && echo --- && \
bench --site hrms.localhost execute frappe.db.exists --args "[""DocType"", ""Korea Insurance Rates""]" && echo --- && \
bench --site hrms.localhost execute frappe.db.exists --args "[""DocType"", ""Korea Tax Table""]"'
```
기대값:
- `Korea Calc Reference`
- `Korea Insurance Rates`
- `Korea Tax Table`

### 4-2. SQL ground truth
```bash
sudo docker exec docker-frappe-1 bash -lc 'cd /home/frappe/frappe-bench && \
bench --site hrms.localhost mariadb -N -e "
select name,module from tabDocType where name in (\"Korea Calc Reference\",\"Korea Insurance Rates\",\"Korea Tax Table\") order by name;
"'
```

### 4-3. hook file load 확인
```bash
sudo docker exec docker-frappe-1 bash -lc 'cd /home/frappe/frappe-bench && \
bench --site hrms.localhost execute frappe.get_attr --args "[""hrms.payroll.doctype.salary_slip.korea_salary_slip.apply_korea_salary_slip_fields""]"'
```

### 4-4. site health 재확인
```bash
curl -s -H 'Host: hrms.localhost' http://127.0.0.1:8000/api/method/ping
```

## Gate 5. API smoke
### 인증 없는 ping
```bash
curl -s -H 'Host: hrms.localhost' http://127.0.0.1:8000/api/method/ping
```

### 인증 필요한 Korea API
비로그인 호출 시 PermissionError가 나오는지 먼저 확인한다. 현재 세션 기준 `export_employee_master`는 로그인 요구를 정상 반환했다.
```bash
curl -s -H 'Host: hrms.localhost' http://127.0.0.1:8000/api/method/hrms.api.korea_integration.export_employee_master
```
기대값:
- anonymous 접근 거부 (PermissionError)
- 즉, endpoint route 자체는 응답 중

### 로그인 세션 또는 API key가 준비된 경우 smoke
- `export_employee_master`
- `export_time_and_leave`
- `notify_worksite_master_change`
- `apply_worksite_master_from_yaml`

판정 기준:
- 500/ImportError 없음
- contract shape 유지
- worksite lock/rejected_locked 동작 유지

## 파일럿 범위 고정 메모
- `privacy_broker live integration is deferred for this pilot`.
- `do not hot-deploy placeholder broker code` without endpoint/auth/audit spec.
- `PII lookup stays outside Frappe runtime` and must be handled by manual or external secure-store procedures.

## 파일럿 진입 전 최종 체크리스트
- [ ] `bench migrate` 성공
- [ ] `Korea Calc Reference` / `Korea Insurance Rates` / `Korea Tax Table` exists 확인
- [ ] `apply_korea_salary_slip_fields` load 확인
- [ ] ping 정상
- [ ] import/worksite API smoke 정상
- [ ] 부평 parallel run 1개월치 비교 준비
- [ ] 올샤는 부평 안정화 1주 후 진입

## 리스크 메모
1. worktree와 runtime 불일치가 가장 큰 운영 리스크다.
2. PR-22 hook은 isolated test는 통과했지만, 실제 lifecycle ordering smoke는 runtime에서 한 번 더 봐야 한다.
3. custom fields는 code merge만으로 자동 생성되지 않으므로, migrate 이후 실제 field surface 확인이 필요하다.

## 이번 세션의 운영 결론
- cleanup은 완료: `/` 사용률 `61% -> 53%`
- Phase 2 code line은 PR-20, PR-21, PR-22까지 머지 완료
- 다음 실운영 관문은 **PR-23 runbook대로 runtime hot-deploy + smoke**다.
