const { exec } = require('child_process');
const path = require('path');

console.log('Installing Equipment Maintenance dependencies...\n');

// Install Python dependencies from requirements.txt
exec('pip install -r requirements.txt', (error, stdout, stderr) => {
    if (error) {
        console.error(`Error installing Python dependencies: ${error.message}`);
        process.exit(1);
    }
    if (stderr) {
        console.warn(`Warning: ${stderr}`);
    }
    console.log('✓ Python dependencies installed successfully');
    console.log(stdout);
    console.log('\n✓ All dependencies installed successfully!');
    console.log('You can now run: python app.py');
});
