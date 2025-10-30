# Example G-code Output with Chip Warden Metadata

## What Gets Added

When you post a program from Fusion 360 using the modified post processor, the G-code will now include a metadata header that Russ can parse.

## Example Output

```gcode
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

(post version: 44132)
(post modified: 2024-06-21)
(Machine)
(  vendor: DN Solutions / Doosan)
(  model: PUMA)
G28 U0 W0
G50 S3000
... rest of program ...
```

## Metadata Fields Explained

| Field | Source | Purpose |
|-------|--------|---------|
| `PROJECT` | Program Comment in Fusion | Top-level project organization |
| `PART` | Program Name (usually the number like 1001) | Part identifier |
| `POSTED` | Current timestamp | Version tracking |
| `OPERATIONS` | Number of CAM operations | Complexity indicator |
| `TOOL-COUNT` | Unique tools used | Quick reference for setup |
| `MACHINE` | Post processor property | Which machine this is for |
| `SETUP` | First operation comment | Which setup/OP this is |

## How Russ Uses This

1. **PROJECT** → Creates folder in git repo: `parts-archive/hydraulic-manifold/`
2. **PART** → Organizes versions: `1001_v1_2025-10-30-1445.nc`
3. **POSTED** → Timestamp for version tracking
4. **OPERATIONS & TOOL-COUNT** → Change detection (warns if tools suddenly change)
5. **MACHINE** → Can route to different FTP directories per machine
6. **SETUP** → Tracks multi-operation jobs (OP1, OP2, etc.)

## Tips for Better Metadata

### In Fusion 360

**Set Program Comment:**
- In CAM → Setup → Post Process tab
- Set "Program Comment" to your project name
- Example: "Hydraulic Manifold" or "Bearing Housing Rev B"

**Set Program Name:**
- Use your part number (1001, 2045, etc.)

**Set Operation Comments:**
- For each CAM operation, set a comment
- Example: "OP1-Rough-Face", "OP2-Finish-Bore"

This makes Russ much smarter about organizing and tracking your programs.

## Testing

After installing the modified post:

1. Post a simple program
2. Open the .nc file in a text editor
3. Verify the Chip Warden metadata block appears
4. Load on CNC to verify it still runs (comments are ignored by controller)

---

*Russ will parse this metadata automatically - no manual work required!*
