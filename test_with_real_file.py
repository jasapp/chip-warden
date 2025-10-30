#!/usr/bin/env python3
"""
Test Chip Warden with real 1001.nc file
"""

import sys
import os
import tempfile
from pathlib import Path

# Add russ directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'russ'))

from gcode_parser import GCodeParser
from file_manager import FileManager

def main():
    # Create temp directories for testing
    tmpdir = '/tmp/chip-warden-test'
    os.makedirs(tmpdir, exist_ok=True)

    archive_dir = f'{tmpdir}/archive'
    ftp_dir = f'{tmpdir}/ftp'

    print('🧪 Testing Chip Warden with your 1001.nc file...')
    print('='*60)
    print()

    # Initialize components
    parser = GCodeParser()
    fm = FileManager(archive_dir, ftp_dir)

    # Parse your file
    print('🔍 Parsing gcode/1001.nc...')
    metadata = parser.parse_file('gcode/1001.nc')

    if not metadata:
        print('❌ Failed to parse metadata!')
        return

    print(f'✅ Parsed metadata:')
    print(f'   Project: {metadata.project}')
    print(f'   Part: {metadata.part}')
    print(f'   Setup: {metadata.setup}')
    print(f'   Machine: {metadata.machine}')
    print(f'   Tools: {metadata.tool_count}, Operations: {metadata.operations}')
    print(f'   Posted: {metadata.posted_timestamp}')
    print()

    # Archive it
    print('📦 Archiving to git repository...')
    archived_path, version = fm.archive_gcode('gcode/1001.nc', metadata)
    print(f'✅ Archived as version {version}')
    print(f'   Path: {archived_path}')
    print()

    # Copy to FTP
    print('📤 Copying to FTP directory...')
    ftp_path = fm.copy_to_ftp(archived_path, metadata, version)
    print(f'✅ FTP file: {ftp_path.name}')
    print()

    # Show archive structure
    print('📁 Archive structure:')
    print('-'*60)
    os.system(f'tree {archive_dir} 2>/dev/null || find {archive_dir} -type f | sort')
    print()

    # Show FTP directory
    print('📤 FTP directory contents:')
    print('-'*60)
    os.system(f'ls -lh {ftp_dir}')
    print()

    # Check CHANGELOG
    changelog = archived_path.parent / "CHANGELOG.md"
    if changelog.exists():
        print('📝 CHANGELOG.md preview:')
        print('-'*60)
        os.system(f'head -20 {changelog}')
        print()

    # Check git log
    print('📜 Git commit history:')
    print('-'*60)
    os.system(f'cd {archive_dir} && git log --oneline -3 2>/dev/null')
    print()

    # Show detailed commit
    print('📋 Latest commit details:')
    print('-'*60)
    os.system(f'cd {archive_dir} && git log -1 2>/dev/null')
    print()

    print('='*60)
    print('✅ Test complete!')
    print()
    print(f'Test files located at: {tmpdir}')
    print(f'   Archive: {archive_dir}')
    print(f'   FTP: {ftp_dir}')
    print()
    print('This is what Russ will do every time you post a file!')
    print()


if __name__ == "__main__":
    main()
