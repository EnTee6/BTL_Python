@echo off
set PYTHON_CMD="C:\Users\ADMIN\AppData\Local\Python\pythoncore-3.14-64\python.exe"

echo Dang khoi dong he thong bang Python cuc bo...
%PYTHON_CMD% run.py
pause
echo.
echo Dang chay Mo hinh Phan cum ^& PCA (analysis/clustering.py)...
%PYTHON_CMD% analysis/clustering.py
echo.

echo ====================================================================
echo [3] HOAN TAT PHAN TICH - KET QUA DA DUOC LUU
echo ====================================================================
echo Toan bo file CSV va Bieu do da duoc luu trong thu muc: output/
echo.

echo [4] KHOI DONG API SERVER
echo Dang mo Flask REST API tren mot cua so dong lenh rieng...
start "EPL 2024 API Server" cmd /k "%PYTHON_CMD% api/app.py"

echo.
echo Da khoi dong API Server thanh cong. Hien tai ban co the tra cuu thong qua CLI.
echo Cu phap tra cuu mau (Ghi de duong dan python cuc bo): 
echo %PYTHON_CMD% api/lookup.py --name "Mohamed Salah" --export
echo.
pause
