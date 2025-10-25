from typing import Optional
import re

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
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
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

    def create_file(self) -> MarkdownResult:
        try:
            with open(self.file_path, 'w') as f:
                f.write("# Dev Notes\n")
            return MarkdownResult(success=True)
        except Exception as e:
            return MarkdownResult(success=False, error=str(e))

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

    def add_content_to_daily_section(self, date: str, section_type: str, content: str) -> MarkdownResult:
        """Add content to a daily section, creating the date section if needed"""
        validation_result = self._validate_date_format(date)
        if not validation_result.success:
            return validation_result

        valid_sections = ["Todo", "Notes", "Ideas"]
        if not section_type or section_type not in valid_sections:
            return MarkdownResult(success=False, error=f"Invalid section type. Use: {valid_sections}")
        
        if not content.strip():
            return MarkdownResult(success=False, error="Content cannot be empty")
        
        result = self.read_file()
        if not result.success:
            return result

        if f"## {date}" not in result.content:
            return self._create_new_date_section(date, section_type, content)
        else:
            return self._add_to_existing_date_section(date, section_type, content)

    def mark_task_complete(self, partial_text: str) -> MarkdownResult:
        """Find and mark a task as complete based on partial text match"""
        if not partial_text.strip():
            return MarkdownResult(success=False, error="Search text cannot be empty")
        
        result = self.read_file()
        if not result.success:
            return result

        lines = result.content.split('\n')

        for i, line in enumerate(lines):
            if "- [ ]" in line and partial_text.lower() in line.lower():
                lines[i] = line.replace("- [ ]", "- [x]")
                break

        return self._write_file_safely('\n'.join(lines))

    def get_username(self) -> str:
        """Get current username for attribute section"""
        import getpass
        return getpass.getuser()

    def _create_new_date_section(self, date: str, section_type: str, content: str) -> MarkdownResult:
        """Create a new date section with content"""
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

        new_section = [f"", f"## {date} (@{self.get_username()})", f"### {section_type}", content, ""]

        for i, new_line in enumerate(new_section):
            lines.insert(insert_index + i, new_line)

        return self._write_file_safely('\n'.join(lines))

    def _add_to_existing_date_section(self, date: str, section_type: str, content: str) -> MarkdownResult:
        """Add content to existing date section"""
        validation_result = self._validate_date_format(date)
        if not validation_result.success:
            return validation_result
        
        result = self.read_file()
        if not result.success:
            return result
            
        lines = result.content.split('\n')
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

        return self._write_file_safely('\n'.join(result_lines))

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
            if "- [ ]" in line and partial_text.lower() in line.lower():
                lines.pop(i)
                task_found = True
                break

        if not task_found:
            return MarkdownResult(success=False, error=f"No task found containing '{partial_text}'")

        return self._write_file_safely('\n'.join(lines))
        """Find and delete a task based on partial text match"""
        if not partial_text.strip():
            return MarkdownResult(success=False, error="Search text cannot be empty")

        result = self.read_file()
        if not result.success:
            return result

        lines = result.content.split('\n')
        task_found = False

        for i, line in enumerate(lines):
            if "- [ ]" in line and partial_text.lower() in line.lower():
                lines.pop(i)
                task_found = True
                break

        if not task_found:
            return MarkdownResult(success=False, error=f"No task found containing '{partial_text}'")

        return self._write_file_safely('\n'.join(lines))
