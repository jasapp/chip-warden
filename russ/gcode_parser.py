"""
G-code Parser for Chip Warden
Extracts metadata from G-code files posted by Fusion 360
"""

import re
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GCodeMetadata:
    """Parsed metadata from Chip Warden header in G-code"""
    project: str
    part: str
    posted_timestamp: str
    operations: int
    tool_count: int
    machine: str
    setup: str
    program_number: Optional[str] = None

    @property
    def posted_datetime(self) -> Optional[datetime]:
        """Convert posted timestamp to datetime object"""
        try:
            return datetime.strptime(self.posted_timestamp, "%Y-%m-%d-%H%M")
        except (ValueError, AttributeError):
            return None

    @property
    def version_filename(self) -> str:
        """Generate versioned filename"""
        # Sanitize part name for filesystem
        safe_part = re.sub(r'[^\w\-]', '_', self.part)
        return f"{safe_part}_{self.posted_timestamp}.nc"

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging/storage"""
        return {
            'project': self.project,
            'part': self.part,
            'posted': self.posted_timestamp,
            'operations': self.operations,
            'tool_count': self.tool_count,
            'machine': self.machine,
            'setup': self.setup,
            'program_number': self.program_number
        }


class GCodeParser:
    """Parse G-code files and extract Chip Warden metadata"""

    METADATA_START = "CHIP-WARDEN-START"
    METADATA_END = "CHIP-WARDEN-END"

    def __init__(self):
        self.metadata_pattern = re.compile(r'\(([^)]+)\)')

    def parse_file(self, filepath: str) -> Optional[GCodeMetadata]:
        """
        Parse G-code file and extract Chip Warden metadata

        Args:
            filepath: Path to .nc or .gcode file

        Returns:
            GCodeMetadata object or None if metadata not found
        """
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return self.parse_content(f.read())
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return None

    def parse_content(self, content: str) -> Optional[GCodeMetadata]:
        """
        Parse G-code content string and extract metadata

        Args:
            content: G-code file content as string

        Returns:
            GCodeMetadata object or None if metadata not found
        """
        lines = content.split('\n')

        # Find metadata block
        in_metadata = False
        metadata = {}
        program_number = None

        for line in lines:
            line = line.strip()

            # Extract program number (O1001 format)
            if line.startswith('O') and program_number is None:
                match = re.match(r'O(\d+)', line)
                if match:
                    program_number = match.group(1)

            # Check for metadata markers
            if self.METADATA_START in line:
                in_metadata = True
                continue
            elif self.METADATA_END in line:
                break

            # Parse metadata lines
            if in_metadata:
                # Extract comment content
                match = self.metadata_pattern.search(line)
                if match:
                    comment = match.group(1)

                    # Parse key: value format
                    if ':' in comment:
                        key, value = comment.split(':', 1)
                        key = key.strip().lower().replace('-', '_')
                        value = value.strip()
                        metadata[key] = value

        # Validate we have minimum required fields
        required_fields = ['project', 'part', 'posted']
        if not all(field in metadata for field in required_fields):
            return None

        # Build metadata object
        try:
            return GCodeMetadata(
                project=metadata.get('project', 'unknown'),
                part=metadata.get('part', 'unknown'),
                posted_timestamp=metadata.get('posted', ''),
                operations=int(metadata.get('operations', 0)),
                tool_count=int(metadata.get('tool_count', 0)),
                machine=metadata.get('machine', 'unknown'),
                setup=metadata.get('setup', 'unknown'),
                program_number=program_number
            )
        except (ValueError, KeyError) as e:
            print(f"Error parsing metadata: {e}")
            return None

    def compare_metadata(self, old: GCodeMetadata, new: GCodeMetadata) -> Dict[str, any]:
        """
        Compare two metadata objects and identify changes

        Args:
            old: Previous version metadata
            new: New version metadata

        Returns:
            Dictionary of changes with warnings
        """
        changes = {
            'has_changes': False,
            'warnings': [],
            'changes': {}
        }

        # Check for significant changes
        if old.tool_count != new.tool_count:
            changes['has_changes'] = True
            changes['changes']['tool_count'] = {
                'old': old.tool_count,
                'new': new.tool_count
            }
            diff = abs(new.tool_count - old.tool_count)
            if diff >= 2:
                changes['warnings'].append(
                    f"⚠️ Tool count changed significantly: {old.tool_count} → {new.tool_count}"
                )

        if old.operations != new.operations:
            changes['has_changes'] = True
            changes['changes']['operations'] = {
                'old': old.operations,
                'new': new.operations
            }
            changes['warnings'].append(
                f"ℹ️ Operation count changed: {old.operations} → {new.operations}"
            )

        if old.machine != new.machine:
            changes['has_changes'] = True
            changes['changes']['machine'] = {
                'old': old.machine,
                'new': new.machine
            }
            changes['warnings'].append(
                f"⚠️ MACHINE CHANGED: {old.machine} → {new.machine} - Verify correct machine!"
            )

        if old.setup != new.setup:
            changes['has_changes'] = True
            changes['changes']['setup'] = {
                'old': old.setup,
                'new': new.setup
            }

        return changes


if __name__ == "__main__":
    # Test parser
    test_gcode = """
%
O1001 (HYDRAULIC MANIFOLD)
(CHIP-WARDEN-START)
(PROJECT: HYDRAULIC MANIFOLD)
(PART: 1001)
(POSTED: 2025-10-30-1445)
(OPERATIONS: 3)
(TOOL-COUNT: 5)
(MACHINE: PUMA)
(SETUP: OP1-ROUGH-FACE)
(CHIP-WARDEN-END)

G28 U0 W0
"""

    parser = GCodeParser()
    metadata = parser.parse_content(test_gcode)

    if metadata:
        print("✅ Parsed metadata:")
        print(f"  Project: {metadata.project}")
        print(f"  Part: {metadata.part}")
        print(f"  Posted: {metadata.posted_timestamp}")
        print(f"  Operations: {metadata.operations}")
        print(f"  Tools: {metadata.tool_count}")
        print(f"  Machine: {metadata.machine}")
        print(f"  Setup: {metadata.setup}")
        print(f"  Program #: {metadata.program_number}")
        print(f"  Filename: {metadata.version_filename}")
    else:
        print("❌ Failed to parse metadata")
