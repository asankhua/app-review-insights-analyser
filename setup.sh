#!/bin/bash

# INDMoney Review Insights - CLI Setup Script

echo "🚀 Setting up INDMoney Review Insights..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/reports data/drafts data/deliveries data/logs data/cache

# Install Python dependencies for CLI
echo "📦 Installing CLI dependencies..."
pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "📋 Usage:"
echo "  python3 main.py --phase [scrape|analyze|generate|email|status]"
echo "  python3 main.py --phase all"
echo ""
echo "📁 CLI Implementation: Moved to cli/ folder"
echo "📊 Configure .env file with your API keys"

# Set up environment variables
echo "⚙️ Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "📝 Please update .env file with your API keys and email settings"
fi

echo "🎯 Next steps:"
echo "1. Update .env file with your API keys:"
echo "   - GROQ_API_KEY: For theme analysis"
echo "   - GEMINI_API_KEY: For weekly note generation"
echo "   - EMAIL_SENDER: Your Gmail address"
echo "   - EMAIL_PASSWORD: Gmail App Password"
echo ""
echo "2. Start the services:"
echo "   - CLI: python3 main.py --phase status"
echo "   - WebUI API Server: cd cliwebui && python3 api_server.py"
echo "   - WebUI Frontend: cd cliwebui && npm run dev"
echo ""
echo "3. Access the WebUI at: http://localhost:3000"
echo "4. API available at: http://localhost:8000"
