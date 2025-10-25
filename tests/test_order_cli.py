from typer.testing import CliRunner
from order.cli import app
import tempfile
import os
from datetime import datetime
from unittest.mock import patch

def test_add_task():
    runner = CliRunner()
    result = runner.invoke(app, ["add", "test"])
    
    assert result.exit_code == 0
    assert "Task added" in result.stdout

def test_add_task_creates_markdown():
    with tempfile.TemporaryDirectory() as temp_dir:
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            runner = CliRunner()
            result = runner.invoke(app, ["add", "test markdown task"])

            assert result.exit_code == 0
            assert os.path.exists("dev-notes.md")

            with open("dev-notes.md", "r") as f:
                    content = f.read()
                    today = datetime.now().strftime("%Y-%m-%d")

                    assert f"## {today}" in content
                    assert "### Todo" in content
                    assert "- [ ] test markdown task" in content

        finally:
            os.chdir(original_dir)

def test_note_command_creates_markdown():
    with tempfile.TemporaryDirectory() as temp_dir:
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            runner = CliRunner()
            result = runner.invoke(app, ["note", "debugging email service "])

            assert result.exit_code == 0
            assert os.path.exists("dev-notes.md")

            with open("dev-notes.md", "r") as f:
                    content = f.read()
                    today = datetime.now().strftime("%Y-%m-%d")

                    assert f"## {today}" in content
                    assert "### Notes" in content
                    assert "debugging email service" in content

        finally:
            os.chdir(original_dir)

def test_idea_command_creates_markdown():
    with tempfile.TemporaryDirectory() as temp_dir:
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            runner = CliRunner()
            result = runner.invoke(app, ["idea", "Consider caching"])

            assert result.exit_code == 0
            assert os.path.exists("dev-notes.md")

            with open("dev-notes.md", "r") as f:
                content = f.read()
                today = datetime.now().strftime("%Y-%m-%d")

                assert f"## {today}" in content
                assert "### Ideas" in content
                assert "Consider caching" in content

        finally:
            os.chdir(original_dir)

def test_list_command_displays_markdown_content():
    test_content = """# Dev Notes

## 2025-10-23
### Todo
- [ ] Test task
- [ ] Another task

### Notes
- Some context note
"""

    with patch('order.cli.MarkdownHandler') as mock_handler:
        from order.markdown_handler import MarkdownResult
        mock_handler.return_value.read_file.return_value = MarkdownResult(success=True, content=test_content)
        
        runner = CliRunner()
        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "Test task" in result.stdout
        assert "Another task" in result.stdout
        assert "Some context note" in result.stdout

def test_done_command_marks_task_complete():
    with tempfile.TemporaryDirectory() as temp_dir:
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            with open("dev-notes.md", "w") as f:
                f.write("""# Dev Notes

## 2025-10-23
### Todo
- [ ] Test task to complete
- [ ] Another task
""")

            runner = CliRunner()
            result = runner.invoke(app, ["done", "Test task"])

            assert result.exit_code == 0
            assert "marked as complete" in result.stdout.lower()
        
            with open("dev-notes.md", "r") as f:
                content = f.read()

                assert "- [x] Test task to complete" in content
                assert "- [ ] Another task" in content

        finally:
            os.chdir(original_dir)
 
def test_today_command_shows_only_current_day():
    with tempfile.TemporaryDirectory() as temp_dir:
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            with open("dev-notes.md", "w") as f:
                today = datetime.now().strftime("%Y-%m-%d") 
                f.write(f"""# Dev Notes

## 2025-10-20
### Todo
- [ ] Old task

## {today}
### Todo
- [ ] Today's task
### Notes
- Today's note

## 2025-10-26
### Todo
- [ ] Future task
""")

            runner = CliRunner()
            result = runner.invoke(app, ["today"])

            assert result.exit_code == 0
            assert "Today's task" in result.stdout
            assert "Today's note" in result.stdout
            assert "Old task" not in result.stdout
            assert "Future task" not in result.stdout

        finally:
            os.chdir(original_dir)

