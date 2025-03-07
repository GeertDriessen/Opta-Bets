import subprocess
import sys
import pandas as pd

def run_script(script_name, description):
    """Run a Python script and capture its output
    
    Args:
        script_name: Name of the script to run
        description: Description of the script for logging
        
    Returns:
        bool: True if script executed successfully, False otherwise
    """
    print(f"\n{'='*80}")
    print(f"Running {description}...")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run([sys.executable, script_name], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors/Warnings:")
            print(result.stderr)
        if result.returncode != 0:
            print(f"Error running {script_name}. Return code: {result.returncode}")
            return False
        return True
    except Exception as e:
        print(f"Exception running {script_name}: {e}")
        return False

def verify_data(filename):
    """Verify that the CSV file exists and contains data
    
    Args:
        filename: Path to the CSV file to verify
        
    Returns:
        bool: True if file exists and contains data, False otherwise
    """
    try:
        df = pd.read_csv(filename)
        if len(df) > 0:
            print(f"\nSuccessfully verified {filename} - contains {len(df)} rows")
            return True
        else:
            print(f"\nWarning: {filename} is empty")
            return False
    except Exception as e:
        print(f"\nError verifying {filename}: {e}")
        return False