$inputJson = [Console]::In.ReadToEnd()

if ([string]::IsNullOrWhiteSpace($inputJson)) {
    exit 0
}

try {
    $payload = $inputJson | ConvertFrom-Json
} catch {
    exit 0
}

$filePath = $payload.tool_input.file_path

if ([string]::IsNullOrWhiteSpace($filePath)) {
    exit 0
}

$normalized = $filePath.Replace('\', '/')

$shouldCheck = (
    $normalized -match '/spark/' -or
    $normalized -match '/ML Layer/' -or
    $normalized -match '/ml/' -or
    $normalized -match '/Phase 2/'
)

if (-not $shouldCheck) {
    exit 0
}

$logDirectory = Join-Path (Get-Location) ".claude\hook-logs"

New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null

$logFile = Join-Path $logDirectory "quality-hooks.log"

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Add-Content $logFile "$timestamp | QUALITY HOOK | $filePath"

$grainTest = Get-ChildItem -Path . -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -match "test.*grain|grain.*test"
    } |
    Select-Object -First 1

$leakageTest = Get-ChildItem -Path . -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -match "test.*leak|leak.*test"
    } |
    Select-Object -First 1

if ($null -eq $grainTest -and $null -eq $leakageTest) {
    Add-Content $logFile "$timestamp | WARNING | No grain/leakage tests discovered"
    exit 0
}

if ($null -ne $grainTest) {
    python -m pytest "$($grainTest.FullName)" -q

    if ($LASTEXITCODE -ne 0) {
        Add-Content $logFile "$timestamp | FAIL | Grain test failed"
        exit 2
    }

    Add-Content $logFile "$timestamp | PASS | Grain test passed"
}

if ($null -ne $leakageTest) {
    python -m pytest "$($leakageTest.FullName)" -q

    if ($LASTEXITCODE -ne 0) {
        Add-Content $logFile "$timestamp | FAIL | Leakage test failed"
        exit 2
    }

    Add-Content $logFile "$timestamp | PASS | Leakage test passed"
}

exit 0