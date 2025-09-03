from core.work_assistant import WorkAssistant
from core.llm_client import LLMClient
from core.session_manager import SessionManager
from unittest.mock import MagicMock, call


def test_plan_sequence_persistence(tmp_path):
    state_file = tmp_path / 'state.json'
    sm = SessionManager(str(state_file))
    llm = LLMClient()
    llm.plan = MagicMock(side_effect=["Step 1: gather materials", "Step 2: test rocket"])
    assistant = WorkAssistant(llm_client=llm, session_manager=sm)
    assistant._handle_user_input('plan Build rocket')
    assistant._handle_user_input('plan')
    expected = ['plan Build rocket', 'Step 1: gather materials', 'Step 2: test rocket']
    assert sm.data['conversation_history'] == expected
    sm2 = SessionManager(str(state_file))
    assert sm2.data['conversation_history'] == expected
    llm.plan.assert_has_calls([call('Build rocket', []), call('Build rocket', ['Step 1: gather materials'])])


def test_llm_plan_prompt_includes_history():
    llm = LLMClient()
    llm.generate_text = MagicMock(return_value='Next step')
    llm.plan('Build rocket', ['Step 1', 'Step 2'])
    prompt = llm.generate_text.call_args[0][0]
    assert 'Step 1' in prompt and 'Step 2' in prompt
