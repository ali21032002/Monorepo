#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to build documentation in multiple formats:
- HTML static files (in site/)
- PDF file (documentation.pdf)
"""
import os
import subprocess
import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"[*] {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def main():
    """Build documentation in all formats"""
    root = Path(__file__).parent
    
    print("[*] Building Mentora Documentation")
    print(f"Working directory: {root}")
    
    # Build HTML static files
    success = run_command(
        "python -m mkdocs build",
        "Building HTML static files"
    )
    
    if not success:
        print("\n[!] Failed to build documentation")
        sys.exit(1)
    
    # Summary
    print(f"\n{'='*60}")
    print("[*] Documentation Build Summary")
    print(f"{'='*60}")
    
    site_dir = root / "site"
    if site_dir.exists():
        index_file = site_dir / "index.html"
        print(f"[+] HTML files: {site_dir}")
        print(f"   Main file: {index_file}")
        print(f"   Open index.html in your browser to view")
        print(f"\n[*] To create PDF:")
        print(f"   1. Open {index_file} in your browser")
        print(f"   2. Press Ctrl+P (or File > Print)")
        print(f"   3. Choose 'Save as PDF' as destination")
        print(f"   4. Save the PDF file")
    
    print("\n[*] Documentation build complete!")
    print("\nTo serve documentation locally:")
    print("  python -m mkdocs serve")

if __name__ == "__main__":
    main()

