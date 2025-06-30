#!/bin/bash
set -e  # Exit on any error

echo "🏭 Installing Warehouse App..."

cd $HOME

# Update and install dependencies
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y git python3-pip

# Clone repository
echo "📥 Downloading Warehouse app..."
if [ -d "warehouse" ]; then
    echo "⚠️  Warehouse directory exists, removing old version..."
    rm -rf warehouse
fi
git clone https://github.com/Danielzapirtan/warehouse.git

cd warehouse

# Handle database setup
FOLDER=/home/userland/WarehouseDB
ALT_FOLDER=.
FILENAME='db.json'

echo "🗄️  Setting up database..."
if test -f $FOLDER/$FILENAME; then
    echo "✅ Database already exists, keeping current data"
else
    echo "📋 Creating new database..."
    mkdir -p $FOLDER
    cp -a $ALT_FOLDER/$FILENAME $FOLDER
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install -r requirements.txt

# Start the application
echo "🚀 Starting Warehouse app..."
python3 app.py &>/dev/null &

# Give it a moment to start
sleep 3

echo ""
echo "✅ Installation complete!"
echo "🌐 Visit http://localhost:7860 in your browser"
echo "💡 To restart later, run: cd ~/warehouse && python3 app.py &"