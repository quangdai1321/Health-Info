@echo off
chcp 65001 >nul
echo === Chuan bi cho demo tren Vercel ===
echo 1. Mo cau noi o cong 11435
start "cau noi" cmd /k python "%~dp0cau_noi.py"
timeout /t 3 >nul
echo 2. Mo duong ham ra dia chi https cong khai
echo    Cho dong chu "https://....trycloudflare.com" roi dan dia chi do vao trang demo.
echo.
"%~dp0cloudflared.exe" tunnel --url http://localhost:11435 --no-autoupdate
