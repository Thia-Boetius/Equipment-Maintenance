# Activate virtual environment and install dependencies
Write-Host "Activating Python virtual environment..." -ForegroundColor Green

# Activate the venv
& .\\.venv\Scripts\Activate.ps1

Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Green

# Install Python dependencies
pip install -r requirements.txt

Write-Host "All dependencies installed successfully!" -ForegroundColor Green
Write-Host "You can now run: python app.py" -ForegroundColor Cyan
