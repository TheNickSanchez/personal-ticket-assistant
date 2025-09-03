import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from assistant import WorkAssistant
from core.session_manager import SessionManager


def test_create_file_writes_content(tmp_path):
    llm = MagicMock()
    llm.generate_text.return_value = "hello world"
    assistant = WorkAssistant(jira_client=MagicMock(), llm_client=llm, session_manager=SessionManager())
    assistant.output_dir = str(tmp_path)
    with patch("assistant.Prompt.ask", return_value="greet"), \
         patch("assistant.console.print"):
        file_path = assistant._create_file("my*file?.txt")
    assert file_path.parent == tmp_path
    assert file_path.name == "my_file_.txt"
    assert file_path.read_text() == "hello world"
    llm.generate_text.assert_called_once_with("greet")
