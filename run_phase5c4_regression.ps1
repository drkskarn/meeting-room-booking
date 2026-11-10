$ErrorActionPreference = "Stop"

# ========================
# Phase 5C.4 Regression
# ========================
python -m pytest `
    tests/test_booking_audit_integrations.py `
    tests/test_user_audit_integrations.py `
    tests/test_room_audit_integrations.py `
    tests/test_audit_log_viewer.py `
    -v

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Phase 5C.4 regression test berjaya."
