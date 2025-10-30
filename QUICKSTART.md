# Chip Warden - Quick Start Guide

**Status:** ✅ Tested and working with real G-code files!

## What Just Happened

Your post processor now outputs Chip Warden metadata:
```gcode
(CHIP-WARDEN-START)
(PROJECT M S)
(PART 1001)
(POSTED 2025-10-29-1912)
(OPERATIONS 20)
(TOOL-COUNT 7)
(MACHINE PUMA)
(SETUP F 2)
(CHIP-WARDEN-END)
```

Russ can parse it, version it, git commit it, and manage your files automatically.

## Deploying to Your RPI

### 1. Copy to RPI

On your mill box (RPI behind the mill):

```bash
cd ~
git clone https://github.com/jasapp/chip-warden.git
cd chip-warden
```

### 2. Run Setup

```bash
./setup.sh
```

### 3. Configure Paths

Edit `russ/config/config.yml`:

```yaml
directories:
  # Where Fusion posts (your Samba share)
  fusion_output: "/path/to/samba/fusion-output"

  # Where CNCs access files (your FTP directory)
  ftp_share: "/path/to/ftp/root"

  # Archive location
  parts_archive: "/home/pi/chip-warden/parts-archive"

  logs: "/home/pi/chip-warden/russ/logs"
```

### 4. Set Up Telegram (Optional but Recommended)

**Get Bot Token:**
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send: `/newbot`
3. Name it (e.g., "Shop Warden Bot")
4. Copy the token

**Get Chat ID:**
1. Start chat with your bot
2. Send any message
3. Visit: `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Find your `chat_id` in the JSON

**Configure:**
```bash
echo "YOUR_BOT_TOKEN" > russ/config/telegram.token
```

Edit `russ/config/config.yml`:
```yaml
telegram:
  enabled: true
  chat_id: "YOUR_CHAT_ID"
  notify_on_post: true
```

### 5. Test Russ

```bash
./venv/bin/python3 russ/russ.py --config russ/config/config.yml
```

You should see:
```
🤖 Russ (Chip Warden) starting...
   Watching: /your/fusion/output
   Archive: /your/parts/archive
   FTP: /your/ftp/share
✅ Russ is running. Watching for new G-code files...
```

Test by posting a file from Fusion 360!

Press `Ctrl+C` to stop.

### 6. Enable Auto-Start (Optional)

Edit `russ/chip-warden.service`:
- Replace `YOUR_USERNAME` with your username
- Replace all `/path/to/chip-warden` with actual path

Install service:
```bash
sudo cp russ/chip-warden.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable chip-warden
sudo systemctl start chip-warden
```

Check status:
```bash
sudo systemctl status chip-warden
```

View logs:
```bash
tail -f russ/logs/russ.log
```

## The Workflow

### Before (Old Way - Causing Scrap)
1. Post from Fusion → `1001.nc`
2. File exists? Overwrite? (miss the dialog...)
3. Go to CNC, FTP directory full of old files
4. Grab wrong version
5. **Scrap part** 😡💸

### After (With Russ - No More Scrap)
1. **Post from Fusion** → Samba share
2. **Russ instantly:**
   - Parses metadata
   - Archives as `1001_v2_2025-10-30-1445.nc`
   - Commits to git with full history
   - Copies to FTP with clear version
   - Sends Telegram: "🔧 Part 1001 v2 ready!"
   - Cleans up old versions
3. **You grab from FTP** - always obvious which is newest
4. **Run part with confidence** ✅

## Telegram Commands

Once Russ is running, send these to your bot:

- `/start` - Show available commands
- `/status` - Check Russ status, file counts
- `/cleanup` - Manually trigger FTP cleanup

## Testing Locally

We've included a test script you can run on this machine:

```bash
python3 test_with_real_file.py
```

This tests the entire workflow with your `gcode/1001.nc` file in a temp directory.

## Fusion 360 Setup

Copy your modified post processor to Fusion:

**File:** `posts/doosan mill-turn fanuc.cps`

**Windows Location:**
```
%appdata%\Autodesk\Fusion 360 CAM\Posts\
```

**Mac Location:**
```
~/Library/Application Support/Autodesk/Fusion 360 CAM/Posts/
```

**In Fusion 360:**
1. CAM workspace
2. Post Process
3. Select "doosan mill-turn fanuc" (your modified post)
4. Set output to Samba share directory
5. Post!

**Tips for Better Metadata:**
- Set "Program Comment" to project name
- Set "Program Name" to part number
- Add operation comments for each setup

## Architecture

```
┌──────────────┐
│ Fusion 360   │ Posts G-code with metadata
└──────┬───────┘
       │
       v
┌──────────────────┐
│ Samba Share      │ fusion-output/
│ (watched by Russ)│
└──────┬───────────┘
       │
       v
┌────────────────────────────────┐
│ Russ (Python Agent)            │
│ • Parses metadata              │
│ • Versions files (never clash) │
│ • Git commits (full history)   │
│ • Manages FTP (clean, obvious) │
│ • Telegram notifications       │
└──────┬─────────────────────────┘
       │
       v
┌──────────────────┐
│ FTP Directory    │ Clear versioned files
│ (CNC access)     │ 1001_v2_2025-10-30-1445.nc
└──────────────────┘
```

## Troubleshooting

**Russ not starting:**
```bash
# Check Python
python3 --version

# Check dependencies
source venv/bin/activate
pip list | grep -E "watchdog|yaml|telegram"

# Check config
cat russ/config/config.yml
```

**Files not being detected:**
```bash
# Check permissions
ls -la /path/to/fusion/output

# Check Russ logs
tail -f russ/logs/russ.log

# Test parser manually
python3 -c "from russ.gcode_parser import GCodeParser; p = GCodeParser(); print(p.parse_file('your_file.nc'))"
```

**Telegram not working:**
```bash
# Verify token
cat russ/config/telegram.token

# Test connection
python3 -c "from russ.telegram_bot import load_telegram_token; print(load_telegram_token())"
```

## Next Steps

1. Deploy to RPI
2. Configure paths
3. Set up Telegram
4. Test with a real post
5. Enable auto-start
6. Never scrap another part

---

**In Russ we trust.** 🤖

*Questions? Issues? https://github.com/jasapp/chip-warden/issues*
