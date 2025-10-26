from typing import Optional
import re
import os
import subprocess
import getpass
from datetime import datetime

TASK_INCOMPLETE = "- [ ]"
TASK_COMPLETE = "- [x]"
DATE_FORMAT_PATTERN = r'^\d{4}-\d{2}-\d{2}$'
DATE_SECTION_PATTERN = r'## \d{4}-\d{2}-\d{2}'
VALID_SECTION_TYPES = ["Todo", "Notes", "Ideas"]

class MarkdownResult:
    def __init__(self, success: bool = True, content: Optional[str] = None, error: Optional[str] = None) -> None:
        self.success = success
        self.content = content
        self.error = error

class MarkdownHandler:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def _validate_date_format(self, date: str) -> MarkdownResult:
        """Validate date format and return error if invalid"""
        if not re.match(DATE_FORMAT_PATTERN, date):
            return MarkdownResult(success=False, error="Invalid date format. Use YYYY-MM-DD")
        
        try:
            year, month, day = map(int, date.split('-'))
            if not (1 <= month <= 12 and 1 <= day <= 31):
                return MarkdownResult(success=False, error="Invalid date format. Use YYYY-MM-DD")
        except ValueError:
            return MarkdownResult(success=False, error="Invalid date format. Use YYYY-MM-DD")
        
        return MarkdownResult(success=True)

    def _write_file_safely(self, content: str) -> MarkdownResult:
        """Write content to file with error handling"""
        try:
            with open(self.file_path, 'w') as f:
                f.write(content)
            return MarkdownResult(success=True)
        except PermissionError:
            return MarkdownResult(success=False, error="Permission denied")
        except OSError as e:
            return MarkdownResult(success=False, error=f"File system error: {str(e)}")
        except Exception as e:
            return MarkdownResult(success=False, error=f"Unexpected error: {str(e)}")

    def create_file(self) -> MarkdownResult:
        try:
            with open(self.file_path, 'w') as f:
                f.write("""# Dev Notes

## Project Context

*Add project-level context, goals, and background information here.*

""")

            return MarkdownResult(success=True)
        except PermissionError:
            return MarkdownResult(success=False, error="Permission denied")
        except OSError as e:
            return MarkdownResult(success=False, error=f"File system error: {str(e)}")
        except Exception as e:
            return MarkdownResult(success=False, error=f"Unexpected error: {str(e)}")

    def read_file(self) -> MarkdownResult:
        try:
            with open(self.file_path, 'r') as f:
                content = f.read()
            return MarkdownResult(success=True, content=content)
        except FileNotFoundError:
            return MarkdownResult(success=False, error="File not found")
        except Exception as e:
            return MarkdownResult(success=False, error=str(e))

    def parse_daily_section(self, date: str) -> MarkdownResult:
        validation_result = self._validate_date_format(date)
        if not validation_result.success:
            return validation_result
        
        result = self.read_file()
        if not result.success:
            return result
            
        lines = result.content.split('\n')
        section_lines = []
        in_target_section = False

        for line in lines:
            if line.startswith(f"## {date}"):
                in_target_section = True
                section_lines.append(line)
            elif line.startswith("## ") and in_target_section:
                break
            elif in_target_section:
                section_lines.append(line)

        return MarkdownResult(success=True, content='\n'.join(section_lines))

    def add_content_to_daily_section(self, date: str, section_type: str, content: str, branch_override: str = None) -> MarkdownResult:
        """Add content to a daily section, creating the date section if needed"""
        validation_result = self._validate_date_format(date)
        if not validation_result.success:
            return validation_result

        if not section_type or section_type not in VALID_SECTION_TYPES:
            return MarkdownResult(success=False, error=f"Invalid section type. Use: {VALID_SECTION_TYPES}")
        
        if not content.strip():
            return MarkdownResult(success=False, error="Content cannot be empty")
        
        result = self.read_file()
        if not result.success:
            return result

        if f"## {date}" not in result.content:
            return self._create_new_date_section(date, section_type, content, branch_override)
        else:
            return self._add_to_existing_date_section(date, section_type, content, branch_override)

    def mark_task_complete(self, partial_text: str) -> MarkdownResult:
        """Find and mark a task as complete based on partial text match"""
        if not partial_text.strip():
            return MarkdownResult(success=False, error="Search text cannot be empty")
        
        result = self.read_file()
        if not result.success:
            return result

        lines = result.content.split('\n')

        for i, line in enumerate(lines):
            if TASK_INCOMPLETE in line and partial_text.lower() in line.lower():
                lines[i] = line.replace(TASK_INCOMPLETE, TASK_COMPLETE)
                break

        return self._write_file_safely('\n'.join(lines))

    def get_username(self) -> str:
        """Get current username for attribute section"""
        return getpass.getuser()

    def _create_new_date_section(self, date: str, section_type: str, content: str, branch_override: str = None) -> MarkdownResult:
        """Create a new date section with user-specific subsection"""
        validation_result = self._validate_date_format(date)
        if not validation_result.success:
            return validation_result
        
        result = self.read_file()
        if not result.success:
            return result
            
        lines = result.content.split('\n')
        insert_index = 1

        for i, line in enumerate(lines):
            if line.startswith("# "):
                insert_index = i + 1
                break

        username = self.get_username()
        branch = branch_override if branch_override is not None else self.get_current_branch()
        user_section = f"{username}-{branch}" if branch else username
        
        new_section = [
            f"", 
            f"## {date}", 
            f"", 
            f"### {user_section} (@{username})", 
            f"#### {section_type}", 
            content, 
            ""
        ]

        for i, new_line in enumerate(new_section):
            lines.insert(insert_index + i, new_line)

        return self._write_file_safely('\n'.join(lines))

    def _add_to_existing_date_section(self, date: str, section_type: str, content: str, branch_override: str = None) -> MarkdownResult:
        """Add content to existing date section"""
        validation_result = self._validate_date_format(date)
        if not validation_result.success:
            return validation_result
        
        result = self.read_file()
        if not result.success:
            return result
            
        lines = result.content.split('\n')
        updated_lines = self._insert_content_into_existing_date(lines, date, section_type, content)
        
        return self._write_file_safely('\n'.join(updated_lines))

    def _insert_content_into_existing_date(self, lines: list, date: str, section_type: str, content: str) -> list:
        """Insert content into existing date section, handling section placement correctly"""
        result_lines = []
        in_target_date = False
        section_added = False

        for line in lines:
            result_lines.append(line)

            if line.startswith(f"## {date}"):
                in_target_date = True
            elif line.startswith("## ") and in_target_date and not section_added:
                result_lines.insert(-1, f"### {section_type}")
                result_lines.insert(-1, content)
                result_lines.insert(-1, "")
                section_added = True
                in_target_date = False

        if in_target_date and not section_added:
            result_lines.append(f"### {section_type}")
            result_lines.append(content)
            result_lines.append("")

        return result_lines

    def search_content(self, query: str) -> MarkdownResult:
        """Search for content in the markdown file"""
        if not query.strip():
            return MarkdownResult(success=False, error="Search query cannot be empty")
        
        result = self.read_file()
        if not result.success:
            return result

        lines = result.content.split('\n')
        matching_lines = []
        
        for line in lines:
            if query.lower() in line.lower():
                matching_lines.append(line)

        if matching_lines:
            return MarkdownResult(success=True, content='\n'.join(matching_lines))
        else:
            return MarkdownResult(success=False, error=f"No results found for '{query}'")

    def delete_task(self, partial_text: str) -> MarkdownResult:
        """Find and delete a task based on partial text match"""
        if not partial_text.strip():
            return MarkdownResult(success=False, error="Search text cannot be empty")

        result = self.read_file()
        if not result.success:
            return result

        lines = result.content.split('\n')
        task_found = False

        for i, line in enumerate(lines):
            if TASK_INCOMPLETE in line and partial_text.lower() in line.lower():
                lines.pop(i)
                task_found = True
                break

        if not task_found:
            return MarkdownResult(success=False, error=f"No task found containing '{partial_text}'")

        return self._write_file_safely('\n'.join(lines))

    def migrate_to_new_format(self) -> MarkdownResult:
        """Migrate old format to new user-subsection format"""
        result = self.read_file()

        if not result.success:
            return result

        content = result.content


        if "## Project Context" not in content:
            content = content.replace("Dev Notes", "Dev Notes\n\n## Project Context\n\n*Add project-level context, goals, and background information here*")
            
        lines = content.split('\n')
        new_lines = []

        for line in lines:
            if line.startswith("## ") and "(@" in line:
                parts = line.split(" (@")
                date_part = parts[0].replace("## ", "")
                username = parts[1].replace(")", "")

                new_lines.append(f"## {date_part}")
                new_lines.append("")
                new_lines.append(f"### {username} (@{username})")

            elif line.startswith("### ") and not line.startswith("#### "):
                section_name = line.replace("### ", "")
                new_lines.append(f"#### {section_name}")
            else:
                new_lines.append(line)

        return self._write_file_safely('\n'.join(new_lines))

    def get_current_branch(self) -> str:
        """Get current git branch name, return empty string if not in git repo"""
        try:
            result = subprocess.run(['git', 'branch', '--show-current'],
                                        capture_output=True, text=True, cwd=os.path.dirname(self.file_path))

            if result.returncode == 0:
                    return result.stdout.strip()
        
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return ""

    def _find_task_in_content(self, lines: list, partial_text: str) -> tuple:
        """Find task and its date in content lines. Returns (task_found, task_date, task_index)"""
        current_date = None
        for i, line in enumerate(lines):
            if line.startswith("## ") and re.match(DATE_SECTION_PATTERN, line):
                current_date = line.replace("## ", "")
            elif TASK_INCOMPLETE in line and partial_text.lower() in line.lower():
                return line.strip(), current_date, i
        return None, None, -1

    def _remove_task_from_lines(self, lines: list, task_index: int) -> list:
        """Remove task at given index from lines"""
        lines.pop(task_index)
        return lines

    def _create_carried_task(self, task_found: str, task_date: str) -> str:
        """Create carried task with history trail"""
        task_text = task_found.replace(TASK_INCOMPLETE, "").strip()
        return f"{TASK_INCOMPLETE} {task_text} (carried from {task_date})"

    def carry_task_forward(self, partial_text: str) -> MarkdownResult:
        """Find task, move it to today with history trail"""
        if not partial_text.strip():
            return MarkdownResult(success=False, error="Search text cannot be empty")
        
        result = self.read_file()
        if not result.success:
            return result
        
        lines = result.content.split('\n')
        task_found, task_date, task_index = self._find_task_in_content(lines, partial_text)
        
        if not task_found:
            return MarkdownResult(success=False, error=f"No task found containing '{partial_text}'")
        
        updated_lines = self._remove_task_from_lines(lines, task_index)
        write_result = self._write_file_safely('\n'.join(updated_lines))
        if not write_result.success:
            return write_result
        
        today = datetime.now().strftime("%Y-%m-%d")
        carried_task = self._create_carried_task(task_found, task_date)
        
        add_result = self.add_content_to_daily_section(today, "Todo", carried_task)
        if add_result.success:
            return MarkdownResult(success=True, content=carried_task)
        
        return add_result

    def install_git_hooks(self) -> MarkdownResult:
        """Install git hooks for automatic dev-notes.md staging"""
        try:
            # Check if we're in a git repo
            git_dir = ".git"
            if not os.path.exists(git_dir):
                return MarkdownResult(success=False, error="Not in a git repository")
            
            # Create hooks directory if it doesn't exist
            hooks_dir = os.path.join(git_dir, "hooks")
            os.makedirs(hooks_dir, exist_ok=True)
            
            # Create pre-commit hook
            hook_path = os.path.join(hooks_dir, "pre-commit")
            hook_content = """#!/bin/sh
# Auto-stage dev-notes.md if it exists
if [ -f "dev-notes.md" ]; then
    git add dev-notes.md
fi
"""
            
            with open(hook_path, 'w') as f:
                f.write(hook_content)
            
            # Make hook executable
            import stat
            os.chmod(hook_path, os.stat(hook_path).st_mode | stat.S_IEXEC)
            
            return MarkdownResult(success=True)
            
        except Exception as e:
            return MarkdownResult(success=False, error=str(e))
