$ErrorActionPreference = "Stop"

$reviewDirectory = ".claude\review-results"

New-Item `
    -ItemType Directory `
    -Force `
    -Path $reviewDirectory | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

$outputFile = Join-Path `
    $reviewDirectory `
    "review-$timestamp.json"

$diff = git diff HEAD

if ([string]::IsNullOrWhiteSpace($diff)) {
    Write-Host "No changes detected."
    exit 0
}

$prompt = @"
Review the current repository changes.

Use .claude/review.md as the review specification.

Review all six categories:

1. data grain
2. feature leakage
3. geographic join
4. API contract
5. terminology
6. test coverage

Return a detailed engineering review.

Do not modify files.
Do not commit.
Do not merge.
Do not deploy.

Here is the current diff:

$diff
"@

$result = claude `
    --bare `
    -p $prompt `
    --allowedTools "Read,Grep,Glob" `
    --output-format json

$result | Set-Content `
    -Encoding UTF8 `
    -Path $outputFile

Write-Host ""
Write-Host "C15 review completed."
Write-Host "Result: $outputFile"