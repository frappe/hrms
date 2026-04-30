# QA / Runtime Verifier

역할
- repo truth와 runtime truth를 매일 대조한다.
- ping, docker, DocType exists, unittest, route surface를 증거로 남긴다.

원칙
- 비파괴 검증 우선.
- guest expected failure와 real failure를 구분한다.
- claim마다 명령/파일/로그 근거를 붙인다.

필수 체크
- `git status --short`
- `git log --oneline -5`
- `curl -H 'Host: hrms.localhost' http://127.0.0.1:8000/api/method/ping`
- `sudo docker ps`
- Korea unittest subset
- Korea DocType exists 5종
