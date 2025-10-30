"""
File Manager for Chip Warden
Handles file versioning, git commits, and directory management
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime

from gcode_parser import GCodeMetadata


class FileManager:
    """Manages G-code file versioning and git repository"""

    def __init__(self, parts_archive_dir: str, ftp_dir: str):
        """
        Initialize file manager

        Args:
            parts_archive_dir: Root directory for parts git repository
            ftp_dir: Directory where CNC machines access files
        """
        self.parts_archive = Path(parts_archive_dir)
        self.ftp_dir = Path(ftp_dir)

        # Ensure directories exist
        self.parts_archive.mkdir(parents=True, exist_ok=True)
        self.ftp_dir.mkdir(parents=True, exist_ok=True)

        # Initialize git repo if needed
        self._init_git_repo()

    def _init_git_repo(self):
        """Initialize git repository in parts archive if not already initialized"""
        git_dir = self.parts_archive / ".git"
        if not git_dir.exists():
            try:
                subprocess.run(
                    ["git", "init"],
                    cwd=self.parts_archive,
                    check=True,
                    capture_output=True
                )
                print(f"✅ Initialized git repository in {self.parts_archive}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to initialize git repo: {e}")

    def get_project_dir(self, project_name: str) -> Path:
        """Get or create project directory in archive"""
        # Sanitize project name for filesystem
        safe_name = self._sanitize_filename(project_name)
        project_dir = self.parts_archive / safe_name
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    def get_part_dir(self, project_name: str, part_name: str) -> Path:
        """Get or create part directory within project"""
        project_dir = self.get_project_dir(project_name)
        safe_part = self._sanitize_filename(part_name)
        part_dir = project_dir / safe_part
        part_dir.mkdir(parents=True, exist_ok=True)
        return part_dir

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize string for use as filename/directory"""
        import re
        # Replace spaces and special chars with underscores
        safe = re.sub(r'[^\w\-]', '_', name)
        # Remove multiple underscores
        safe = re.sub(r'_+', '_', safe)
        # Remove leading/trailing underscores
        safe = safe.strip('_')
        return safe.lower()

    def get_existing_versions(self, project: str, part: str) -> List[Path]:
        """
        Get list of existing versions for a part

        Returns:
            List of file paths, sorted by modification time (newest first)
        """
        part_dir = self.get_part_dir(project, part)
        nc_files = list(part_dir.glob("*.nc"))
        # Sort by modification time, newest first
        nc_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return nc_files

    def get_next_version_number(self, project: str, part: str) -> int:
        """Get next version number for a part"""
        existing = self.get_existing_versions(project, part)
        return len(existing) + 1

    def archive_gcode(
        self,
        source_file: str,
        metadata: GCodeMetadata,
        commit: bool = True
    ) -> Tuple[Path, int]:
        """
        Archive G-code file to parts repository

        Args:
            source_file: Path to source .nc file
            metadata: Parsed metadata
            commit: Whether to git commit

        Returns:
            Tuple of (archived_file_path, version_number)
        """
        # Get destination directory
        part_dir = self.get_part_dir(metadata.project, metadata.part)

        # Get version number
        version = self.get_next_version_number(metadata.project, metadata.part)

        # Build filename with version
        safe_part = self._sanitize_filename(metadata.part)
        filename = f"{safe_part}_v{version}_{metadata.posted_timestamp}.nc"
        dest_path = part_dir / filename

        # Copy file
        shutil.copy2(source_file, dest_path)
        print(f"📦 Archived to: {dest_path}")

        # Create/update CHANGELOG
        self._update_changelog(part_dir, metadata, version)

        # Git commit
        if commit:
            self._git_commit(metadata, version, dest_path)

        return dest_path, version

    def _update_changelog(self, part_dir: Path, metadata: GCodeMetadata, version: int):
        """Update CHANGELOG.md for the part"""
        changelog_path = part_dir / "CHANGELOG.md"

        # Create header if new file
        if not changelog_path.exists():
            header = f"# {metadata.part} - Change Log\n\n"
            header += f"Project: {metadata.project}\n\n"
        else:
            header = ""

        # Read existing content
        existing_content = ""
        if changelog_path.exists():
            with open(changelog_path, 'r') as f:
                lines = f.readlines()
                # Skip header if it exists
                if lines and lines[0].startswith('#'):
                    existing_content = ''.join(lines[3:])  # Skip header lines
                else:
                    existing_content = ''.join(lines)

        # New entry
        entry = f"## Version {version} - {metadata.posted_timestamp}\n\n"
        entry += f"- **Setup:** {metadata.setup}\n"
        entry += f"- **Machine:** {metadata.machine}\n"
        entry += f"- **Operations:** {metadata.operations}\n"
        entry += f"- **Tools:** {metadata.tool_count}\n"
        entry += f"- **Posted:** {metadata.posted_datetime or metadata.posted_timestamp}\n\n"

        # Write updated changelog
        with open(changelog_path, 'w') as f:
            if header:
                f.write(header)
            f.write(entry)
            f.write(existing_content)

        print(f"📝 Updated changelog: {changelog_path}")

    def _git_commit(self, metadata: GCodeMetadata, version: int, file_path: Path):
        """Create git commit for new version"""
        try:
            # Get relative path for git
            rel_path = file_path.relative_to(self.parts_archive)
            changelog_path = file_path.parent / "CHANGELOG.md"
            rel_changelog = changelog_path.relative_to(self.parts_archive)

            # Add files
            subprocess.run(
                ["git", "add", str(rel_path), str(rel_changelog)],
                cwd=self.parts_archive,
                check=True,
                capture_output=True
            )

            # Commit message
            commit_msg = f"{metadata.part} v{version} - {metadata.setup}\n\n"
            commit_msg += f"Project: {metadata.project}\n"
            commit_msg += f"Machine: {metadata.machine}\n"
            commit_msg += f"Operations: {metadata.operations}\n"
            commit_msg += f"Tools: {metadata.tool_count}\n"
            commit_msg += f"Posted: {metadata.posted_timestamp}\n\n"
            commit_msg += "🤖 Committed by Russ (Chip Warden)"

            # Commit
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=self.parts_archive,
                check=True,
                capture_output=True
            )

            print(f"✅ Git commit created")

        except subprocess.CalledProcessError as e:
            print(f"⚠️ Git commit failed: {e}")

    def copy_to_ftp(
        self,
        source_file: Path,
        metadata: GCodeMetadata,
        version: int
    ) -> Path:
        """
        Copy file to FTP directory with clear naming

        Args:
            source_file: Path to archived file
            metadata: Metadata
            version: Version number

        Returns:
            Path to FTP file
        """
        safe_part = self._sanitize_filename(metadata.part)
        filename = f"{safe_part}_v{version}_{metadata.posted_timestamp}.nc"
        ftp_path = self.ftp_dir / filename

        shutil.copy2(source_file, ftp_path)
        print(f"📤 Copied to FTP: {ftp_path}")

        return ftp_path

    def cleanup_old_ftp_files(self, keep_count: int = 2):
        """
        Clean up old files from FTP directory

        Args:
            keep_count: How many recent files to keep per part
        """
        # Group files by part name (extract from filename)
        from collections import defaultdict
        files_by_part = defaultdict(list)

        for nc_file in self.ftp_dir.glob("*.nc"):
            # Extract part name from filename (before first underscore or version marker)
            part_key = nc_file.stem.split('_v')[0]
            files_by_part[part_key].append(nc_file)

        # Clean up old files for each part
        removed_count = 0
        for part, files in files_by_part.items():
            # Sort by modification time, newest first
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Remove old files
            for old_file in files[keep_count:]:
                old_file.unlink()
                print(f"🗑️  Removed old FTP file: {old_file.name}")
                removed_count += 1

        if removed_count > 0:
            print(f"✅ Cleaned up {removed_count} old files from FTP directory")

        return removed_count


if __name__ == "__main__":
    # Test file manager
    import tempfile

    # Create temp directories
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_dir = os.path.join(tmpdir, "archive")
        ftp_dir = os.path.join(tmpdir, "ftp")

        fm = FileManager(archive_dir, ftp_dir)

        # Create test G-code file
        test_file = os.path.join(tmpdir, "test.nc")
        with open(test_file, 'w') as f:
            f.write("G28 U0 W0\n")

        # Create test metadata
        from gcode_parser import GCodeMetadata
        metadata = GCodeMetadata(
            project="test-project",
            part="1001",
            posted_timestamp="2025-10-30-1445",
            operations=3,
            tool_count=5,
            machine="PUMA",
            setup="OP1-TEST"
        )

        # Archive file
        archived_path, version = fm.archive_gcode(test_file, metadata)
        print(f"\n✅ Test archived: {archived_path}")
        print(f"   Version: {version}")

        # Copy to FTP
        ftp_path = fm.copy_to_ftp(archived_path, metadata, version)
        print(f"✅ Test FTP copy: {ftp_path}")

        print("\n✅ File manager test complete")
