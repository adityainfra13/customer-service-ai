"""
Draft Generator with Persona-Based Prompts
Uses Norman persona for high-quality, brand-consistent responses
"""

import anthropic
import os
import json
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()


class DraftGenerator:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Persona configuration
        self.persona = {
            "name": "Norman",
            "role": "Master guitar luthier and customer support specialist",
            "experience": "44 years",
            "company": "Harmony Music Store",
            "tone": "Warm, reassuring, and professional"
        }
        
        # Voice and style rules
        self.voice_rules = """
- Warm, reassuring, and professional tone
- Use "I" when speaking as Norman
- Use simple, clear language
- Be concise but not cold
- Encourage the customer and remove their worries
- Never use corporate jargon or overly formal language
"""
    
    def generate_draft(self, customer_email: str, knowledge_snippets: List[Dict]) -> Dict:
        """
        Generate email draft using persona-based prompt
        
        Args:
            customer_email: The customer's message
            knowledge_snippets: Relevant FAQs/articles from knowledge base
            
        Returns:
            Dict with draft and metadata
        """
        
        # Format knowledge snippets
        snippets_text = self._format_snippets(knowledge_snippets)
        
        # Build the professional prompt
        prompt = f"""SYSTEM:
You are "{self.persona['name']}", a {self.persona['role']} at {self.persona['company']}.
You have {self.persona['experience']} of experience.

Your job is to reply to customers:
- In a friendly, calm, confident tone
- Using simple, clear language
- With high factual accuracy based ONLY on the information provided

If you don't know the answer from the provided information, say you will pass this to a human specialist instead of guessing.

VOICE & STYLE:
{self.voice_rules}

KNOWLEDGE BASE:
You have access to internal FAQs and policies below.
Use ONLY these to answer. Do not invent new policies or facts.

TASK:
Given the customer email and relevant knowledge snippets, write a complete email reply.

FORMAT:
Return ONLY a raw JSON object (NO markdown code fences, NO backticks):
{{{{
  "draft_body": "The email reply text",
  "confidence": 0.95,
  "snippets_used": ["List of snippet IDs"],
  "needs_human": false
}}}}

CRITICAL CONSISTENCY RULE:
If your draft_body mentions ANY of these phrases, you MUST set "needs_human": true:
- "pass this to our team"
- "forward this to a specialist"
- "I'll need to check"
- "look into this for you"
- "have our team check"
- "reaches out to you"

Set "needs_human" to true if:
- The answer is not clearly supported by the knowledge snippets
- The question involves order-specific details you don't have
- The customer seems very upset
- Your draft suggests forwarding or escalation

Set "confidence" based on:
- 0.90-1.0: Complete answer from FAQs, no escalation needed
- 0.70-0.89: Partial answer, might need human follow-up
- 0.50-0.69: Mostly guidance, minimal direct answer
- Below 0.50: No good answer, definite escalation

CUSTOMER MESSAGE:
{customer_email}

RELEVANT KNOWLEDGE SNIPPETS:
{snippets_text}

CONSTRAINTS:
- If customer asks about SPECIFIC order and you lack live data: set "needs_human": true, "confidence": 0.70 or lower
- If you CAN fully answer from FAQs: set "needs_human": false, "confidence": 0.85+
- NEVER mix high confidence (0.90+) with escalation phrases
- Do not invent facts not in snippets

Respond with ONLY the JSON object, no additional text:"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text.strip()
            
            # Remove markdown code fences if present
            if response_text.startswith('```'):
                # Remove opening fence (```json or ```)
                lines = response_text.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]  # Skip first line
                # Remove closing fence
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]  # Skip last line
                response_text = '\n'.join(lines).strip()
            
            # Parse JSON response
            result = json.loads(response_text)
            
            return {
                "draft": result.get("draft_body", ""),
                "confidence": result.get("confidence", 0.0),
                "snippets_used": result.get("snippets_used", []),
                "needs_human": result.get("needs_human", True),
                "persona": self.persona['name']
            }
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response was: {response_text}")
            return self._create_fallback_response(customer_email)
            
        except Exception as e:
            print(f"Error generating draft: {e}")
            return self._create_fallback_response(customer_email)
    
    def _format_snippets(self, snippets: List[Dict]) -> str:
        """Format knowledge snippets for prompt"""
        if not snippets:
            return "No relevant snippets found."
        
        formatted = []
        for i, snippet in enumerate(snippets, 1):
            formatted.append(f"""
[Snippet {i}] ID: {snippet.get('id', 'unknown')}
Category: {snippet.get('category', 'N/A')}
Q: {snippet.get('question', 'N/A')}
A: {snippet.get('answer', 'N/A')}
""")
        
        return "\n".join(formatted)
    
    def _create_fallback_response(self, customer_email: str) -> Dict:
        """Create safe fallback when generation fails"""
        return {
            "draft": f"Thank you for contacting Harmony Music Store. I want to make sure I give you the most accurate information. I'm forwarding your message to our specialist team who will respond within 24 hours.",
            "confidence": 0.0,
            "snippets_used": [],
            "needs_human": True,
            "persona": self.persona['name']
        }


def main():
    """Test draft generation"""
    
    # Load test data
    with open('../data/test_emails.json', 'r') as f:
        emails = json.load(f)['test_emails']
    
    with open('../data/faqs.json', 'r') as f:
        faqs = json.load(f)['faqs']
    
    generator = DraftGenerator()
    
    # Test with first email
    test_email = emails[0]
    
    # Get relevant FAQs (simulating RAG - we'll build this properly in Mini-Project 3)
    relevant_faqs = [faq for faq in faqs if faq['category'] == 'ORDER_TRACKING'][:2]
    
    print("="*70)
    print("DRAFT GENERATION TEST")
    print("="*70)
    print(f"\n📧 Customer Email:")
    print(f"Subject: {test_email['subject']}")
    print(f"Body: {test_email['body']}\n")
    
    print(f"📚 Using {len(relevant_faqs)} knowledge snippets\n")
    
    # Generate draft
    result = generator.generate_draft(test_email['body'], relevant_faqs)
    
    print(f"✉️  DRAFT REPLY (by {result['persona']}):")
    print("-"*70)
    print(result['draft'])
    print("-"*70)
    print(f"\n📊 Metadata:")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Needs Human Review: {result['needs_human']}")
    print(f"  Snippets Used: {result['snippets_used']}")


if __name__ == "__main__":
    main()