# scripts\download_books.ps1
$dest = "data\corpus"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

# Download the catalog of text files (it's a big list, but one request)
Write-Host "Fetching Gutenberg catalog list..."
$catalog = Invoke-WebRequest -Uri "https://www.gutenberg.org/robot/harvest?filetypes[]=txt&langs[]=en" -UseBasicParsing
$links = $catalog.Links | Where-Object { $_.href -match '\.txt$' } | Select-Object -First 200

Write-Host "Downloading $($links.Count) books..."
$count = 0
foreach ($link in $links) {
    $count++
    $url = $link.href
    if ($url -notmatch '^http') { $url = "https://www.gutenberg.org" + $url }
    $filename = Split-Path $url -Leaf
    $outPath = Join-Path $dest "gutenberg_$filename"
    if (Test-Path $outPath) { continue }
    
    try {
        Invoke-WebRequest -Uri $url -OutFile $outPath -UseBasicParsing -TimeoutSec 30
        Write-Host "[$count] Saved $filename"
    } catch {
        Write-Host "[$count] Failed: $url"
    }
    Start-Sleep -Seconds 2   # polite delay
}
Write-Host "Done. Files are in $dest"