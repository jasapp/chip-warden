# Fusion 360 Post Processor Modifications

## Overview

To enable Chip Warden (Russ) to properly identify and organize your G-code files, we need to modify your Fusion 360 post processors to inject metadata into the G-code output.

## What Gets Added

The modified post will add a metadata block at the start of every G-code file:

```gcode
(CHIP-WARDEN-START)
(PROJECT: hydraulic-manifold)
(PART: main-body-v3)
(DESIGN-FILE: hydraulic-manifold.f3d)
(SETUP: OP1-face-and-bore)
(POSTED: 2025-10-30-1445)
(TOOL-COUNT: 5)
(CHIP-WARDEN-END)
O1001
G54 G90 G20
... rest of program
```

## What Russ Does With This

- **PROJECT** - Top-level organization in git repo
- **PART** - Individual part within project (for assemblies)
- **DESIGN-FILE** - Original Fusion design filename
- **SETUP** - Which operation (OP1, OP2, etc.)
- **POSTED** - Timestamp for tracking
- **TOOL-COUNT** - Quick reference

## Modification Instructions

### Step 1: Locate Your Post Processor

**Windows:**
```
%appdata%\Autodesk\Fusion 360 CAM\Posts\
```

**Mac:**
```
~/Library/Application Support/Autodesk/Fusion 360 CAM/Posts/
```

Your post files have `.cps` extension (e.g., `fanuc.cps`, `haas.cps`)

### Step 2: Backup Original

Copy your post file:
```
fanuc.cps  →  fanuc-original.cps
```

### Step 3: Add Metadata Function

Add this function near the top of your `.cps` file (after the header comments, before `onOpen()`):

```javascript
function writeChipWardenMetadata() {
  // Get design and document info
  var projectName = "unknown-project";
  var partName = "unknown-part";
  var designFile = "unknown.f3d";

  // Try to extract from program name or comment
  if (programName) {
    partName = programName;
  }

  if (programComment) {
    projectName = programComment;
  }

  // Get current timestamp
  var now = new Date();
  var timestamp = now.getFullYear() + "-" +
                  String(now.getMonth() + 1).padStart(2, '0') + "-" +
                  String(now.getDate()).padStart(2, '0') + "-" +
                  String(now.getHours()).padStart(2, '0') +
                  String(now.getMinutes()).padStart(2, '0');

  // Count tools
  var toolCount = getNumberOfSections();

  // Write metadata block
  writeComment("CHIP-WARDEN-START");
  writeComment("PROJECT: " + projectName);
  writeComment("PART: " + partName);
  writeComment("DESIGN-FILE: " + designFile);

  if (hasParameter("operation-comment")) {
    writeComment("SETUP: " + getParameter("operation-comment"));
  }

  writeComment("POSTED: " + timestamp);
  writeComment("TOOL-COUNT: " + toolCount);
  writeComment("CHIP-WARDEN-END");
  writeln("");
}
```

### Step 4: Call Function in onOpen()

Find the `onOpen()` function in your post processor and add the metadata writer right after the header:

```javascript
function onOpen() {
  // ... existing header code ...

  writeProgramHeader();  // or whatever your post does for header

  // Add this line:
  writeChipWardenMetadata();

  // ... rest of onOpen code ...
}
```

### Step 5: Test

1. Post a simple program from Fusion
2. Open the generated .nc file
3. Verify the metadata block appears at the top
4. Check that program runs correctly on your CNC (the comments should be ignored)

## Advanced: Using Fusion Properties

If you want Russ to access more detailed information, you can set custom properties in Fusion:

**In Fusion 360:**
1. Go to your design
2. Right-click design name → Properties
3. Add custom properties:
   - `project-name`
   - `part-number`
   - `revision`

**In post processor**, access these with:
```javascript
if (hasParameter("document-property-project-name")) {
  projectName = getParameter("document-property-project-name");
}
```

## Multiple Machines

If you have different posts for different machines (e.g., `haas.cps`, `mazak.cps`), add the same modifications to each post processor.

You can also add a machine identifier:
```javascript
writeComment("MACHINE: haas-vf2");
```

## Questions?

Drop them in the GitHub issues or modify as needed. Russ is flexible and can parse whatever format you prefer.

---

*Russ approves this message.*
