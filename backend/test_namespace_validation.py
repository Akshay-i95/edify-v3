"""
Test script for Namespace Validation functionality

This script demonstrates how the namespace validation works to ensure users
only access content appropriate to their assigned grade levels.
"""

from namespace_validator import namespace_validator

def test_namespace_validation():
    """Test various namespace validation scenarios"""
    
    print("=" * 60)
    print("EDIFY AI ASSISTANT - NAMESPACE VALIDATION DEMO")
    print("=" * 60)
    
    test_cases = [
        {
            'name': 'Valid Primary School Access',
            'query': 'What are Grade 3 reading strategies?',
            'namespaces': ['kb-psp'],
            'expected': True,
            'description': 'User with Primary School access asking about Grade 3'
        },
        {
            'name': 'Invalid Access - Higher Grade',
            'query': 'How do I teach Grade 7 algebra?',
            'namespaces': ['kb-psp'],
            'expected': False,
            'description': 'Primary School user asking about Grade 7 (Middle School content)'
        },
        {
            'name': 'Valid Middle School Access',
            'query': 'Grade 8 science curriculum guidelines?',
            'namespaces': ['kb-msp'],
            'expected': True,
            'description': 'Middle School user asking about Grade 8'
        },
        {
            'name': 'Multiple Namespace Access',
            'query': 'What about Grade 6 math strategies?',
            'namespaces': ['kb-psp', 'kb-msp'],
            'expected': True,
            'description': 'User with both Primary and Middle School access'
        },
        {
            'name': 'Early Childhood Valid Access',
            'query': 'How to assess nursery students?',
            'namespaces': ['kb-esp'],
            'expected': True,
            'description': 'Early School Program user asking about nursery'
        },
        {
            'name': 'Senior School Invalid Access',
            'query': 'Grade 11 chemistry lab safety?',
            'namespaces': ['kb-msp'],
            'expected': False,
            'description': 'Middle School user asking about Grade 11 (Senior School content)'
        },
        {
            'name': 'No Grade Mentioned - Always Valid',
            'query': 'What are effective teaching strategies?',
            'namespaces': ['kb-psp'],
            'expected': True,
            'description': 'General query without specific grade mention'
        },
        {
            'name': 'Edipedia Access - Generally Allowed',
            'query': 'What about Grade 7 policies?',
            'namespaces': ['edipedia-k12'],
            'expected': True,
            'description': 'Edipedia content is generally accessible regardless of grade'
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print(f"   Query: '{test['query']}'")
        print(f"   Namespaces: {test['namespaces']}")
        print(f"   Description: {test['description']}")
        
        is_valid, error_message = namespace_validator.validate_query_access(
            test['query'], test['namespaces']
        )
        
        if is_valid == test['expected']:
            print(f"   ✅ PASS - Access {'GRANTED' if is_valid else 'DENIED'}")
            passed += 1
        else:
            print(f"   ❌ FAIL - Expected {test['expected']}, got {is_valid}")
            failed += 1
            
        if error_message:
            print(f"   📝 Error Message: {error_message}")
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    # Show namespace information
    print("\n📚 AVAILABLE NAMESPACES:")
    print("\nKB Namespaces (Curriculum Content):")
    for ns in namespace_validator.get_all_kb_namespaces():
        info = namespace_validator.get_namespace_info(ns)
        if info:
            print(f"  • {ns}: {info['display_name']} ({info['age_range']})")
    
    print("\nEdipedia Namespaces (General Content):")
    for ns in namespace_validator.get_all_edipedia_namespaces():
        info = namespace_validator.get_namespace_info(ns)
        if info:
            print(f"  • {ns}: {info['display_name']}")
    
    print("\n🎓 GRADE DETECTION EXAMPLES:")
    example_queries = [
        "What about Grade 7 students?",
        "How to teach 3rd grade math?",
        "Strategies for class 10 science?",
        "Assessment for IK3 children?",  
        "Middle school curriculum guidelines?"
    ]
    
    for query in example_queries:
        detected_grades = namespace_validator._detect_grades_in_query(query)
        print(f"  • '{query}' → Detected grades: {list(detected_grades) if detected_grades else 'None'}")

if __name__ == "__main__":
    test_namespace_validation()