$ErrorActionPreference = "Stop"

# ========================
# Phase 5D Full Regression
# ========================
python -m pytest `
    tests/test_booking_audit_integrations.py `
    tests/test_user_audit_integrations.py `
    tests/test_room_audit_integrations.py `
    tests/test_audit_log_viewer.py `
    tests/test_booking_email_messages.py `
    tests/test_booking_email_integrations.py `
    -v

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Phase 5D regression berjaya."
Write-Host "Sasaran keseluruhan: 35 passed."
