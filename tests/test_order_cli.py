from typer.testing import CliRunner
from order.cli import app
import tempfile
import os
import stat
import subprocess
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

## 2025-10-28
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
            
            with open("dev-notes.md", "r") as f:
                content = f.read()
                assert "Task to delete" not in content
                assert "Task to keep" in content

        finally:
            os.chdir(original_dir)

def test_smart_file_discovery_finds_existing_file():
    """Test that CLI finds existing dev-notes.md in parent directories"""
    with tempfile.TemporaryDirectory() as temp_dir:
        root_notes = os.path.join(temp_dir, "dev-notes.md")
        with open(root_notes, "w") as f:
            f.write("# Dev Notes\n\n## 2025-10-24\n### Todo\n- [ ] Existing task\n")
        
        subdir = os.path.join(temp_dir, "src", "components")
        os.makedirs(subdir)
        
        original_dir = os.getcwd()
        os.chdir(subdir)
        
        try:
            runner = CliRunner()
            result = runner.invoke(app, ["add", "New task from subdir"])
            
            assert result.exit_code == 0
            
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
            
            assert os.path.exists(custom_notes)
            assert not os.path.exists("dev-notes.md")
            
            with open(custom_notes, "r") as f:
                content = f.read()
                assert "Custom file task" in content

        finally:
            os.chdir(original_dir)
            if "ORDER_NOTES_FILE" in os.environ:
                del os.environ["ORDER_NOTES_FILE"]

def test_all_commands_work_with_new_user_subsection_format():
    """Test that all CLI commands work with new user-subsection format"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            new_format_content = """# Dev Notes

## Project Context

*Add project-level context, goals, and background information here.*

## 2025-10-27

### alice-feature-auth (@alice)
#### Todo
- [ ] Fix login bug
- [ ] Update authentication tests

#### Notes
- Left off debugging OAuth flow

#### Ideas
- Consider Redis for session storage

### bob-main (@bob)
#### Todo
- [ ] Review Alice's PR
- [ ] Deploy to staging
"""
            
            with open("dev-notes.md", "w") as f:
                f.write(new_format_content)

            runner = CliRunner()
            
            result = runner.invoke(app, ["today"])
            assert result.exit_code == 0
            assert "alice-feature-auth" in result.stdout
            assert "Fix login bug" in result.stdout
            assert "bob-main" in result.stdout
            
            result = runner.invoke(app, ["search", "login"])
            assert result.exit_code == 0
            assert "Fix login bug" in result.stdout
            
            result = runner.invoke(app, ["done", "login bug"])
            assert result.exit_code == 0
            assert "marked as complete" in result.stdout.lower()
            
            with open("dev-notes.md", "r") as f:
                content = f.read()
                assert "- [x] Fix login bug" in content
            
            result = runner.invoke(app, ["delete", "Review Alice"])
            assert result.exit_code == 0
            assert "deleted" in result.stdout.lower()
            
            with open("dev-notes.md", "r") as f:
                content = f.read()
                assert "Review Alice's PR" not in content
                assert "Deploy to staging" in content

        finally:
            os.chdir(original_dir)

def test_add_command_with_branch_flag():
    """Test that --branch flag overrides git branch detection"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            runner = CliRunner()
            result = runner.invoke(app, ["add", "Test task", "--branch", "custom-feature"])

            assert result.exit_code == 0
            assert os.path.exists("dev-notes.md")

            with open("dev-notes.md", "r") as f:
                    content = f.read()

                    assert "custom-feature" in content
                    assert "Test task" in content

        finally:
            os.chdir(original_dir)

def test_get_today_function_returns_correct_format():
    """Test that get_today returns date in YYYY-MM-DD format"""
    from order.cli import get_today
    from datetime import datetime
    
    result = get_today()
    expected = datetime.now().strftime("%Y-%m-%d")
    
    assert result == expected
    assert len(result) == 10
    assert result.count('-') == 2

def test_carry_command_moves_task_with_history():
    with tempfile.TemporaryDirectory() as temp_dir:
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            with open("dev-notes.md", "w") as f:
                f.write("""# Dev Notes

## 2025-10-24

### testuser (@testuser)
#### Todo
- [ ] Fix login bug
- [ ] Another task
""")

            runner = CliRunner()
            result = runner.invoke(app, ["carry", "Fix login"])

            assert result.exit_code == 0
            assert "Task carried forward" in result.stdout

            with open("dev-notes.md", "r") as f:
                    content = f.read()
                    today = datetime.now().strftime("%Y-%m-%d")

                    assert f"- [ ] Fix login bug (carried from 2025-10-24)" in content
                    assert f"## {today}" in content

        finally:
            os.chdir(original_dir)

def test_install_hooks_command_creates_git_hooks():
    with tempfile.TemporaryDirectory() as temp_dir:
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            subprocess.run(["git", "init"], capture_output=True)

            runner = CliRunner()
            result = runner.invoke(app, ["install-hooks"])

            assert result.exit_code == 0
            assert "Git hooks installed successfully" in result.stdout

            hook_path = ".git/hooks/pre-commit"
            assert os.path.exists(hook_path)
            assert os.stat(hook_path).st_mode & stat.S_IEXEC

        finally:
            os.chdir(original_dir)

def test_context_command_adds_project_context_fixed():
    """Test context command adds content to project context section"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            with open("dev-notes.md", 'w') as f:
                f.write("""# Dev Notes

## Project Context

*Add project-level context, goals, and background information here.*

""")
            
            runner = CliRunner()
            result = runner.invoke(app, ["context", "Working on user authentication system"])
            
            assert result.exit_code == 0
            assert "Context added: Working on user authentication system" in result.stdout
            
            with open("dev-notes.md", 'r') as f:
                content = f.read()
                assert "Working on user authentication system" in content
                assert "## Project Context" in content
        finally:
            os.chdir(original_dir)

def test_context_show_command_displays_current_context_fixed():
    """Test context show command displays current project context"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            with open("dev-notes.md", 'w') as f:
                f.write("""# Dev Notes

## Project Context

Working on user authentication system

""")
            
            runner = CliRunner()
            result = runner.invoke(app, ["context", "show"])
            
            assert result.exit_code == 0
            assert "Working on user authentication system" in result.stdout
        finally:
            os.chdir(original_dir)

def test_help_command_shows_comprehensive_usage():
    """Test that help command shows detailed usage examples"""
    runner = CliRunner()
    result = runner.invoke(app, ["help"])
    
    assert result.exit_code == 0
    assert "Order CLI - Developer Notes & Task Management" in result.stdout
    assert "Quick Start Examples:" in result.stdout
    assert "order add" in result.stdout
    assert "order note" in result.stdout
    assert "order done" in result.stdout
    assert "Git Integration:" in result.stdout
    assert "Team Collaboration:" in result.stdout

def test_backlog_command_adds_task_to_backlog():
    """Test that backlog command adds tasks to backlog section"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            runner = CliRunner()
            result = runner.invoke(app, ["backlog", "Research new framework"])

            assert result.exit_code == 0
            assert "Backlog task added" in result.stdout

            with open("dev-notes.md", "r") as f:
                    content = f.read()

                    assert "## Backlog" in content
                    assert "- [ ] Research new framework" in content

                    lines = content.split('\n')

                    project_context_idx = next(i for i, line in enumerate(lines) if line.strip() == "## Project Context")
                    backlog_idx = next(i for i, line in enumerate(lines) if line.strip() == "## Backlog")
                    
                    assert backlog_idx > project_context_idx  # Backlog comes after Project Context

        finally:
            os.chdir(original_dir)
