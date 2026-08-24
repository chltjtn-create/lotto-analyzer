@echo off
cd /d D:\GoogleDrive
echo. | python -m streamlit run lotto_analyzer\dashboard\app.py --server.port 8501
