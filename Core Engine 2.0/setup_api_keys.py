#!/usr/bin/env python3
"""
Setup script to configure API keys for Core Engine 2.0
"""

from settings import settings

def setup_groq_key():
    """Setup Groq API key"""
    print("🔑 Setting up Groq API Key")
    print("-" * 30)
    
    current_key = settings.groq_api_key
    if current_key:
        print(f"Current key: {current_key[:10]}...{current_key[-4:]}")
        update = input("Update existing key? (y/n): ").lower().strip()
        if update != 'y':
            return
    
    new_key = input("Enter your Groq API key: ").strip()
    if new_key:
        settings.groq_api_key = new_key
        print("✅ Groq API key saved successfully!")
    else:
        print("❌ No key provided")

def setup_gemini_key():
    """Setup Gemini API key"""
    print("🔑 Setting up Gemini API Key")
    print("-" * 30)
    
    current_key = settings.gemini_api_key
    if current_key:
        print(f"Current key: {current_key[:10]}...{current_key[-4:]}")
        update = input("Update existing key? (y/n): ").lower().strip()
        if update != 'y':
            return
    
    new_key = input("Enter your Gemini API key: ").strip()
    if new_key:
        settings.gemini_api_key = new_key
        print("✅ Gemini API key saved successfully!")
    else:
        print("❌ No key provided")

def setup_openai_key():
    """Setup OpenAI API key"""
    print("🔑 Setting up OpenAI API Key")
    print("-" * 30)
    
    current_key = settings.openai_api_key
    if current_key:
        print(f"Current key: {current_key[:10]}...{current_key[-4:]}")
        update = input("Update existing key? (y/n): ").lower().strip()
        if update != 'y':
            return
    
    new_key = input("Enter your OpenAI API key: ").strip()
    if new_key:
        settings.openai_api_key = new_key
        print("✅ OpenAI API key saved successfully!")
    else:
        print("❌ No key provided")

def main():
    """Main setup function"""
    print("🚀 Core Engine 2.0 API Key Setup")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Setup Groq API Key")
        print("2. Setup Gemini API Key")
        print("3. Setup OpenAI API Key")
        print("4. View current status")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            setup_groq_key()
        elif choice == '2':
            setup_gemini_key()
        elif choice == '3':
            setup_openai_key()
        elif choice == '4':
            settings.print_status()
        elif choice == '5':
            print("👋 Setup complete!")
            break
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    main()
