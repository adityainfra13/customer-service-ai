"""
Test the complete workflow with RAG: 
Intent Detection → RAG Search → Draft Generation → Quality Check → Routing
"""

import json
from email_processor import preprocess_email
from intent_detector import IntentDetector
from rag_system import RAGSystem
from draft_generator import DraftGenerator
from quality_checker import QualityChecker


def main():
    # Load test data from JSON file
    with open('../data/test_emails.json', 'r') as f:
        emails = json.load(f)['test_emails']
    
    # Initialize all systems
    detector = IntentDetector()
    rag = RAGSystem()
    generator = DraftGenerator()
    checker = QualityChecker()
    
    print("="*70)
    print("COMPLETE AI AUTOMATION WORKFLOW TEST")
    print("="*70)
    
    # Statistics
    total_processed = 0
    auto_send_count = 0
    human_review_count = 0
    escalate_count = 0
    
    # Test with emails (change range as needed: [:3], [6:10], or all)
    for test_email in emails[6:10]:  # Testing emails 7-10
        print(f"\n{'='*70}")
        print(f"📧 EMAIL #{test_email['id']}: {test_email['subject']}")
        print(f"{'='*70}")
        
        # Display FULL customer email
        print(f"\n📩 FULL CUSTOMER EMAIL:")
        print(f"   Subject: {test_email['subject']}")
        print(f"   Body:")
        print(f"   {'-'*66}")
        # Indent each line of the body
        for line in test_email['body'].split('\n'):
            print(f"   {line}")
        print(f"   {'-'*66}")
        
        # Step 1: Preprocess
        print(f"\n1️⃣  PREPROCESSING:")
        preprocessed = preprocess_email(test_email)
        print(f"   Order Numbers: {preprocessed['order_numbers']}")
        print(f"   Urgency: {preprocessed['urgency_level']}")
        print(f"   Text Length: {preprocessed['length']} characters")
        
        # Step 2: Detect Intent
        print(f"\n2️⃣  INTENT DETECTION:")
        intent_result = detector.detect_intent(test_email['body'])
        print(f"   Category: {intent_result['category']}")
        print(f"   Confidence: {intent_result['confidence']:.2f}")
        print(f"   Reasoning: {intent_result['reasoning'][:100]}...")
        
        # Step 3: RAG Search (adjust top_k based on complexity)
        print(f"\n3️⃣  RAG SEARCH:")
        
        # Dynamic top_k based on email complexity (if field exists)
        if test_email.get('complexity') == 'complex':
            top_k = 5
        elif intent_result['category'] == 'MULTIPLE':
            top_k = 5
        else:
            top_k = 3
        
        relevant_faqs = rag.search_relevant_faqs(
            customer_question=test_email['body'],
            category=intent_result['category'],
            top_k=top_k
        )
        print(f"   Found {len(relevant_faqs)} relevant FAQs (requested top_{top_k}):")
        for i, faq in enumerate(relevant_faqs, 1):
            score = faq.get('relevance_score', 'N/A')
            print(f"   {i}. [ID: {faq['id']}] {faq['question']}")
            print(f"      Relevance: {score}")
            if faq.get('relevance_reason'):
                print(f"      Reason: {faq['relevance_reason']}")
        
        # Step 4: Generate Draft
        print(f"\n4️⃣  DRAFT GENERATION:")
        draft_result = generator.generate_draft(test_email['body'], relevant_faqs)
        
        # Display FULL draft message
        print(f"\n   📝 FULL DRAFT EMAIL:")
        print(f"   {'='*66}")
        # Indent each line of the draft
        for line in draft_result['draft'].split('\n'):
            print(f"   {line}")
        print(f"   {'='*66}")
        
        print(f"\n   Draft Metadata:")
        print(f"   - Confidence: {draft_result['confidence']:.2f}")
        print(f"   - Needs Human: {draft_result['needs_human']}")
        print(f"   - Snippets Used: {draft_result['snippets_used']}")
        print(f"   - Persona: {draft_result['persona']}")
        
        # Step 5: Quality Check
        print(f"\n5️⃣  QUALITY CHECK:")
        quality_result = checker.check_quality(
            test_email['body'],
            draft_result['draft'],
            relevant_faqs
        )
        print(f"   Quality Score: {quality_result['quality_score']:.2f}")
        print(f"   Is Safe: {quality_result['is_safe']}")
        print(f"   Needs Human: {quality_result['needs_human_review']}")
        
        if quality_result.get('breakdown'):
            print(f"\n   Quality Breakdown:")
            for metric, score in quality_result['breakdown'].items():
                print(f"   - {metric}: {score:.2f}")
        
        if quality_result.get('issues') and len(quality_result['issues']) > 0:
            print(f"\n   ⚠️  Issues Found:")
            for issue in quality_result['issues']:
                print(f"   - {issue}")
        
        # Step 6: Final Routing Decision
        print(f"\n6️⃣  ROUTING DECISION:")
        needs_human = draft_result['needs_human'] or quality_result['needs_human_review']
        final_confidence = min(draft_result['confidence'], quality_result['quality_score'])
        is_urgent = preprocessed['urgency_level'] == "HIGH"
        
        # Decision matrix with priority order
        if not quality_result['is_safe']:
            action = "🚨 ESCALATE_TO_HUMAN"
            reason = "Safety concern detected"
            escalate_count += 1
        elif is_urgent:
            action = "🚨 ESCALATE_TO_HUMAN (HIGH URGENCY)"
            reason = f"Customer urgency: {preprocessed['urgency_level']} (overrides quality metrics)"
            escalate_count += 1
        elif needs_human:
            action = "👤 HUMAN_REVIEW_WITH_DRAFT"
            reason = "Draft or QC flagged for review"
            human_review_count += 1
        elif final_confidence >= 0.85:
            action = "✅ AUTO_SEND"
            reason = "High confidence, safe to auto-send"
            auto_send_count += 1
        else:
            action = "👤 HUMAN_REVIEW_WITH_DRAFT"
            reason = f"Confidence too low ({final_confidence:.2f})"
            human_review_count += 1
        
        print(f"\n   Decision Factors:")
        print(f"   - Urgency Level: {preprocessed['urgency_level']}")
        print(f"   - Draft Needs Human: {draft_result['needs_human']}")
        print(f"   - QC Needs Human: {quality_result['needs_human_review']}")
        print(f"   - Final Confidence: {final_confidence:.2f}")
        
        print(f"\n   📋 FINAL DECISION:")
        print(f"   → Action: {action}")
        print(f"   → Reason: {reason}")
        
        total_processed += 1
        print(f"\n{'='*70}\n")
    
    # Summary Statistics
    print("\n" + "="*70)
    print("✅ COMPLETE WORKFLOW TEST FINISHED")
    print("="*70)
    
    print(f"\n📊 PROCESSING STATISTICS:")
    print(f"   Total Emails: {total_processed}")
    if total_processed > 0:
        print(f"   ✅ Auto-Send: {auto_send_count} ({auto_send_count/total_processed*100:.0f}%)")
        print(f"   👤 Human Review: {human_review_count} ({human_review_count/total_processed*100:.0f}%)")
        print(f"   🚨 Escalate: {escalate_count} ({escalate_count/total_processed*100:.0f}%)")
    
    print("\n💡 YOUR AI AUTOMATION SYSTEM INCLUDES:")
    print("  1. Email preprocessing (order extraction, urgency detection)")
    print("  2. Intent classification (AI-powered categorization)")
    print("  3. RAG search (intelligent knowledge base retrieval)")
    print("  4. Draft generation (persona-based responses)")
    print("  5. Quality control (safety & accuracy verification)")
    print("  6. Smart routing (auto-send vs human review)")
    
    print("\n🎯 DECISION PRIORITY:")
    print("  1. Safety concerns → Always escalate")
    print("  2. High urgency → Always escalate (even if draft is good)")
    print("  3. Needs human flag → Review with draft")
    print("  4. High confidence (≥0.85) → Auto-send")
    print("  5. Medium confidence → Review with draft")


if __name__ == "__main__":
    main()