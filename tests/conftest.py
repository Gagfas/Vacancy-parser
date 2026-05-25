import sys
import os
import tempfile
import glob
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Clean up test databases before running tests
def pytest_configure(config):
    for db_file in glob.glob('test_vacancies*.db'):
        try:
            os.remove(db_file)
        except (OSError, PermissionError):
            pass
