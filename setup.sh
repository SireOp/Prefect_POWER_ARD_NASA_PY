#!/bin/bash
set -e  # Exit on any error

# 1. Create a Python virtual environment in .venv
python3 -m venv .venv  || { echo "Failed to create virtual environment"; exit 1; }
echo " Created Python virtual environment in $(pwd)/.venv"

# 2. (Optional) Activate the environment in this script (if sourcing)
# If the script is sourced, the following will activate .venv in the current shell.
# If the script is executed normally, this has no lasting effect, so we also print instructions.
source .venv/bin/activate 2>/dev/null || true
echo "To activate the virtual environment, run: source $(pwd)/.venv/bin/activate"

# 3. Generate requirements.txt with initial dependencies
cat > requirements.txt << 'REQ'
xarray
fsspec
pandas
# zarr (optional, remove '#' to include)
REQ
echo "Created requirements.txt with xarray, fsspec, pandas (zarr optional)"

# 4. Scaffold the project folder structure
mkdir -p src/power_data_project
mkdir -p data/input data/output
mkdir -p notebooks
echo " Created directories: src/power_data_project/, data/input/, data/output/, notebooks/"

# 5. Create placeholder files
echo "# Prefect_POWER_ARD_NASA_PY" > README.md
echo "[Choose an open-source license and paste it here]" > LICENSE
# .gitignore with common Python ignores
cat > .gitignore << 'IGNORE'
# Virtual environment
.venv/
# Python cache and compiled files
__pycache__/
*.py[cod]
*$py.class
# Jupyter Notebook checkpoints
notebooks/.ipynb_checkpoints/
# Local data outputs (avoid committing large derived data)
data/output/
IGNORE
# main Python script (with a simple placeholder implementation)
echo "def main():" > src/power_data_project/main.py
echo "    print('Hello from power_data_project')" >> src/power_data_project/main.py
echo "" >> src/power_data_project/main.py
echo "if __name__ == '__main__':" >> src/power_data_project/main.py
echo "    main()" >> src/power_data_project/main.py
# Create an empty __init__.py to mark the package (optional but recommended)
touch src/power_data_project/__init__.py
echo "Created placeholder files: README.md, LICENSE, .gitignore, src/power_data_project/main.py (and __init__.py)"

# 6. Echo instruction for auto-activation in future sessions
echo "To enable auto-activation in new terminals, add this line to your ~/.bashrc or ~/.zshrc:"
echo "source $(pwd)/.venv/bin/activate"

# 7. Final message – if sourced, the venv is active; if executed, remind user to activate
if [[ "$-" == *i* ]] && [[ "$BASH_SOURCE" != "$0" ]]; then
    echo "✅ Setup complete. Virtual environment is now activated in this shell."
else
    echo "✅ Setup complete. (Activate the venv with 'source .venv/bin/activate' to start using it.)"
fi