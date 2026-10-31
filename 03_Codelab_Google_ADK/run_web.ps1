# PowerShell script to run ADK Web UI locally
$env:PYTHONUTF8=1
Write-Host "Starting Google ADK Web UI for DevFest Assistant Agent..." -ForegroundColor Cyan
Write-Host "Open your browser at: http://127.0.0.1:8000" -ForegroundColor Green
..\.venv\Scripts\adk.exe web devfest_assistant_agent

