# Chip Warden Installation Guide

## Prerequisites

- Linux machine (RPI or any Linux box)
- Python 3.8+
- Git
- Network access to Fusion 360 post directory (Samba share)
- FTP server running (for CNC access)

## Step 1: Clone Repository

On your Linux machine (the RPI behind the mill):

```bash
cd ~
git clone https://github.com/jasapp/chip-warden.git
cd chip-warden
```

## Step 2: Run Setup Script

```bash
./setup.sh
```

This will:
- Create Python virtual environment
- Install dependencies
- Create config.yml from template
- Set up directories

## Step 3: Configure Directories

Edit `russ/config/config.yml`:

```yaml
directories:
  # Where Fusion 360 posts files (your Samba share output directory)
  fusion_output: "/path/to/samba/fusion-output"

  # Where CNC machines access files (your FTP root)
  ftp_share: "/path/to/ftp/cnc-programs"

  # Where to store archived versions (git repo)
  parts_archive: "/home/pi/chip-warden/parts-archive"

  # Logs
  logs: "/home/pi/chip-warden/russ/logs"
```

## Step 4: Set Up Telegram Bot

### Create Bot

1. Open Telegram and message [@BotFather](https://t.me/botfather)
2. Send: `/newbot`
3. Follow prompts to name your bot (e.g., "Shop Warden Bot")
4. Copy the bot token

### Get Your Chat ID

1. Start a chat with your new bot
2. Send it any message
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find your `chat_id` in the JSON response

### Save Token

```bash
echo "YOUR_BOT_TOKEN_HERE" > russ/config/telegram.token
```

### Update Config

Edit `russ/config/config.yml`:

```yaml
telegram:
  enabled: true
  chat_id: "YOUR_CHAT_ID_HERE"
  notify_on_post: true
```

## Step 5: Install Modified Post Processor

Copy your modified post processor to Fusion 360:

**Windows:**
```
Copy: posts/doosan mill-turn fanuc.cps
To:   %appdata%\Autodesk\Fusion 360 CAM\Posts\
```

**Mac:**
```
Copy: posts/doosan mill-turn fanuc.cps
To:   ~/Library/Application Support/Autodesk/Fusion 360 CAM/Posts/
```

## Step 6: Test Russ

Start Russ manually to test:

```bash
cd ~/chip-warden
./venv/bin/python3 russ/russ.py --config russ/config/config.yml
```

You should see:
```
🤖 Russ (Chip Warden) starting...
   Watching: /path/to/fusion-output
   Archive: /path/to/parts-archive
   FTP: /path/to/ftp
✅ Russ is running. Watching for new G-code files...
```

Test by posting a file from Fusion 360. Russ should:
1. Detect the file
2. Parse metadata
3. Archive to git
4. Copy to FTP
5. Send you a Telegram message
6. Delete the original

Press `Ctrl+C` to stop.

## Step 7: Set Up Auto-Start (Optional)

To have Russ start automatically on boot:

### Edit Service File

Edit `russ/chip-warden.service` and replace:
- `YOUR_USERNAME` with your username
- `/path/to/chip-warden` with actual path (e.g., `/home/pi/chip-warden`)

### Install Service

```bash
sudo cp russ/chip-warden.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable chip-warden
sudo systemctl start chip-warden
```

### Check Status

```bash
sudo systemctl status chip-warden
```

### View Logs

```bash
tail -f russ/logs/russ.log
```

## Step 8: Configure Fusion 360 Post Output

In Fusion 360, when posting:

1. Select your modified post processor
2. Set output folder to your Samba share fusion-output directory
3. Post the program

Russ will handle the rest!

## Troubleshooting

### Russ not detecting files

- Check `fusion_output` path in config.yml
- Verify Samba share is mounted correctly
- Check file permissions

### Telegram not working

- Verify bot token in `russ/config/telegram.token`
- Check chat_id in config.yml
- Test with: `python3 -c "from russ.telegram_bot import load_telegram_token; print(load_telegram_token())"`

### Git commits failing

- Verify git is installed: `git --version`
- Check parts_archive directory permissions
- Initialize manually: `cd parts-archive && git init`

### Files not appearing in FTP

- Check `ftp_share` path in config.yml
- Verify FTP server is running
- Check directory permissions

## Daily Usage

Once set up, the workflow is:

1. **Design in Fusion 360** (set meaningful program comments!)
2. **Post to Samba share** (use modified post processor)
3. **Russ handles everything:**
   - Parses metadata
   - Archives to git
   - Copies to FTP with clear naming
   - Notifies you on Telegram
4. **Grab file from FTP on CNC controller**
5. **Run your part** (no more scrapped parts!)

## Commands

### Manual Control

Start Russ:
```bash
./venv/bin/python3 russ/russ.py
```

Process existing files:
```bash
./venv/bin/python3 russ/russ.py --process-existing
```

### Telegram Bot Commands

Send these to your bot in Telegram:

- `/start` - Show available commands
- `/status` - Check Russ status and file counts
- `/cleanup` - Manually clean up old FTP files
- `/help` - Show command list

## Updating

To update Chip Warden:

```bash
cd ~/chip-warden
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart chip-warden  # If running as service
```

---

**In Russ we trust.** 🤖
