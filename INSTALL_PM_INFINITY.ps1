# PM-INFINITY installer — Windows 11 / PowerShell 5.1+
$ErrorActionPreference = "Stop"

$root = if (Test-Path "D:\") { "D:\PM_INFINITY" } else {
    Join-Path ([Environment]::GetFolderPath("MyDocuments")) "PM_INFINITY"
}
New-Item -ItemType Directory -Force -Path $root | Out-Null

$folders = @(
    "01_INBOX",
    "02_ACTIVE_JOBS",
    "03_DELIVERED_CLIENTS",
    "04_MASTER_ARCHIVE",
    "05_VIDEO_PROJECTS",
    "06_PHOTO_EXPORTS",
    "07_BUSINESS_ASSETS",
    "08_BACKUP_LOGS",
    "09_SYSTEM_TOOLS",
    "04_MASTER_ARCHIVE\2026",
    "07_BUSINESS_ASSETS\LOGOS_AND_BRANDING",
    "07_BUSINESS_ASSETS\PRESETS_AND_LUTS",
    "07_BUSINESS_ASSETS\PRICE_LISTS_AND_TEMPLATES"
)
foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path (Join-Path $root $folder) | Out-Null
}

$scriptDir = Join-Path $root "09_SYSTEM_TOOLS"
$backupScript = @'
$ErrorActionPreference = "Stop"
$source = Read-Host "Enter PM_INFINITY source folder (e.g. D:\PM_INFINITY)"
$destination = Read-Host "Enter BACKUP drive destination (e.g. E:\PM_INFINITY_BACKUP)"
if (!(Test-Path $source)) { throw "Source folder does not exist: $source" }
if (!(Test-Path $destination)) { New-Item -ItemType Directory -Force -Path $destination | Out-Null }
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$log = Join-Path $source "08_BACKUP_LOGS\backup_$stamp.log"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
Write-Host "Copying files. This can take time for large video projects..."
robocopy $source $destination /E /COPY:DAT /DCOPY:DAT /R:2 /W:5 /XJ /FFT /TEE "/LOG:$log"
$rc = $LASTEXITCODE
if ($rc -ge 8) { Write-Error "Robocopy reported a failure. Exit code: $rc. Review $log" }
else { Write-Host "Backup copy completed. Robocopy exit code: $rc. Log: $log" }
'@
$verifyScript = @'
$ErrorActionPreference = "Stop"
$root = Read-Host "Enter PM_INFINITY folder to verify"
if (!(Test-Path $root)) { throw "Folder not found: $root" }
$outDir = Join-Path $root "08_BACKUP_LOGS"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outFile = Join-Path $outDir ("sha256_manifest_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".csv")
$files = Get-ChildItem -LiteralPath $root -File -Recurse -Force |
    Where-Object { $_.FullName -notlike "$outDir\sha256_manifest_*" }
$total = $files.Count
$i = 0
$rows = foreach ($file in $files) {
    $i++
    Write-Progress -Activity "Hashing archive files" -Status "$i of $total : $($file.Name)" -PercentComplete (($i / [Math]::Max($total,1)) * 100)
    $hash = Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256
    [PSCustomObject]@{
        RelativePath = $file.FullName.Substring($root.TrimEnd('\').Length).TrimStart('\')
        Bytes = $file.Length
        LastWriteTimeUtc = $file.LastWriteTimeUtc.ToString("o")
        SHA256 = $hash.Hash
    }
}
$rows | Export-Csv -LiteralPath $outFile -NoTypeInformation -Encoding UTF8
Write-Host "Verification manifest created: $outFile"
Write-Host "Files hashed: $total. This records integrity fingerprints; it does not repair damaged files."
'@

Set-Content -LiteralPath (Join-Path $scriptDir "BACKUP_PM_INFINITY.ps1") -Value $backupScript -Encoding UTF8
Set-Content -LiteralPath (Join-Path $scriptDir "VERIFY_PM_INFINITY.ps1") -Value $verifyScript -Encoding UTF8

$dashboard = @"
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pete Media | PM Infinity Storage</title>
<style>
body{font:16px Segoe UI,Arial,sans-serif;background:#101114;color:#eee;margin:0;padding:32px}
main{max-width:900px;margin:auto}h1{color:#d6b66b;letter-spacing:1px}
.card{background:#1b1d22;border:1px solid #383a40;border-radius:12px;padding:18px;margin:14px 0}
code{color:#e7cf94}li{margin:8px 0}.muted{color:#aaa}
</style></head><body><main>
<h1>PETE MEDIA — INFINITY STORAGE</h1><p class="muted">PM-∞ | Local-first archive control panel</p>
<div class="card"><h2>Archive root</h2><p><code>$root</code></p></div>
<div class="card"><h2>Standard project structure</h2><ol>
<li><b>ORIGINALS</b> — untouched camera originals</li><li><b>WORKING</b> — Lightroom, Photoshop and Premiere project files</li>
<li><b>EDITED</b> — retouched photographs and rendered masters</li><li><b>DELIVERY</b> — client-ready exports</li><li><b>DOCUMENTS</b> — contracts, briefs and receipts</li></ol></div>
<div class="card"><h2>Operations</h2><ul>
<li>Backup: run <code>09_SYSTEM_TOOLS\BACKUP_PM_INFINITY.ps1</code></li>
<li>Integrity manifest: run <code>09_SYSTEM_TOOLS\VERIFY_PM_INFINITY.ps1</code></li>
<li>Logs and manifests: <code>08_BACKUP_LOGS</code></li></ul></div>
<div class="card"><h2>Safety rules</h2><ul><li>Never treat one copy as a backup.</li><li>Keep a second copy on a physically separate drive.</li>
<li>Do not delete camera originals until the backup and verification are complete.</li>
<li>Do not publish private client galleries without client permission.</li></ul></div>
</main></body></html>
"@
Set-Content -LiteralPath (Join-Path $root "PM_INFINITY_DASHBOARD.html") -Value $dashboard -Encoding UTF8

Write-Host ""
Write-Host "PM-INFINITY foundation installed at: $root" -ForegroundColor Green
Write-Host "Dashboard: $(Join-Path $root 'PM_INFINITY_DASHBOARD.html')"
Write-Host "Scripts: $scriptDir"
Start-Process (Join-Path $root "PM_INFINITY_DASHBOARD.html")
