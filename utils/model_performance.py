#!/usr/bin/env python3
"""
Model Performance Testing Script
Tests different Ollama models for workload analysis speed and quality
"""

import os
import time
import json
from pathlib import Path
from core.work_assistant import WorkAssistant
from core.llm_client import LLMClient
from dotenv import load_dotenv

load_dotenv()

# Models to test (reasoning-focused, ordered by size - smallest first)
MODELS_TO_TEST = [
    "qwen2.5:3b",           # 1.9GB - Fast general reasoning
    "llama3.2:3b",          # ~2GB - Very fast, good reasoning (downloading)
    "phi3:3.8b",            # ~2.3GB - Microsoft reasoning-focused (downloading)
    "llama2:latest",        # 3.8GB - Stable general model
    "qwen2.5:7b",           # ~4GB - Best reasoning in small size (downloading)
    "qwen3:14b"             # 9.3GB - Current heavy model (for comparison)
]

def clear_all_caches():
    """Clear all cache files"""
    cache_files = [
        ".cache.json", 
        "analysis_cache.json", 
        "session_state.json"
    ]
    
    for cache_file in cache_files:
        if Path(cache_file).exists():
            Path(cache_file).unlink()
            print(f"✅ Cleared {cache_file}")
    
    print("🧹 All caches cleared")

def test_model_performance(model_name, sample_tickets=None):
    """Test a specific model's performance"""
    print(f"\n🧪 Testing {model_name}...")
    
    # Update environment for this test
    os.environ['OLLAMA_MODEL'] = model_name
    
    try:
        # Create fresh instance
        assistant = WorkAssistant()
        
        # Use sample tickets if provided, otherwise fetch real ones
        if sample_tickets:
            assistant.current_tickets = sample_tickets
        else:
            print("📥 Fetching tickets...")
            assistant.current_tickets = assistant.jira.get_my_tickets()
        
        if not assistant.current_tickets:
            print("❌ No tickets found")
            return None
        
        # Time the analysis
        print(f"⏱️  Running analysis with {len(assistant.current_tickets)} tickets...")
        start_time = time.time()
        
        analysis = assistant.llm.analyze_workload(assistant.current_tickets)
        
        end_time = time.time()
        duration = end_time - start_time
        
        result = {
            'model': model_name,
            'duration_seconds': round(duration, 2),
            'ticket_count': len(assistant.current_tickets),
            'analysis_length': len(analysis.summary),
            'top_priority_found': analysis.top_priority is not None,
            'analysis_preview': analysis.summary[:200] + "..." if len(analysis.summary) > 200 else analysis.summary
        }
        
        print(f"✅ {model_name}: {duration:.1f}s ({len(assistant.current_tickets)} tickets)")
        print(f"   Top priority: {analysis.top_priority.key if analysis.top_priority else 'None'}")
        print(f"   Analysis length: {len(analysis.summary)} chars")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing {model_name}: {e}")
        return {
            'model': model_name,
            'error': str(e),
            'duration_seconds': None
        }

def main():
    """Run the model comparison test"""
    print("🚀 Starting Ollama Model Performance Test")
    print("=" * 60)
    
    # Clear caches first
    clear_all_caches()
    
    # Store results
    results = []
    sample_tickets = None
    
    for i, model in enumerate(MODELS_TO_TEST):
        print(f"\n📊 Test {i+1}/{len(MODELS_TO_TEST)}: {model}")
        
        # Clear cache before each test
        clear_all_caches()
        
        result = test_model_performance(model, sample_tickets)
        if result:
            results.append(result)
            
            # Use the same tickets for all tests for fairness
            if sample_tickets is None and 'error' not in result:
                # For subsequent tests, we could reuse tickets, but for now fetch fresh each time
                pass
        
        # Small delay between tests
        time.sleep(1)
    
    # Display results summary
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 60)
    
    # Sort by duration (fastest first)
    valid_results = [r for r in results if r.get('duration_seconds')]
    valid_results.sort(key=lambda x: x['duration_seconds'])
    
    for result in valid_results:
        duration = result['duration_seconds']
        model = result['model']
        print(f"⚡ {model:<20} {duration:>6.1f}s")
    
    # Show errors
    error_results = [r for r in results if 'error' in r]
    if error_results:
        print("\n❌ ERRORS:")
        for result in error_results:
            print(f"   {result['model']}: {result['error']}")
    
    # Save detailed results
    with open('model_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to model_test_results.json")
    
    # Recommendation
    if valid_results:
        fastest = valid_results[0]
        current_model = os.getenv('OLLAMA_MODEL', 'qwen3:14b')
        current_result = next((r for r in valid_results if r['model'] == current_model), None)
        
        print(f"\n🏆 RECOMMENDATION:")
        print(f"   Fastest: {fastest['model']} ({fastest['duration_seconds']}s)")
        if current_result and fastest['model'] != current_model:
            speedup = current_result['duration_seconds'] / fastest['duration_seconds']
            print(f"   Speedup vs current ({current_model}): {speedup:.1f}x faster")
        
        print(f"\n💡 To use the fastest model, update your .env:")
        print(f"   OLLAMA_MODEL={fastest['model']}")

if __name__ == "__main__":
    main()
