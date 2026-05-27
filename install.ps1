# Activate virtual environment and install dependencies
Write-Host "Activating Python virtual environment..." -ForegroundColor Green

# Activate the venv
& .\.venv\Scripts\Activate.ps1

Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Green

# Install Python dependencies with upgrade flag
.\.venv\Scripts\pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt

if ($?) {
    Write-Host "All dependencies installed successfully!" -ForegroundColor Green
    Write-Host "You can now run: python app.py" -ForegroundColor Cyan
} else {
    Write-Host "Installation failed. Please check the error messages above." -ForegroundColor Red
}
