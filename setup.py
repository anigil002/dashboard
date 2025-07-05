# setup_windows.py - Windows-compatible setup script (no Unicode characters)

import subprocess
import sys
import os
from pathlib import Path
import json

def run_command(command, description):
    """Run a command and return success status"""
    print(f"[*] {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[+] {description} - Success")
            return True
        else:
            print(f"[-] {description} - Failed")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"[-] {description} - Exception: {e}")
        return False

def check_anaconda():
    """Check if Anaconda is properly installed"""
    print("\n[*] Checking Anaconda installation...")
    
    # Check conda command
    if run_command("conda --version", "Checking conda"):
        print("[+] Anaconda/Miniconda is installed")
        return True
    else:
        print("[-] Conda not found in PATH")
        return False

def create_environment():
    """Create a dedicated environment for the dashboard"""
    print("\n[*] Creating dedicated environment...")
    
    env_name = "recruitment-dashboard"
    
    # Check if environment already exists
    result = subprocess.run("conda env list", shell=True, capture_output=True, text=True)
    if env_name in result.stdout:
        print(f"[!] Environment '{env_name}' already exists")
        
        # Ask user if they want to remove and recreate
        while True:
            recreate = input("Do you want to recreate the environment? (y/n): ").lower().strip()
            if recreate in ['y', 'yes']:
                run_command(f"conda env remove -n {env_name} -y", f"Removing existing environment")
                break
            elif recreate in ['n', 'no']:
                return env_name
            else:
                print("Please enter 'y' for yes or 'n' for no")
    
    # Create new environment with Python 3.11 (more stable than 3.12)
    success = run_command(
        f"conda create -n {env_name} python=3.11 -y",
        f"Creating environment '{env_name}'"
    )
    
    if success:
        print(f"[+] Environment '{env_name}' created successfully")
        return env_name
    else:
        print("[-] Failed to create environment")
        return None

def install_packages(env_name):
    """Install required packages in the environment"""
    print(f"\n[*] Installing packages in '{env_name}' environment...")
    
    # Packages to install via conda (preferred for data science)
    conda_packages = [
        "pandas",
        "numpy", 
        "openpyxl",
        "xlrd"
    ]
    
    # Packages to install via pip (not available in conda or newer versions needed)
    pip_packages = [
        "flask==2.3.3",
        "werkzeug==2.3.7",
        "scikit-learn",
        "joblib"
    ]
    
    # Install conda packages
    conda_cmd = f"conda install -n {env_name} " + " ".join(conda_packages) + " -c conda-forge -y"
    if not run_command(conda_cmd, "Installing conda packages"):
        print("[-] Failed to install conda packages")
        return False
    
    # Install pip packages
    pip_cmd = f"conda run -n {env_name} pip install " + " ".join(pip_packages)
    if not run_command(pip_cmd, "Installing pip packages"):
        print("[!] Some pip packages failed to install, but continuing...")
    
    return True

def test_installation(env_name):
    """Test if all packages are working"""
    print(f"\n[*] Testing installation in '{env_name}' environment...")
    
    test_script = '''
import sys
print("Python version: " + sys.version)

try:
    import flask
    print("[+] Flask " + flask.__version__)
except ImportError as e:
    print("[-] Flask: " + str(e))

try:
    import pandas as pd
    print("[+] Pandas " + pd.__version__)
except ImportError as e:
    print("[-] Pandas: " + str(e))

try:
    import numpy as np
    print("[+] Numpy " + np.__version__)
except ImportError as e:
    print("[-] Numpy: " + str(e))

try:
    import openpyxl
    print("[+] Openpyxl " + openpyxl.__version__)
except ImportError as e:
    print("[-] Openpyxl: " + str(e))

try:
    import sklearn
    print("[+] Scikit-learn " + sklearn.__version__)
except ImportError as e:
    print("[!] Scikit-learn: " + str(e) + " (AI features will be disabled)")

print("\\n[+] Package testing completed!")
'''
    
    # Save test script with UTF-8 encoding
    try:
        with open("test_packages.py", "w", encoding='utf-8') as f:
            f.write(test_script)
    except:
        # Fallback to default encoding without special characters
        with open("test_packages.py", "w") as f:
            f.write(test_script.replace('[+]', '[OK]').replace('[-]', '[ERR]').replace('[!]', '[WARN]'))
    
    # Run test
    success = run_command(f"conda run -n {env_name} python test_packages.py", "Testing packages")
    
    # Clean up
    if os.path.exists("test_packages.py"):
        os.remove("test_packages.py")
    
    return success

