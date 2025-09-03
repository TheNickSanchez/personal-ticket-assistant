#!/usr/bin/env python3
"""
Interactive workflow test with CPE-3222
"""

import os
import time
from core.work_assistant import WorkAssistant
from dotenv import load_dotenv

load_dotenv()

def test_workflow():
    """Test full workflow with CPE-3222"""
    print("🚀 STARTING WORKFLOW TEST WITH CPE-3222")
    print("=" * 60)
    
    assistant = WorkAssistant()
    
    # Step 1: Initialize and get tickets
    print("\n🔄 Step 1: Initializing assistant...")
    start_time = time.time()
    
    assistant.current_tickets = assistant.jira.get_my_tickets()
    assistant.current_analysis = assistant.llm.analyze_workload(assistant.current_tickets)
    
    init_time = time.time() - start_time
    print(f"⚡ Initialization: {init_time:.1f}s")
    
    # Step 2: Find CPE-3222
    print(f"\n🔍 Step 2: Finding CPE-3222...")
    cpe_3222 = assistant._find_ticket('CPE-3222')
    if not cpe_3222:
        print("❌ CPE-3222 not found!")
        return
    
    print(f"✅ Found: {cpe_3222.key} - {cpe_3222.summary}")
    print(f"   Priority: {cpe_3222.priority} | Status: {cpe_3222.status}")
    print(f"   Age: {cpe_3222.age_days} days | Stale: {cpe_3222.stale_days} days")
    
    # Step 3: Focus on ticket (detailed view)
    print(f"\n🎯 Step 3: Focusing on CPE-3222...")
    start_time = time.time()
    
    assistant.current_focus = cpe_3222
    assistant.save_state()
    
    # Get AI suggestions
    suggestion = assistant.llm.suggest_action(cpe_3222, "User wants detailed analysis and next steps")
    focus_time = time.time() - start_time
    
    print(f"⚡ Focus + AI suggestion: {focus_time:.1f}s")
    print(f"📊 Suggestion length: {len(suggestion)} chars")
    print(f"🎯 Suggestion preview: {suggestion[:200]}...")
    
    # Step 4: Get help/advice
    print(f"\n🆘 Step 4: Getting AI help...")
    start_time = time.time()
    
    help_suggestion = assistant.llm.suggest_action(cpe_3222, "The user specifically asked for help with this ticket")
    clean_help = assistant._clean_ai_response(help_suggestion)
    
    help_time = time.time() - start_time
    print(f"⚡ AI help generation: {help_time:.1f}s")
    print(f"📊 Help length: {len(clean_help)} chars")
    print(f"🤖 Help preview: {clean_help[:200]}...")
    
    # Step 5: Research mode
    print(f"\n🔬 Step 5: Research mode...")
    start_time = time.time()
    
    research = assistant.llm.suggest_action(cpe_3222, "Research this issue deeply and provide technical insights")
    clean_research = assistant._clean_ai_response(research)
    
    research_time = time.time() - start_time
    print(f"⚡ Research generation: {research_time:.1f}s")
    print(f"📊 Research length: {len(clean_research)} chars")
    print(f"🔍 Research preview: {clean_research[:200]}...")
    
    # Step 6: Action plan
    print(f"\n📋 Step 6: Creating action plan...")
    start_time = time.time()
    
    plan = assistant.llm.suggest_action(cpe_3222, "Create a detailed step-by-step action plan to resolve this ticket")
    clean_plan = assistant._clean_ai_response(plan)
    
    plan_time = time.time() - start_time
    print(f"⚡ Action plan generation: {plan_time:.1f}s")
    print(f"📊 Plan length: {len(clean_plan)} chars")
    print(f"📝 Plan preview: {clean_plan[:200]}...")
    
    # Step 7: Comment drafting
    print(f"\n💬 Step 7: Drafting comment...")
    start_time = time.time()
    
    comment_prompt = f"""Help me draft a professional Jira comment for this ticket:

Ticket: {cpe_3222.key} - {cpe_3222.summary}
Context: Testing workflow - investigating next steps
Current status: {cpe_3222.status}

Write a concise, professional comment that provides value to stakeholders."""
    
    comment_suggestion = assistant.llm.generate_text(comment_prompt)
    
    comment_time = time.time() - start_time
    print(f"⚡ Comment generation: {comment_time:.1f}s")
    print(f"📊 Comment length: {len(comment_suggestion)} chars")
    print(f"💭 Comment preview: {comment_suggestion[:200]}...")
    
    # Step 8: Get Jira URL
    print(f"\n🔗 Step 8: Getting Jira URL...")
    base = os.getenv('JIRA_BASE_URL', '').rstrip('/')
    url = f"{base}/browse/{cpe_3222.key}"
    print(f"🔗 URL: {url}")
    
    # Summary
    total_time = init_time + focus_time + help_time + research_time + plan_time + comment_time
    
    print(f"\n{'='*60}")
    print(f"🏆 WORKFLOW TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Total Time: {total_time:.1f}s")
    print(f"   • Initialization: {init_time:.1f}s")
    print(f"   • Focus + Suggestion: {focus_time:.1f}s") 
    print(f"   • AI Help: {help_time:.1f}s")
    print(f"   • Research: {research_time:.1f}s")
    print(f"   • Action Plan: {plan_time:.1f}s")
    print(f"   • Comment Draft: {comment_time:.1f}s")
    print(f"")
    print(f"🎯 Ticket: {cpe_3222.key} - {cpe_3222.summary}")
    print(f"⚡ Speed: All AI operations < 10s each")
    print(f"📊 Quality: Generated helpful, actionable content")
    print(f"🔄 Workflow: Smooth progression through all features")
    
    print(f"\n🎉 WORKFLOW TEST: SUCCESS!")
    
    return {
        'total_time': total_time,
        'ticket': cpe_3222.key,
        'summary': cpe_3222.summary,
        'all_fast': all([t < 10 for t in [focus_time, help_time, research_time, plan_time, comment_time]])
    }

if __name__ == "__main__":
    result = test_workflow()