def test_search_command_finds_content():
    with tempfile.TemporaryDirectory() as temp_dir:
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            with open("dev-notes.md", "w") as f:
                f.write("""# Dev Notes

## 2025-10-20
### Todo
- [ ] Fix authentication bug
- [ ] Update documentation

## 2025-10-23
### Notes
- Working on email service debugging
- Database connection issues

### Ideas
- Consider redis caching
""")

            runner = CliRunner()
            result = runner.invoke(app, ["search", "email"])

            assert result.exit_code == 0
            assert "email service debugging" in result.stdout
            assert "authentication bug" not in result.stdout
            assert "Redis caching" not in result.stdout

        finally:
            os.chdir(original_dir)

def test_poetry_script_entry_point_exists():
    """Test that the poetry script entry point is configured"""
    import subprocess
    import sys

    try:
        result = subprocess.run([sys.executable, "-c", "import order.cli; print('success')"],
            capture_output=True, text=True, timeout=5)

        assert result.returncode == 0
        assert "success" in result.stdout

    except subprocess.TimeoutExpired:
        pytest.fail("Import test timed out")

def test_delete_command_removes_task():
    """Test that delete command removes a task by partial text match"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Create file with tasks
            with open("dev-notes.md", "w") as f:
                f.write("""# Dev Notes

## 2025-10-24
### Todo
- [ ] Task to delete
- [ ] Task to keep
""")

            runner = CliRunner()
            result = runner.invoke(app, ["delete", "Task to delete"])

            assert result.exit_code == 0
            assert "deleted" in result.stdout.lower()
            
            # Verify task was removed
            with open("dev-notes.md", "r") as f:
                content = f.read()
                assert "Task to delete" not in content
                assert "Task to keep" in content

        finally:
            os.chdir(original_dir)

def test_smart_file_discovery_finds_existing_file():
    """Test that CLI finds existing dev-notes.md in parent directories"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create dev-notes.md in root
        root_notes = os.path.join(temp_dir, "dev-notes.md")
        with open(root_notes, "w") as f:
            f.write("# Dev Notes\n\n## 2025-10-24\n### Todo\n- [ ] Existing task\n")
        
        # Create subdirectory and run command from there
        subdir = os.path.join(temp_dir, "src", "components")
        os.makedirs(subdir)
        
        original_dir = os.getcwd()
        os.chdir(subdir)
        
        try:
            runner = CliRunner()
            result = runner.invoke(app, ["add", "New task from subdir"])
            
            assert result.exit_code == 0
            
            # Should have updated the root file, not created new one
            assert os.path.exists(root_notes)
            assert not os.path.exists(os.path.join(subdir, "dev-notes.md"))
            
            with open(root_notes, "r") as f:
                content = f.read()
                assert "Existing task" in content
                assert "New task from subdir" in content
                
        finally:
            os.chdir(original_dir)

def test_configuration_system_respects_custom_file_path():
    """Test that CLI respects custom dev-notes.md path from environment variable"""
    with tempfile.TemporaryDirectory() as temp_dir:
        custom_notes = os.path.join(temp_dir, "my-custom-notes.md")

        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            os.environ["ORDER_NOTES_FILE"] = custom_notes

            runner = CliRunner()
            result = runner.invoke(app, ["add", "Custom file task"])

            assert result.exit_code == 0
            
            # Should create the custom file, not dev-notes.md
            assert os.path.exists(custom_notes)
            assert not os.path.exists("dev-notes.md")
            
            with open(custom_notes, "r") as f:
                content = f.read()
                assert "Custom file task" in content

        finally:
            os.chdir(original_dir)
            if "ORDER_NOTES_FILE" in os.environ:
                del os.environ["ORDER_NOTES_FILE"]
