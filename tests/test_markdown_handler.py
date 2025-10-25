import os
import pytest
import tempfile
from order.markdown_handler import MarkdownHandler

def test_create_new_markdown_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "dev-notes.md")
        handler = MarkdownHandler(file_path)

        handler.create_file()

        assert os.path.exists(file_path)
        with open(file_path, 'r') as f:
            content = f.read()
            assert "Dev Notes" in content

def test_read_existing_markdown_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "dev-notes.md")

        with open(file_path, 'w') as f:
            f.write("# Dev Notes\n\n## 2025-10-22 (@testuser)\n## Todo\n- [] Test task\n")

        handler = MarkdownHandler(file_path)
        result = handler.read_file()

        assert result.success
        assert "# Dev Notes" in result.content
        assert "Test task" in result.content

def test_parse_daily_section():
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "dev-notes.md")

        content = """# Dev Notes

## 2025-10-21 (@user1)
### Todo
- [] Old task

## 2025-10-22 (@testuser)
### Todo
- [] Today's task
### Notes
- Working on markdown parser

## 2025-10-23 (@user2)
### Todo
- [] Future task
"""

        with open(file_path, 'w') as f:
            f.write(content)

        handler = MarkdownHandler(file_path)
        result = handler.parse_daily_section("2025-10-22")

        assert result.success
        assert "Today's task" in result.content
        assert "Working on markdown parser" in result.content
        assert "Old task" not in result.content
        assert "Future task" not in result.content

def test_add_content_to_daily_section():
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "dev-notes.md")
    
        handler = MarkdownHandler(file_path)
        handler.create_file()
        handler.add_content_to_daily_section("2025-10-22", "Todo", "- [ ] Test task")    
        result = handler.read_file()

        assert result.success
        assert "## 2025-10-22" in result.content
        assert "### Todo" in result.content
        assert "- [ ] Test task" in result.content

def test_add_content_to_existing_date_section(tmp_path):
    
    """Test that content is added to the correct existing date section, not the end of the file"""
    test_file = tmp_path / "test.md"
    initial_content = """# Dev Notes

## 2025-10-23
### Todo
- [ ] Existing task

## 2025-10-22
### Todo
- [ ] Old task
"""

    test_file.write_text(initial_content)
    handler = MarkdownHandler(str(test_file))

    handler.add_content_to_daily_section("2025-10-23", "Notes", "New note content")

    result = handler.read_file()
    lines = result.content.split('\n')
    
    date_section_index = None
    for i, line in enumerate(lines):
        if line == "## 2025-10-23":
            date_section_index = i
            break

    next_date_index = None
    for i, line in enumerate(lines):
        if line == "## 2025-10-22":
            next_date_index = i
            break

    section_content = '\n'.join(lines[date_section_index:next_date_index])

    assert "New note content" in section_content

def test_add_multiple_sections_to_same_date(tmp_path):
    """Test adding different section types to the same date"""

    test_file = tmp_path / "test.md"
    test_file.write_text("# Dev Notes\n")

    handler = MarkdownHandler(str(test_file))
    handler.add_content_to_daily_section("2025-10-23", "Todo", "- [ ] Task 1")
    handler.add_content_to_daily_section("2025-10-23", "Notes", "Some context")
    handler.add_content_to_daily_section("2025-10-23", "Ideas", "Great idea") 

    result = handler.read_file()

    assert result.success
    assert "### Todo" in result.content
    assert "### Notes" in result.content
    assert "### Ideas" in result.content
    assert "Task 1" in result.content
    assert "Some context" in result.content
    assert "Great idea" in result.content

def test_add_empty_content(tmp_path):
    """Test handling of empty content"""
    test_file = tmp_path / "test.md"
    test_file.write_text("# Dev Notes\n")
    
    handler = MarkdownHandler(str(test_file))
    result = handler.add_content_to_daily_section("2025-10-23", "Todo", "")
    
    assert not result.success
    assert "Content cannot be empty" in result.error

def test_add_content_to_file_without_header(tmp_path):
    """Test adding content to file that doesn't have proper header"""
    test_file = tmp_path / "test.md"
    test_file.write_text("Some random content\n")
    
    handler = MarkdownHandler(str(test_file))
    handler.add_content_to_daily_section("2025-10-23", "Todo", "- [ ] Task")
    
    result = handler.read_file()
    
    # Should still work, adding date section at top
    assert result.success
    assert "## 2025-10-23" in result.content
    assert "### Todo" in result.content
    assert "- [ ] Task" in result.content

def test_add_content_creates_date_section_with_user_attribution():
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "dev-notes.md")
        handler = MarkdownHandler(file_path)
        handler.create_file()
        
        handler.add_content_to_daily_section("2025-10-24", "Todo", "- [ ] Test task")
        
        result = handler.read_file()
        
        assert result.success
        assert "## 2025-10-24 (@" in result.content
        assert ")" in result.content
        assert "### Todo" in result.content
        assert "- [ ] Test task" in result.content

def test_add_content_handles_permission_error(tmp_path):
    """Test handling of permission errors when file is read-only"""
    test_file = tmp_path / "readonly.md"
    test_file.write_text("# Dev Notes \n")

    import stat
    test_file.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    handler = MarkdownHandler(str(test_file))

    try:
        handler.add_content_to_daily_section("2025-10-24", "Todo", "- [ ] Test")
    except PermissionError:
        pass

def test_invalid_date_format_validation():
    """Test that invalid date formats are rejected"""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "dev-notes.md")
        handler = MarkdownHandler(file_path)
        handler.create_file()

        invalid_dates = ["2025-13-01", "25-10-24", "2025/10/24", "Oct 24 2025", "invalid"]

        for invalid_date in invalid_dates:
            result = handler.add_content_to_daily_section(invalid_date, "Todo", "- [ ] Test task")

            assert not result.success
            assert "Invalid date format" in result.error

def test_invalid_section_type_validation():
    """Test that invalid section types are rejected"""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "dev-notes.md")
        
        handler = MarkdownHandler(file_path)
        handler.create_file()

        invalid_sections = ["Tasks", "Comments", "Bugs", "Random", ""]

        for invalid_section in invalid_sections:
            result = handler.add_content_to_daily_section("2025-10-24", invalid_section, "- [ ] Test content")

            assert not result.success
            assert "Invalid section type" in result.error

def test_empty_search_query_validation():
    """Test that empty search queries are rejected"""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "dev-notes.md")
        
        handler = MarkdownHandler(file_path)
        handler.create_file()

        empty_queries = ["", "   ", "\t", "\n"]

        for empty_query in empty_queries:
            result = handler.mark_task_complete(empty_query)
            assert not result.success
            assert "Search text cannot be empty" in result.error
            
            assert not result.success
            assert "Search text cannot be empty" in result.error

def test_new_file_structure_with_project_context():
    """Test that new files are created with Project Context section"""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "dev-notes.md")

        handler = MarkdownHandler(file_path)
        
        result = handler.create_file()

        assert result.success

        content_result = handler.read_file()

        assert content_result.success

        expected_structure = """# Dev Notes

## Project Context

*Add project-level context, goals, and background information here.*

"""

        assert expected_structure in content_result.content


        
