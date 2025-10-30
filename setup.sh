#!/bin/bash
# Chip Warden Setup Script
# Run this on your RPI or Linux box to install Russ

set -e  # Exit on error

echo "🔧 Chip Warden Setup"
echo "===================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "❌ Python 3 not found"; exit 1; }

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "russ" ]; then
    echo "❌ Please run this script from the chip-warden directory"
    exit 1
fi

# Create virtual environment
echo ""
echo "📦 Creating Python virtual environment..."
if [ -d "venv" ]; then
    echo "   venv already exists, skipping..."
else
    python3 -m venv venv
    echo "   ✅ Created venv"
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "   ✅ Dependencies installed"

# Create config from example
echo ""
echo "⚙️  Setting up configuration..."
if [ -f "russ/config/config.yml" ]; then
    echo "   config.yml already exists, skipping..."
else
    cp russ/config/config.example.yml russ/config/config.yml
    echo "   ✅ Created config.yml from example"
    echo "   ⚠️  IMPORTANT: Edit russ/config/config.yml with your paths!"
fi

# Create directories
echo ""
echo "📁 Creating directories..."
mkdir -p russ/logs
mkdir -p parts-archive
echo "   ✅ Directories created"

# Make russ.py executable
chmod +x russ/russ.py

# Test imports
echo ""
echo "🧪 Testing Python imports..."
python3 -c "from russ.gcode_parser import GCodeParser; from russ.file_manager import FileManager; print('✅ Imports OK')" || {
    echo "❌ Import test failed"
    exit 1
}

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit russ/config/config.yml with your directory paths"
echo "2. Set up Telegram bot:"
echo "   - Message @BotFather on Telegram to create a bot"
echo "   - Save the token to: russ/config/telegram.token"
echo "   - Set your chat ID in config.yml"
echo "3. Test Russ: ./venv/bin/python3 russ/russ.py --config russ/config/config.yml"
echo "4. Set up systemd service (optional - for auto-start on boot)"
echo ""
echo "In Russ we trust. 🤖"
