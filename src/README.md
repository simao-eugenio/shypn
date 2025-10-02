# src/
This folder contains all source code for the project. Only the `shypn` package inside this folder should contain Python modules and subpackages. All other code folders have been moved inside `src/shypn/` for a clean architecture.

## Running the UI during WSL development

If you are developing on Windows + WSL (WSLg) and encounter display/backend issues when using Conda, create a small virtualenv that uses the system site packages and run the UI with system Python. Example:

```bash
python3 -m venv ../venv/shypnenv --system-site-packages
. ../venv/shypnenv/bin/activate
/usr/bin/python3 ../src/shypn.py
```

This ensures the running Python uses the system Gtk/GI stack (which is compatible with WSLg) while keeping your Conda environment intact for other work.