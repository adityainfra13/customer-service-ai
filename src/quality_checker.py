"""
Quality Checker - Evaluates draft replies
Implements your advanced quality control prompt
"""

import anthropic
import os
import json
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()


class QualityChecker:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.threshold = 0.85  # Minimum score for auto-send
    
    def check_quality(self, customer_message: str, draft_reply: str, 
                     knowledge_snippets: List[Dict]) -> Dict:
        """
        Evaluate draft quality using AI
        
        Returns quality score, safety check, and review recommendation
        """
        
        snippets_text = self._format_snippets(knowledge_snippets)
        
        prompt = f"""SYSTEM:
You are an AI quality-control assistant that evaluates email replies written by another AI.

Your job:
1) Check accuracy against the provided knowledge snippets
2) Check if the reply follows voice and style rules
3) Check if the reply avoids hallucinations and unsafe statements
4) Check if the draft itself requests human escalation

You MUST respond in valid JSON only, no extra text.

EVALUATION CRITERIA:
- Accuracy (40%): Does the reply stay consistent with the knowledge snippets?
- Completeness (25%): Does it answer the customer's main question(s)?
- Voice and tone (20%): Does it sound warm, reassuring, and confident?
- Policy adherence (15%): Any contradictions with policy? Any promises we can't guarantee?

JSON FORMAT (respond with ONLY raw JSON, NO markdown, NO code fences):
{{{{
  "quality_score": 0.92,
  "is_safe": true,
  "needs_human_review": false,
  "issues": ["list of problems found, empty if none"],
  "suggested_edits": "revised version if needed, empty string if not needed",
  "breakdown": {{{{
    "accuracy": 0.95,
    "completeness": 0.90,
    "voice_tone": 0.92,
    "policy_adherence": 0.90
  }}}}
}}}}

CRITICAL RULES:
- If the reply contradicts or goes beyond the snippets → "is_safe": false and "needs_human_review": true
- If important parts of the question are not answered → "needs_human_review": true
- If "quality_score" < 0.85 → "needs_human_review": true
- If the draft contains ANY escalation phrases, set "needs_human_review": true:
  * "I'll need to look into"
  * "have our team check"
  * "pass this to"
  * "forward this to"
  * "our team will"
  * "look into this for you"
  * "have someone reach out"
  * "specialist will contact"
  
- Voice should be: Warm, reassuring, expert, simple language. No overpromising.

IMPORTANT: Even if the email is well-written (high quality score), if it mentions needing human follow-up, 
you MUST set "needs_human_review": true because the email itself is requesting escalation.

---

CUSTOMER_MESSAGE:
{customer_message}

DRAFT_REPLY:
{draft_reply}

KNOWLEDGE_SNIPPETS:
{snippets_text}

Now evaluate and return JSON:"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text.strip()
            
            # Remove markdown code fences if present
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                response_text = '\n'.join(lines).strip()
            
            result = json.loads(response_text)
            
            # Add routing decision
            result['action'] = self._determine_action(result)
            
            return result
            
        except Exception as e:
            print(f"Error in quality check: {e}")
            return {
                "quality_score": 0.0,
                "is_safe": False,
                "needs_human_review": True,
                "issues": [f"Quality check failed: {str(e)}"],
                "action": "ESCALATE_TO_HUMAN"
            }
    
    def _determine_action(self, quality_result: Dict) -> str:
        """Determine routing action based on quality score"""
        score = quality_result.get('quality_score', 0)
        is_safe = quality_result.get('is_safe', False)
        needs_human = quality_result.get('needs_human_review', True)
        
        if not is_safe or needs_human:
            return "ESCALATE_TO_HUMAN"
        elif score >= self.threshold:
            return "AUTO_SEND"
        elif score >= 0.70:
            return "HUMAN_REVIEW_WITH_DRAFT"
        else:
            return "ESCALATE_TO_HUMAN"
    
    def _format_snippets(self, snippets: List[Dict]) -> str:
        """Format snippets for prompt"""
        if not snippets:
            return "No snippets provided."
        
        formatted = []
        for i, snippet in enumerate(snippets, 1):
            formatted.append(f"[{i}] {snippet.get('question', 'N/A')}: {snippet.get('answer', 'N/A')}")
        
        return "\n".join(formatted)


def main():
    """Test quality checking"""
    
    # Sample data
    customer_message = "Where is my order #45823? I ordered it last week."
    
    draft_reply = """Hi there!

I'd be happy to help you track your order. You can check the status using the tracking number that was sent to your email. Just visit harmoneymusic.com/track and enter your order #45823.

Typically, orders arrive within 3-5 business days from the ship date. If you're not seeing tracking info in your email, please let me know and I'll look into it for you!

Best,
Norman"""

    knowledge_snippets = [
        {
            "id": 1,
            "question": "Where is my order?",
            "answer": "You can track your order using the tracking number sent to your email. Visit harmoneymusic.com/track. Orders typically arrive within 3-5 business days."
        }
    ]
    
    checker = QualityChecker()
    
    print("="*70)
    print("QUALITY CHECK TEST")
    print("="*70)
    
    result = checker.check_quality(customer_message, draft_reply, knowledge_snippets)
    
    print(f"\n📊 Quality Score: {result['quality_score']:.2f}")
    print(f"✅ Safe: {result['is_safe']}")
    print(f"👤 Needs Human: {result['needs_human_review']}")
    print(f"🎬 Action: {result['action']}")
    
    if result.get('breakdown'):
        print(f"\n📈 Breakdown:")
        for metric, score in result['breakdown'].items():
            print(f"  {metric}: {score:.2f}")
    
    if result.get('issues'):
        print(f"\n⚠️  Issues Found:")
        for issue in result['issues']:
            print(f"  - {issue}")
    
    if result.get('suggested_edits'):
        print(f"\n✏️  Suggested Edits:")
        print(result['suggested_edits'])


if __name__ == "__main__":
    main()