#!/usr/bin/env python3
"""
Setup script for Reading AI project
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def main():
    print("🤖 Reading AI Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Install requirements
    if not install_requirements():
        print("\n⚠️  Installation failed. You can try installing manually:")
        print("pip install transformers torch openai python-dotenv")
        return
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. For FREE AI (no API key needed):")
    print("   python free_reading_ai.py")
    print("\n2. For OpenAI GPT (requires API key):")
    print("   - Get free credits at: https://platform.openai.com/")
    print("   - Add your API key to .env file")
    print("   - Run: python reading.py")
    
    print("\n📖 The free version includes:")
    print("   • Text summarization")
    print("   • Question answering")
    print("   • Sentiment analysis") 
    print("   • Reading statistics")
    print("   • Key phrase extraction")
    print("   • Comprehension questions")

if __name__ == "__main__":
    main()
