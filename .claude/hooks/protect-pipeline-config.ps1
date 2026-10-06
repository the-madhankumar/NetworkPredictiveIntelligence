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

$isSensitive = (
    $normalized -match '/src/AirFlow/' -or
    $normalized -match '/airflow/' -or
    $normalized -match 'pipeline.*config' -or
    $normalized -match '/config/'
)

if ($isSensitive) {
    Write-Host "PIPELINE CONFIGURATION CHANGE REQUESTED"
    Write-Host "File: $filePath"
    Write-Host "Explicit confirmation is required before this change."

    exit 2
}

exit 0