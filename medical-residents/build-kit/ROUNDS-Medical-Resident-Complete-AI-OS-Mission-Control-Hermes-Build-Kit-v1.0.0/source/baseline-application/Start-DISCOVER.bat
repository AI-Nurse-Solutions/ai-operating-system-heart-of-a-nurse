@echo off
setlocal
set "APP_DIR=%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js was not found. Opening portable mode, which uses separate browser storage.
  start "" "%APP_DIR%index.html"
  exit /b 0
)
start "" powershell -NoProfile -WindowStyle Hidden -Command "$ok=$false; 1..30 | ForEach-Object { try { $h=Invoke-RestMethod -UseBasicParsing 'http://127.0.0.1:43127/health'; if ($h.product -eq 'DISCOVER-NURSE-AI-OS-MISSION-CONTROL' -and $h.version -eq '2.0.0') { $ok=$true; break } } catch {}; Start-Sleep -Milliseconds 200 }; if ($ok) { Start-Process 'http://127.0.0.1:43127/' }"
node "%APP_DIR%server.mjs"
if errorlevel 1 (
  echo The local server did not start. Opening portable mode instead; it uses separate browser storage.
  start "" "%APP_DIR%index.html"
)
endlocal
