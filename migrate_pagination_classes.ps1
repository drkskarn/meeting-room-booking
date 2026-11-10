# ========================
# Global Pagination Class Migration
# ========================
# Run from the project root, for example:
# C:\laragon\www\meeting-room-booking
#
# This script:
# 1. Updates pagination class names in the four admin templates.
# 2. Creates a .bak backup before changing each file.
# 3. Does not alter route/filter/pagination logic.

$ErrorActionPreference = "Stop"

$templates = @(
    "app\templates\admin\users.html",
    "app\templates\admin\bookings.html",
    "app\templates\admin\rooms.html",
    "app\templates\admin\audit_logs.html"
)

$replacements = [ordered]@{
    "audit-pagination"    = "app-pagination"
    "audit-page-link"     = "app-page-link"
    "audit-page-arrow"    = "app-page-arrow"
    "audit-page-ellipsis" = "app-page-ellipsis"
}

foreach ($relativePath in $templates) {
    $path = Join-Path (Get-Location) $relativePath

    if (-not (Test-Path $path)) {
        Write-Warning "Fail tidak dijumpai: $relativePath"
        continue
    }

    $backupPath = "$path.bak"
    Copy-Item $path $backupPath -Force

    $content = Get-Content $path -Raw -Encoding UTF8

    foreach ($oldClass in $replacements.Keys) {
        $content = $content.Replace(
            $oldClass,
            $replacements[$oldClass]
        )
    }

    Set-Content -Path $path -Value $content -Encoding UTF8

    Write-Host "Dikemaskini: $relativePath"
    Write-Host "Backup     : $relativePath.bak"
}

Write-Host ""
Write-Host "Migrasi pagination selesai."
