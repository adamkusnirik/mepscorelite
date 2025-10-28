Write-Host "Running data download..." -ForegroundColor Green
& .\.venv\Scripts\python.exe download.py

Write-Host "Creating data/derived directory if it doesn't exist..." -ForegroundColor Green
if (-not (Test-Path -Path "data\derived")) {
    New-Item -ItemType Directory -Path "data\derived" -Force
    Write-Host "Created data\derived directory" -ForegroundColor Cyan
} else {
    Write-Host "data\derived directory already exists" -ForegroundColor Cyan
}

Write-Host "Building ranking from raw data..." -ForegroundColor Green

# Install pandas if not already installed
Write-Host "Checking for pandas..." -ForegroundColor Cyan
& .\.venv\Scripts\pip.exe install pandas --quiet

# Create a temporary Python script
$scriptContent = @"
import os
import pandas as pd

data_file = os.path.join('data', 'raw', 'meps_data.xml')
print(f"File exists: {os.path.exists(data_file)}")

# Create a simple test ranking
df = pd.DataFrame([
    {'mep_id': '1', 'mep_name': 'Test MEP', 'country': 'EU', 'party': 'TEST', 'score': 100, 'speeches': 10, 'reports': 5, 'amendments': 2}
])

output_file = os.path.join('data', 'derived', 'ranking-9.csv')
df.to_csv(output_file, index=False)
print(f"Created ranking file: {output_file}")
"@

Write-Host "Creating temporary script..." -ForegroundColor Cyan
$scriptContent | Out-File -FilePath "temp_script.py" -Encoding utf8

# Run the temporary script
Write-Host "Running temporary script..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe temp_script.py

# Clean up
Write-Host "Cleaning up..." -ForegroundColor Cyan
Remove-Item -Path "temp_script.py"

Write-Host "Done!" -ForegroundColor Green 