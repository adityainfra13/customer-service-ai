"""
Email preprocessing module
Handles cleaning and extracting key information from raw emails
"""

import re
import json
from typing import Dict, List

def extract_order_number(text: str) -> List[str]:
    """Extract order numbers from text"""
    # Matches: #12345, order #12345, order: 12345, order 12345
    patterns = [
        r'#(\d{5,})',
        r'order[:\s]+#?(\d{5,})',
        r'Order[:\s]+#?(\d{5,})'
    ]
    
    order_numbers = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        order_numbers.extend(matches)
    
    return list(set(order_numbers))


def detect_urgency(text: str) -> str:
    """Detect if email is urgent based on language"""
    urgent_keywords = [
        'urgent', 'asap', 'immediately', 'emergency',
        'angry', 'unacceptable', 'furious', 'disappointed',
        'third time', 'still waiting', 'never received'
    ]
    
    text_lower = text.lower()
    
    # Check for ALL CAPS sign of anger
    caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if len(text) > 0 else 0
    
    # Check for multiple exclamation marks
    exclamations = text.count('!!!')
    
    urgent_count = sum(1 for keyword in urgent_keywords if keyword in text_lower)
    
    if urgent_count >= 2 or caps_ratio > 0.3 or exclamations > 0:
        return "HIGH"
    elif urgent_count == 1:
        return "MEDIUM"
    else:
        return "LOW"


def preprocess_email(raw_email: Dict) -> Dict:
    """
    Clean and extract key information from email
    
    Args:
        raw_email: Dict with 'subject' and 'body' keys
        
    Returns:
        Dictionary with cleaned and extracted information
    """
    subject = raw_email.get('subject', '')
    body = raw_email.get('body', '')
    
    # Combine subject and body
    full_text = f"{subject}. {body}"
    
    # Clean text
    cleaned = re.sub(r'\s+', ' ', full_text).strip()
    
    # Extract information
    order_numbers = extract_order_number(cleaned)
    urgency = detect_urgency(cleaned)
    
    return {
        'subject': subject,
        'body': body,
        'cleaned_text': cleaned,
        'order_numbers': order_numbers,
        'urgency_level': urgency,
        'length': len(cleaned),
        'has_order_number': len(order_numbers) > 0
    }


def main():
    """Test with sample emails"""
    # Load test emails
    with open('../data/test_emails.json', 'r') as f:
        data = json.load(f)
    
    print("="*70)
    print("EMAIL PREPROCESSING TEST")
    print("="*70)
    
    for email in data['test_emails'][:5]:
        print(f"\n📧 Email #{email['id']}: {email['subject']}")
        print(f"Body: {email['body'][:80]}...")
        
        result = preprocess_email(email)
        
        print(f"✓ Order Numbers: {result['order_numbers']}")
        print(f"✓ Urgency: {result['urgency_level']}")
        print(f"✓ Length: {result['length']} characters")
        print("-"*70)


if __name__ == "__main__":
    main()