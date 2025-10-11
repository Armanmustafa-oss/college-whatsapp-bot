# tests/test_semantics.py
from app.services.rag_service import rag_service

test_queries = [
    ("What's the address of the main branch?", "450 University Avenue"),
    ("How much are the fees?", "8,500 EUR"),
    ("Tell me about dorms", "400 EUR"),
    ("When do classes start?", "September"),
]

def test_semantic_accuracy():
    passed = 0
    for query, expected in test_queries:
        results = rag_service.search_documents(query)
        content = " ".join([r["content"] for r in results])
        if expected.lower() in content.lower():
            print(f"✅ PASS: {query}")
            passed += 1
        else:
            print(f"❌ FAIL: {query}")
            print(f"   Expected: {expected}")
            print(f"   Got: {content[:100]}...")
    accuracy = (passed / len(test_queries)) * 100
    print(f"\n🎯 Semantic Accuracy: {accuracy:.1f}%")
    return accuracy >= 80