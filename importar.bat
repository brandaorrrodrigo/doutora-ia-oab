@echo off
set POSTGRES_PASSWORD=changeme123
set POSTGRES_USER=postgres
set POSTGRES_DB=juris_ia
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
python importar_consolidadas.py
pause
