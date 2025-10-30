# Chip Warden

**Powered by Russ** - Your G-code guardian angel

## The Problem

Running a machine shop means dealing with G-code files constantly. Post from Fusion 360, transfer to CNC, hope you grabbed the right version. One mistake = scrapped parts and wasted time.

**Chip Warden solves this:**
- Never overwrite files accidentally
- Always know which program is the latest
- Full version history in git
- Clean FTP directories (no more hunting through dozens of old files)
- Telegram notifications when new programs are ready
- Smart G-code analysis and change tracking

## How It Works

### Workflow

1. **Fusion 360 Posts** → Samba share on your network
2. **Russ (the agent) processes it:**
   - Parses G-code for part info (extracted from post processor comments)
   - Commits to git with full version history
   - Copies to FTP directory with clear naming
   - Sends you a Telegram notification
   - Cleans up after you've grabbed the file
3. **You grab it from CNC controller** - always the right file
4. **Russ cleans up the FTP directory** - stays clean and obvious

### Architecture

```
┌─────────────┐
│ Fusion 360  │
└──────┬──────┘
       │ posts NC file
       v
┌─────────────────────┐
│  Samba Share        │
│  /fusion-output/    │
└──────┬──────────────┘
       │
       v
┌─────────────────────────────────┐
│  Russ (Python Agent)            │
│  - Parse G-code metadata        │
│  - Git commit (version history) │
│  - Smart file naming            │
│  - Telegram notifications       │
│  - FTP cleanup                  │
└──────┬──────────────────────────┘
       │
       v
┌─────────────────────┐
│  FTP Directory      │
│  (CNC Access)       │
└─────────────────────┘
```

## Components

### 1. Russ Agent (Python)
- File watcher monitoring Samba share
- G-code parser
- Git integration
- Telegram bot integration
- FTP management

### 2. Modified Fusion 360 Post Processors
Enhanced posts inject metadata into G-code:
```gcode
(CHIP-WARDEN-START)
(PROJECT: hydraulic-manifold)
(PART: main-body-v3)
(POSTED: 2025-10-30-1445)
(SETUP: OP1-face-and-bore)
(CHIP-WARDEN-END)
```

### 3. Git Repository Structure
```
parts/
  hydraulic-manifold/
    main-body/
      main-body_v1_2025-10-30-0830.nc
      main-body_v2_2025-10-30-1445.nc
      CHANGELOG.md
  bearing-housing/
    ...
```

## Future Enhancements

- Claude API integration for G-code analysis
  - "What changed in this version?"
  - "Feed rate dropped 30% - intentional?"
  - Tool wear pattern detection
- Notion database logging
- Material usage tracking
- Cycle time estimation vs actual
- Quality checkpoint tracking

## Named After

Russ - lead machinist from the 90s who always knew which program was which and never scrapped a part.

---

*In Russ we trust.*
