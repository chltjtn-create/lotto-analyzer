# 로또 분석기 대시보드 실행
# 사용법: .\lotto_analyzer\scripts\run_dashboard.ps1
# 브라우저에서 http://localhost:8501 접속

$ErrorActionPreference = "Stop"
Set-Location "D:\GoogleDrive"
cmd /c "echo. | python -m streamlit run lotto_analyzer\dashboard\app.py --server.port 8501"
