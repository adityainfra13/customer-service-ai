import anthropic
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if API key is loaded
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("❌ ERROR: ANTHROPIC_API_KEY not found in .env file")
    exit(1)

print("✅ API key loaded successfully")
print(f"Key starts with: {api_key[:20]}...")

# Test Anthropic API
try:
    client = anthropic.Anthropic(api_key=api_key)
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "Say 'Setup successful!' if you can read this."}
        ]
    )
    
    print("\n✅ API Connection Test:")
    print(message.content[0].text)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
