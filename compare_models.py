#!/usr/bin/env python3
"""
Compare analysis quality between models
"""

import os
import time
from pathlib import Path
from assistant import WorkAssistant
from dotenv import load_dotenv

load_dotenv()

def clear_caches():
    """Clear all cache files"""
    for cache_file in [".cache.json", "analysis_cache.json", "session_state.json"]:
        if Path(cache_file).exists():
            Path(cache_file).unlink()

def test_model_analysis(model_name):
    """Get full analysis from a model"""
    print(f"\n{'='*80}")
    print(f"🧪 TESTING {model_name.upper()}")
    print(f"{'='*80}")
    
    clear_caches()
    os.environ['OLLAMA_MODEL'] = model_name
    
    start_time = time.time()
    
    try:
        assistant = WorkAssistant()
        print(f"📥 Fetching tickets...")
        assistant.current_tickets = assistant.jira.get_my_tickets()
        
        print(f"⏱️  Running analysis with {len(assistant.current_tickets)} tickets...")
        analysis = assistant.llm.analyze_workload(assistant.current_tickets)
        
        duration = time.time() - start_time
        
        print(f"⚡ Duration: {duration:.1f}s")
        print(f"🎯 Top Priority: {analysis.top_priority.key if analysis.top_priority else 'None'}")
        print(f"📊 Length: {len(analysis.summary)} chars")
        
        print(f"\n{'🔍 FULL ANALYSIS OUTPUT:':<50}")
        print(f"{'─'*80}")
        print(analysis.summary)
        print(f"{'─'*80}")
        
        return {
            'model': model_name,
            'duration': duration,
            'top_priority': analysis.top_priority.key if analysis.top_priority else None,
            'analysis': analysis.summary,
            'length': len(analysis.summary)
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    models_to_compare = ['llama3.2:3b', 'phi3:3.8b']
    results = []
    
    print("🏆 MODEL ANALYSIS COMPARISON")
    print("Testing fastest models for analysis quality vs speed")
    
    for model in models_to_compare:
        result = test_model_analysis(model)
        if result:
            results.append(result)
    
    # Summary comparison
    print(f"\n{'='*80}")
    print("📊 SUMMARY COMPARISON")
    print(f"{'='*80}")
    
    for result in results:
        print(f"\n🤖 {result['model']}")
        print(f"   Speed: {result['duration']:.1f}s")
        print(f"   Top Priority: {result['top_priority']}")
        print(f"   Detail Level: {result['length']} chars")
    
    if len(results) >= 2:
        speed_diff = results[1]['duration'] / results[0]['duration']
        detail_diff = results[1]['length'] / results[0]['length']
        
        print(f"\n🏁 WINNER ANALYSIS:")
        faster_model = results[0]['model'] if results[0]['duration'] < results[1]['duration'] else results[1]['model']
        more_detailed = results[0]['model'] if results[0]['length'] > results[1]['length'] else results[1]['model']
        
        print(f"   Faster: {faster_model}")
        print(f"   More Detailed: {more_detailed}")
        print(f"   Speed Difference: {abs(speed_diff-1)*100:.1f}%")
        print(f"   Detail Difference: {abs(detail_diff-1)*100:.1f}%")

if __name__ == "__main__":
    main()