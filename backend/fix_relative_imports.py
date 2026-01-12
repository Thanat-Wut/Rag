#!/usr/bin/env python3
"""
Fix all relative imports to absolute imports for backend package
"""
import re
from pathlib import Path

def fix_file(filepath: Path):
    """Fix relative imports in a single file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        # Fix: from config import → from config import
        line = re.sub(r'from \.\.config import', 'from config import', line)
        
        # Fix: from models import → from models import
        line = re.sub(r'from \.\.models import', 'from models import', line)
        
        # Fix: from connectors. → from connectors.
        line = re.sub(r'from \.\.connectors\.', 'from connectors.', line)
        
        # Fix: from utils. → from utils.
        line = re.sub(r'from \.\.utils\.', 'from utils.', line)
        
        # Fix: from .decision → from brain.decision (only in brain/)
        if 'brain' in str(filepath):
            line = re.sub(r'from \.decision import', 'from brain.decision import', line)
            line = re.sub(r'from \.classifier import', 'from brain.classifier import', line)
        
        # Fix: from .way_api → from connectors.way_api (only in connectors/)
        if 'connectors' in str(filepath):
            line = re.sub(r'from \.way_api import', 'from connectors.way_api import', line)
            line = re.sub(r'from \.mock_answers import', 'from connectors.mock_answers import', line)
        
        new_lines.append(line)
    
    new_content = '\n'.join(new_lines)
    
    if new_content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Fixed: {filepath}")
        return True
    return False

def main():
    backend_dir = Path('.')
    fixed_count = 0
    
    # Fix all Python files
    for py_file in backend_dir.rglob('*.py'):
        if '__pycache__' in str(py_file) or 'venv' in str(py_file):
            continue
        
        if fix_file(py_file):
            fixed_count += 1
    
    print(f"\n✅ Total files fixed: {fixed_count}")

if __name__ == '__main__':
    main()