def create_vscode_settings(env_name):
    """Create VS Code settings for the project"""
    print(f"\n[*] Creating VS Code settings...")
    
    # Get conda environment path
    result = subprocess.run("conda info --base", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        conda_base = result.stdout.strip()
        
        # Handle different possible paths
        if os.name == 'nt':  # Windows
            python_path = f"{conda_base}\\envs\\{env_name}\\python.exe"
        else:
            python_path = f"{conda_base}/envs/{env_name}/bin/python"
        
        # Create .vscode directory
        vscode_dir = Path(".vscode")
        vscode_dir.mkdir(exist_ok=True)
        
        # Create settings.json
        settings = {
            "python.defaultInterpreterPath": python_path,
            "python.terminal.activateEnvironment": True,
            "files.associations": {
                "*.html": "html"
            },
            "emmet.includeLanguages": {
                "html": "html"
            },
            "files.encoding": "utf8"
        }
        
        with open(vscode_dir / "settings.json", "w", encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
        
        print(f"[+] VS Code settings created")
        print(f"[*] Python interpreter: {python_path}")
        return True
    else:
        print("[!] Could not determine conda base path")
        return False

def create_activation_script(env_name):
    """Create activation scripts for easy environment switching"""
    print(f"\n[*] Creating activation scripts...")
    
    # Windows batch script
    batch_script = f'''@echo off
echo Starting Recruitment Dashboard Environment
echo.
call conda activate {env_name}
echo [+] Environment '{env_name}' activated
echo.
echo Quick commands:
echo   python app.py          - Start the dashboard
echo   python setup.py        - Run setup again
echo   conda deactivate       - Exit environment
echo.
cmd /k
'''
    
    with open("activate_env.bat", "w") as f:
        f.write(batch_script)
    
    print("[+] Activation script created: activate_env.bat")

def create_project_structure():
    """Create the project directory structure"""
    print(f"\n[*] Creating project structure...")
    
    directories = [
        "uploads",
        "models", 
        "templates",
        "static/css",
        "static/js",
        "static/img"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Create placeholder logo
    logo_placeholder = Path("static/img/placeholder.png")
    if not logo_placeholder.exists():
        with open(logo_placeholder, "w") as f:
            f.write("# Replace with your company logo (200x50 px recommended)")
    
    print("[+] Project structure created")

def create_sample_data(env_name):
    """Create sample Excel file for testing"""
    print(f"\n[*] Creating sample data...")
    
    sample_script = '''
import pandas as pd
from datetime import datetime, timedelta
import random

# Sample data generation
ta_partners = ['Alice Brown', 'Bob Smith', 'Carol Davis', 'David Wilson']
roles = ['Software Engineer', 'Data Scientist', 'Product Manager', 'Sales Manager']
countries = ['United States', 'United Kingdom', 'Germany', 'Canada']
projects = ['Project Alpha', 'Project Beta', 'Project Gamma']

# Generate hired data
hired_data = []
for i in range(50):
    pos_created = datetime.now() - timedelta(days=random.randint(30, 365))
    filled_date = pos_created + timedelta(days=random.randint(10, 80))
    
    hired_data.append({
        'Position Created Date': pos_created,
        'Filled Date': filled_date,
        'Hiring Manager': f'Manager {random.randint(1, 10)}',
        'TA Partner': random.choice(ta_partners),
        'Sourcing Partner': random.choice(ta_partners),
        'Country': random.choice(countries),
        'Project': random.choice(projects),
        'Role': random.choice(roles),
        'Number of CVs shared': random.randint(10, 100),
        'Number of 1st interviews': random.randint(2, 20),
        'Number of offers': random.randint(1, 5),
        'Number of accepted offers': 1,
        'Max budgeted salary': random.randint(50000, 150000),
        'Accepted salary': random.randint(48000, 155000),
        'Currency': 'USD'
    })

# Generate pipeline data
pipeline_data = []
job_states = ['Sourcing', 'Interview', 'Offer', 'Reference Check']

for i in range(30):
    pipeline_data.append({
        'Position Created Date': datetime.now() - timedelta(days=random.randint(1, 90)),
        'Hiring Manager': f'Manager {random.randint(1, 10)}',
        'TA Partner': random.choice(ta_partners),
        'Sourcing Partner': random.choice(ta_partners),
        'Country': random.choice(countries),
        'Project': random.choice(projects),
        'Role': random.choice(roles),
        'Job State': random.choice(job_states),
        'Number of CVs shared': random.randint(5, 50),
        'Number of 1st interviews': random.randint(0, 15),
        'Number of offers': random.randint(0, 3),
        'Max budgeted salary': random.randint(50000, 150000),
        'Currency': 'USD'
    })

# Create Excel file
with pd.ExcelWriter('sample_recruitment_data.xlsx', engine='openpyxl') as writer:
    pd.DataFrame(hired_data).to_excel(writer, sheet_name='Hired', index=False)
    pd.DataFrame(pipeline_data).to_excel(writer, sheet_name='Final', index=False)

print("[+] Sample data file created: sample_recruitment_data.xlsx")
'''
    
    # Save and run the sample data script
    with open("create_sample.py", "w", encoding='utf-8') as f:
        f.write(sample_script)
    
    success = run_command(f"conda run -n {env_name} python create_sample.py", "Creating sample data")
    
    # Clean up
    if os.path.exists("create_sample.py"):
        os.remove("create_sample.py")
    
    return success

def main():
    """Main setup function"""
    print("RECRUITMENT DASHBOARD - ANACONDA SETUP")
    print("=" * 50)
    
    # Check Anaconda installation
    if not check_anaconda():
        print("\n[-] Anaconda not found!")
        print("Please make sure Anaconda is installed and added to PATH")
        print("Restart VS Code after installing Anaconda")
        input("Press Enter to exit...")
        return
    
    # Create environment
    env_name = create_environment()
    if not env_name:
        print("[-] Failed to create environment")
        input("Press Enter to exit...")
        return
    
    # Install packages
    if not install_packages(env_name):
        print("[-] Failed to install packages")
        input("Press Enter to exit...")
        return
    
    # Test installation
    test_installation(env_name)
    
    # Create VS Code settings
    create_vscode_settings(env_name)
    
    # Create activation scripts
    create_activation_script(env_name)
    
    # Create project structure
    create_project_structure()
    
    # Create sample data
    create_sample_data(env_name)
    
    print("\n" + "=" * 50)
    print("[+] SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    
    print(f"\nNEXT STEPS:")
    print(f"1. In VS Code, press Ctrl+Shift+P")
    print(f"2. Type 'Python: Select Interpreter'")
    print(f"3. Choose the '{env_name}' environment")
    print(f"4. Or run: activate_env.bat")
    print(f"5. Then run: python app.py")
    print(f"6. Open browser: http://localhost:5000")
    
    print(f"\nUSEFUL COMMANDS:")
    print(f"  conda activate {env_name}     - Activate environment")
    print(f"  conda deactivate              - Deactivate environment")
    print(f"  python app.py                 - Start dashboard")
    
    print(f"\nTROUBLESHOoting:")
    print(f"- If VS Code doesn't see the environment, restart VS Code")
    print(f"- Use activate_env.bat to manually activate the environment")
    print(f"- Check VS Code Python interpreter in bottom-left corner")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()