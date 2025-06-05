import sys
import os

# Add the project root directory to the Python path.
# This allows pytest to find the 'src' directory for imports like 'from src.module import ...'
# os.path.dirname(__file__) gives the directory of the conftest.py file (project root)
# os.path.abspath ensures it's an absolute path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# You can also add the 'src' directory directly if you prefer imports like 'from tuck_in_terrors_sim...'
# sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), "src"))
# However, keeping 'src' in the import path (from src.tuck_in_terrors_sim...) is a common pattern.