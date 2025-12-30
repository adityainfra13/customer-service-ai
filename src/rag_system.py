"""
RAG System - Retrieval Augmented Generation
Searches knowledge base and retrieves relevant information using AI ranking
"""

import json
import anthropic
import os
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()


class RAGSystem:
    def __init__(self, faq_file='../data/faqs.json'):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Load FAQ database
        with open(faq_file, 'r') as f:
            data = json.load(f)
            self.faqs = data['faqs']
        
        print(f"✅ Loaded {len(self.faqs)} FAQs from knowledge base")
    
    def search_relevant_faqs(self, customer_question: str, category: str = None, top_k: int = 3) -> List[Dict]:
        """
        Find the most relevant FAQs for a customer question
        Uses Claude to rank relevance
        
        Args:
            customer_question: The customer's question
            category: Optional category filter (e.g., "ORDER_TRACKING")
            top_k: Number of FAQs to return
            
        Returns:
            List of most relevant FAQs with relevance scores
        """
        
        # Filter by category if provided
        if category and category not in ["OTHER", "MULTIPLE"]:
            candidate_faqs = [faq for faq in self.faqs if faq['category'] == category]
        else:
            candidate_faqs = self.faqs
        
        # If we have very few FAQs, return them all
        if len(candidate_faqs) <= top_k:
            return candidate_faqs
        
        # Build the ranking prompt
        faq_list = "\n".join([
            f"{i+1}. [ID: {faq['id']}] Q: {faq['question']}"
            for i, faq in enumerate(candidate_faqs)
        ])
        
        prompt = f"""You are a relevance ranking system for a customer support knowledge base.

Your task: Rank which FAQs are most relevant to answer the customer's question.

CUSTOMER QUESTION:
{customer_question}

AVAILABLE FAQs:
{faq_list}

INSTRUCTIONS:
1. Analyze the customer's question and identify what they're asking about
2. Compare each FAQ to see which ones would help answer their question
3. Rank the top {top_k} most relevant FAQs

Consider:
- Exact topic match (e.g., if they ask about shipping, prioritize shipping FAQs)
- Semantic similarity (similar concepts even if different words)
- Completeness (does the FAQ fully answer their question?)
- Specificity (specific FAQs are better than generic ones)

Return ONLY a JSON array (NO markdown, NO code fences) with the top {top_k} FAQ IDs ranked by relevance:
{{{{
  "ranked_faqs": [
    {{{{"id": 1, "relevance_score": 0.95, "reason": "Directly answers the question"}}}}
    {{{{"id": 3, "relevance_score": 0.80, "reason": "Provides related information"}}}},
    {{{{"id": 7, "relevance_score": 0.60, "reason": "Tangentially relevant"}}}}
  ]
}}}}

Now rank the FAQs:"""

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
            
            # Parse JSON response
            result = json.loads(response_text)
            ranked_ids = result.get('ranked_faqs', [])
            
            # Retrieve the full FAQ objects
            relevant_faqs = []
            for ranked in ranked_ids[:top_k]:
                faq_id = ranked['id']
                faq = next((f for f in candidate_faqs if f['id'] == faq_id), None)
                if faq:
                    # Add relevance metadata
                    faq_with_score = faq.copy()
                    faq_with_score['relevance_score'] = ranked.get('relevance_score', 0.5)
                    faq_with_score['relevance_reason'] = ranked.get('reason', '')
                    relevant_faqs.append(faq_with_score)
            
            return relevant_faqs
            
        except Exception as e:
            print(f"Error in RAG search: {e}")
            print(f"Falling back to simple category-based retrieval")
            # Fallback: return first N FAQs from category
            return candidate_faqs[:top_k]
    
    def search_multi_category(self, customer_question: str, top_k: int = 5) -> List[Dict]:
        """
        Search across ALL categories (for MULTIPLE or OTHER intent)
        
        Args:
            customer_question: The customer's question
            top_k: Number of FAQs to return
            
        Returns:
            List of most relevant FAQs from all categories
        """
        return self.search_relevant_faqs(customer_question, category=None, top_k=top_k)


def main():
    """Test RAG system"""
    
    rag = RAGSystem()
    
    # Test cases
    test_questions = [
        {
            "question": "Where is my order #45823? I ordered it last week.",
            "category": "ORDER_TRACKING"
        },
        {
            "question": "The guitar I received has a crack in the neck. I want to return it.",
            "category": "RETURN_REFUND"
        },
        {
            "question": "Does the Fender Stratocaster come with a case?",
            "category": "PRODUCT_QUESTION"
        },
        {
            "question": "My amplifier is making buzzing noises. Is this covered under warranty?",
            "category": "WARRANTY"
        }
    ]
    
    print("="*70)
    print("RAG SYSTEM TEST")
    print("="*70)
    
    for i, test in enumerate(test_questions, 1):
        print(f"\n📧 Test Question {i}:")
        print(f"Q: {test['question']}")
        print(f"Category: {test['category']}\n")
        
        # Search for relevant FAQs
        results = rag.search_relevant_faqs(
            customer_question=test['question'],
            category=test['category'],
            top_k=3
        )
        
        print(f"Found {len(results)} relevant FAQs:")
        print("-"*70)
        
        for j, faq in enumerate(results, 1):
            print(f"{j}. [ID: {faq['id']}] {faq['question']}")
            if 'relevance_score' in faq:
                print(f"   Relevance: {faq['relevance_score']:.2f}")
                print(f"   Reason: {faq['relevance_reason']}")
            print(f"   Answer: {faq['answer'][:100]}...")
            print()
        
        print("="*70)


if __name__ == "__main__":
    main()