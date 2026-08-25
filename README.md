# 한국 로또 6/45 분석 프로그램

이 프로젝트는 로또 6/45 과거 데이터를 수집하고 분석하는 참고용 프로그램입니다.

로또는 무작위 추첨이며, 이 프로그램은 미래 당첨번호를 예측하거나 당첨을 보장하지 않습니다.

## 현재 단계

MVP 핵심 기능을 구현했습니다.

현재 가능한 작업:

- 단일 회차 데이터 수집
- 회차 범위 데이터 수집
- 최신 회차 추정 후 수집
- 수집 데이터 검증
- SQLite 데이터베이스 초기화
- 수집 데이터 SQLite 저장
- CSV 백업 생성
- JSON 백업 생성
- 번호별 전체 출현 횟수 분석
- 최근 10회, 30회, 100회, 300회 출현 횟수 분석
- 번호별 미출현 회차 수 분석
- 홀짝, 고저, 연속번호, 끝수, 합계, 구간 패턴 분석
- Frequency, Recency, Gap, Momentum 기반 번호 점수화
- Hot, Warm, Cold 번호 분류
- 조건 기반 추천 조합 생성
- 추천 조합 저장
- 발표 결과와 추천 조합 비교 평가
- 워크포워드 백테스트
- PNG 차트 출력
- 엑셀 리포트 출력
- 테스트용 가짜 응답을 이용한 단위 테스트

## 실행 방법

프로젝트 루트에서 실행합니다.

```powershell
python -m lotto_analyzer.main collect-draw 1
python -m lotto_analyzer.main collect-range 1 5
python -m lotto_analyzer.main collect-latest --start 1
python -m lotto_analyzer.main init-db
python -m lotto_analyzer.main save-draw 1
python -m lotto_analyzer.main save-range 1 5
python -m lotto_analyzer.main export-data
python -m lotto_analyzer.main analyze-frequency
python -m lotto_analyzer.main analyze-frequency --number 7
python -m lotto_analyzer.main analyze-patterns
python -m lotto_analyzer.main score-numbers
python -m lotto_analyzer.main generate-combinations --count 5 --strategy Hybrid
python -m lotto_analyzer.main recommend --count 5 --strategy Hybrid
python -m lotto_analyzer.main evaluate-recommendations 1150
python -m lotto_analyzer.main backtest 1000 1010 --strategy Hybrid
python -m lotto_analyzer.main export-charts
python -m lotto_analyzer.main export-report
```

동행복권 사이트가 접속 대기나 차단 화면을 반환하면 수집 명령이 실패할 수 있습니다. 이 경우 잠시 후 다시 실행합니다.

통계 분석 명령은 SQLite에 저장된 회차 데이터를 기준으로 실행됩니다. 먼저 `save-draw` 또는 `save-range`로 데이터를 저장해야 합니다.

추천 평가 명령은 추천 대상 회차의 실제 당첨 결과가 DB에 저장된 뒤 실행해야 합니다.

## 테스트 방법

```powershell
python -m unittest discover -s lotto_analyzer/tests
```

## 웹 대시보드

분석 결과는 웹에서 확인합니다.

<https://lotto007.streamlit.app>

로컬에서 띄우려면:

```powershell
python -m streamlit run dashboard/app.py
```

## 주간 자동 실행

매주 월요일 07:13(한국시간)에 GitHub Actions가 다음 흐름을 수행합니다.
PC 전원과 무관하게 GitHub 서버에서 실행됩니다.

```text
최신 회차 확인
-> 새 당첨번호 DB 입력
-> CSV/JSON 백업 갱신
-> 기존 추천 조합 평가
-> 다음 회차 추천 조합 생성
-> 엑셀 리포트 생성
-> 갱신된 데이터를 저장소에 커밋
```

수동 실행은 GitHub 저장소의 Actions 탭에서 "2. 주간 자동 분석" 워크플로우를
선택하고 **Run workflow**를 누릅니다. 별도 Secret 설정은 필요 없습니다.

로컬에서 직접 실행할 수도 있습니다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\GoogleDrive\lotto_analyzer\scripts\run_weekly_update.ps1 -Force
```

## 고지

```text
본 결과는 통계 분석 기반 참고자료이며
당첨을 보장하지 않습니다.
```
