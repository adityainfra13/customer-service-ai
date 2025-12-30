"""
Intent Detection Module
Uses Claude AI to classify customer emails into categories
"""

import anthropic
import os
import json
from dotenv import load_dotenv
from typing import Dict

# Load environment variables
load_dotenv()

class IntentDetector:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.categories = [
            "ORDER_TRACKING",
            "RETURN_REFUND",
            "PRODUCT_QUESTION",
            "WARRANTY",
            "TECHNICAL_SUPPORT",
            "COMPLAINT",
            "MULTIPLE",
            "OTHER"
        ]
    
    def detect_intent(self, email_text: str) -> Dict:
        """
        Classify email into intent category using Claude
        
        Args:
            email_text: Cleaned email text
            
        Returns:
            Dict with category and confidence score
        """
        
        prompt = f"""You are an email classifier for Harmony Music Store, a musical instrument retailer.

Your job is to classify customer emails into ONE category:

Categories:
- ORDER_TRACKING: Questions about order status, shipping, delivery
- RETURN_REFUND: Return requests, refund inquiries, exchanges
- PRODUCT_QUESTION: Questions about products, features, recommendations
- WARRANTY: Warranty claims, coverage questions
- TECHNICAL_SUPPORT: Help with using products, troubleshooting
- COMPLAINT: Complaints about service, product quality, delays
- MULTIPLE: Email contains multiple different questions/issues
- OTHER: Does not fit any category above

Email to classify:
{email_text}

Respond ONLY with valid JSON in this exact format:
{{
  "category": "CATEGORY_NAME",
  "confidence": 0.95,
  "reasoning": "Brief explanation of why this category was chosen"
}}"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract response
            response_text = message.content[0].text.strip()
            
            # Parse JSON response
            result = json.loads(response_text)
            
            return {
                "category": result.get("category", "OTHER"),
                "confidence": result.get("confidence", 0.0),
                "reasoning": result.get("reasoning", "")
            }
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response was: {response_text}")
            return {
                "category": "OTHER",
                "confidence": 0.0,
                "reasoning": "Failed to parse response"
            }
        except Exception as e:
            print(f"Error detecting intent: {e}")
            return {
                "category": "OTHER",
                "confidence": 0.0,
                "reasoning": f"Error: {str(e)}"
            }


def main():
    """Test intent detection with sample emails"""
    
    # Load test emails
    with open('../data/test_emails.json', 'r') as f:
        data = json.load(f)
    
    detector = IntentDetector()
    
    print("="*70)
    print("INTENT DETECTION TEST")
    print("="*70)
    
    correct = 0
    total = 0
    
    for email in data['test_emails']:
        print(f"\n📧 Email #{email['id']}: {email['subject']}")
        print(f"Body: {email['body'][:60]}...")
        print(f"Expected: {email['expected_category']}")
        
        # Detect intent
        result = detector.detect_intent(email['body'])
        
        print(f"Detected: {result['category']} (confidence: {result['confidence']:.2f})")
        print(f"Reasoning: {result['reasoning']}")
        
        # Check accuracy
        if result['category'] == email['expected_category']:
            print("✅ CORRECT")
            correct += 1
        else:
            print("❌ INCORRECT")
        
        total += 1
        print("-"*70)
    
    # Show accuracy
    accuracy = (correct / total) * 100
    print(f"\n📊 Accuracy: {correct}/{total} ({accuracy:.1f}%)")


if __name__ == "__main__":
    main()