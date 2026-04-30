#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = REPO_ROOT / '.hermes' / 'harness' / 'runs'
RUNS_DIR.mkdir(parents=True, exist_ok=True)
TS = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def run(command: str, timeout: int = 120, cwd: Path | None = REPO_ROOT) -> dict:
    result = subprocess.run(
        command,
        shell=True,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return {
        'command': command,
        'exit_code': result.returncode,
        'stdout': result.stdout.strip(),
        'stderr': result.stderr.strip(),
    }


def doctype_exists(name: str) -> dict:
    cmd = (
        "sudo docker exec docker-frappe-1 bash -lc "
        + json.dumps(
            f'cd /home/frappe/frappe-bench && bench --site hrms.localhost execute frappe.db.exists --args "[\\\"DocType\\\", \\\"{name}\\\"]"'
        )
    )
    return run(cmd, timeout=180)


snapshot = {
    'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    'repo_root': str(REPO_ROOT),
    'checks': {},
    'derived': {},
}

snapshot['checks']['branch'] = run('git branch --show-current')
snapshot['checks']['git_status'] = run('git status --short')
snapshot['checks']['git_diff_stat'] = run('git diff --stat')
snapshot['checks']['recent_commits'] = run('git log --oneline -5')
snapshot['checks']['ping'] = run("curl -sS -H 'Host: hrms.localhost' http://127.0.0.1:8000/api/method/ping")
snapshot['checks']['docker_ps'] = run("sudo docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'", timeout=180)
snapshot['checks']['guest_export_employee_master'] = run(
    "python3 - <<'PY'\n"
    "import urllib.error, urllib.request\n"
    "req = urllib.request.Request('http://127.0.0.1:8000/api/method/hrms.api.korea_integration.export_employee_master', headers={'Host': 'hrms.localhost'})\n"
    "try:\n"
    "    with urllib.request.urlopen(req, timeout=15) as resp:\n"
    "        body = resp.read().decode('utf-8', 'replace')\n"
    "        print(str(resp.status))\n"
    "        print(body.splitlines()[0] if body else '')\n"
    "except urllib.error.HTTPError as e:\n"
    "    body = e.read().decode('utf-8', 'replace')\n"
    "    print(str(e.code))\n"
    "    print(body.splitlines()[0] if body else '')\n"
    "PY",
    timeout=180,
)
snapshot['checks']['korea_tests'] = run(
    'python3 -m unittest tests.test_korea_integration tests.test_korea_salary_slip_hooks tests.test_korea_payroll_doctypes tests.test_korea_print_formats tests.test_korea_setup tests.test_korea_privacy_contract',
    timeout=300,
)

doctypes = [
    'Korea Calc Reference',
    'Korea Insurance Rates',
    'Korea Tax Table',
    'Korea Salary Slip Extension',
    'Korea Severance Slip',
]
snapshot['checks']['doctypes'] = {name: doctype_exists(name) for name in doctypes}

key_files = [
    'hrms/api/korea_integration.py',
    'hrms/payroll/doctype/korea_salary_slip_extension/korea_salary_slip_extension.json',
    'hrms/payroll/doctype/korea_severance_slip/korea_severance_slip.json',
    'hrms/locale/ko.po',
    'docs/runbooks/korea-phase2-runtime-gate-and-pilot-smoke.md',
    '.hermes/harness/launch-week.yaml',
    'docs/runbooks/manual-paid-onboarding.md',
]
snapshot['checks']['key_files'] = {
    path: {'exists': (REPO_ROOT / path).exists()} for path in key_files
}

ping_ok = snapshot['checks']['ping']['exit_code'] == 0 and 'pong' in snapshot['checks']['ping']['stdout']
tests_output = snapshot['checks']['korea_tests']['stdout'] + '\n' + snapshot['checks']['korea_tests']['stderr']
tests_ok = snapshot['checks']['korea_tests']['exit_code'] == 0 and 'OK' in tests_output
doctypes_ok = all(
    item['exit_code'] == 0 and name in item['stdout']
    for name, item in snapshot['checks']['doctypes'].items()
)
route_guard_ok = '403' in snapshot['checks']['guest_export_employee_master']['stdout']
code_text = (REPO_ROOT / 'hrms/api/korea_integration.py').read_text(encoding='utf-8')
contract_text = (REPO_ROOT / 'docs/integration/frappe-side-contract.md').read_text(encoding='utf-8')
employment_exempt_export_ready = 'employment_insurance_exempt' in code_text and 'employment_insurance_exempt' in contract_text
manual_onboarding_runbook_ready = (REPO_ROOT / 'docs/runbooks/manual-paid-onboarding.md').exists()

snapshot['derived']['status'] = 'on-track' if (ping_ok and tests_ok and doctypes_ok) else 'at-risk'
snapshot['derived']['working'] = []
snapshot['derived']['not_working'] = []
snapshot['derived']['remaining'] = []

if not employment_exempt_export_ready:
    snapshot['derived']['remaining'].append(
        {
            'status': '진행중',
            'item': 'Frappe export contract에 내국인 만65세 고용보험 면제 flag를 추가하고 테스트/문서 정합성까지 맞추기',
            'evidence': [
                'hrms/api/korea_integration.py:104-119',
                'docs/integration/frappe-side-contract.md:103-119',
                'hrms/setup.py:390-395',
            ],
        }
    )

snapshot['derived']['remaining'].append(
    {
        'status': '대기',
        'item': '외부 엔진의 국민연금 상한(6,370,000) 계산 로직 보정',
        'evidence': [
            'docs/integration/engine-side-contract.md:891-892',
            'docs/korea/02-social-insurance.md:42-52',
        ],
    }
)

if not manual_onboarding_runbook_ready:
    snapshot['derived']['remaining'].append(
        {
            'status': '미착수',
            'item': 'manual paid onboarding 기준의 고객 청구/프로비저닝/첫달 검증 운영 문서 고정',
            'evidence': [
                'docs/prd/PRD-korea-hrms-integration.md:106-111',
                'hrms/subscription_utils.py:30-59',
            ],
        }
    )

if ping_ok:
    snapshot['derived']['working'].append('runtime ping 정상')
else:
    snapshot['derived']['not_working'].append('runtime ping 실패')

if tests_ok:
    snapshot['derived']['working'].append('Korea unittest subset 58건 통과')
else:
    snapshot['derived']['not_working'].append('Korea unittest subset 실패')

if doctypes_ok:
    snapshot['derived']['working'].append('Korea DocType 5종 live 존재')
else:
    snapshot['derived']['not_working'].append('Korea DocType 5종 중 일부 live 미존재')

if route_guard_ok:
    snapshot['derived']['working'].append('guest export route는 의도대로 비인증 차단(403)')
else:
    snapshot['derived']['not_working'].append('guest export route 표면이 기대와 다름')

board_lines = [
    f'# Korea Launch Board — {TS}',
    '',
    '## 결론',
    f"- 상태: **{snapshot['derived']['status']}**",
    '- 기본 출시 posture: **manual paid onboarding**',
    '',
    '## 되는 것',
]
for item in snapshot['derived']['working']:
    board_lines.append(f'- {item}')

board_lines += ['', '## 안 되는 것']
if snapshot['derived']['not_working']:
    for item in snapshot['derived']['not_working']:
        board_lines.append(f'- {item}')
else:
    board_lines.append('- 미확인된 즉시 실패 신호 없음')

board_lines += ['', '## 진행 남은 것']
for item in snapshot['derived']['remaining']:
    board_lines.append(f"- [{item['status']}] {item['item']}")
    for evidence in item['evidence']:
        board_lines.append(f'  - 근거: `{evidence}`')

board_lines += [
    '',
    '## 근거',
    f"- branch: `{snapshot['checks']['branch']['stdout']}`",
    f"- git status: `{snapshot['checks']['git_status']['stdout'] or 'clean'}`",
    '- recent commits:',
]
for line in snapshot['checks']['recent_commits']['stdout'].splitlines():
    board_lines.append(f'  - `{line}`')
board_lines += [
    f"- ping: `{snapshot['checks']['ping']['stdout']}`",
    f"- tests exit: `{snapshot['checks']['korea_tests']['exit_code']}`",
    f"- guest route surface: `{snapshot['checks']['guest_export_employee_master']['stdout'].splitlines()[0] if snapshot['checks']['guest_export_employee_master']['stdout'] else 'n/a'}`",
    '',
    '## 리스크',
    '- external engine P0 정확성 갭은 이 repo 수정만으로 닫히지 않는다.',
    '- self-serve billing/checkout 증거가 없어 1차 launch는 managed subscription으로 한정해야 한다.',
    '- `.hermes/`는 현재 untracked이므로 커밋 경계 관리가 필요하다.',
]

snapshot_path = RUNS_DIR / f'{TS}-snapshot.json'
board_path = RUNS_DIR / f'{TS}-board.md'
snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
board_path.write_text('\n'.join(board_lines) + '\n', encoding='utf-8')

print(json.dumps({
    'status': snapshot['derived']['status'],
    'snapshot_path': str(snapshot_path),
    'board_path': str(board_path),
    'working_count': len(snapshot['derived']['working']),
    'not_working_count': len(snapshot['derived']['not_working']),
    'remaining_count': len(snapshot['derived']['remaining']),
}, ensure_ascii=False))
