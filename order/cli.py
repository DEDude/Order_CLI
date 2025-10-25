import os
import typer
from datetime import datetime
from order.markdown_handler import MarkdownHandler

DEV_NOTES_FILE: str = "dev-notes.md"
TODO_SECTION: str = "Todo"
NOTES_SECTION: str = "Notes"
IDEAS_SECTION: str = "Ideas"

def find_dev_notes_file() -> str:
    """Find dev-notes.md in current directory or walk up to find existing one"""
    custom_file = os.environ.get("ORDER_NOTES_FILE")
    if custom_file:
        return custom_file
    
    current_dir = os.getcwd()
    
    while current_dir != os.path.dirname(current_dir):  # Stop at root
        potential_file = os.path.join(current_dir, DEV_NOTES_FILE)
        if os.path.exists(potential_file):
            return potential_file
        current_dir = os.path.dirname(current_dir)
    
    return DEV_NOTES_FILE

def _validate_content(content: str, content_type: str) -> None:
    """Validate content is not empty and raise exit if invalid"""
    if not content.strip():
        typer.echo(f"Error: {content_type} content cannot be empty")
        raise typer.Exit(1)

def _add_content_with_feedback(section_type: str, content: str, content_type: str, branch: str = None) -> None:
    """Add content to daily section with consistent error handling"""
    _validate_content(content, content_type)
    
    handler = get_handler()
    today = get_today()
    result = handler.add_content_to_daily_section(today, section_type, content, branch)
    
    if result.success:
        typer.echo(f"{content_type} added: {content}")
    else:
        typer.echo(f"Error: {result.error}")
        raise typer.Exit(1)

def get_handler() -> MarkdownHandler:
    """Get a MarkdownHandler instance, creating file if needed"""
    file_path = find_dev_notes_file()
    
    handler = MarkdownHandler(file_path)
    result = handler.read_file()
    if not result.success:
        create_result = handler.create_file()
        if not create_result.success:
            typer.echo(f"Error creating file: {create_result.error}")
            raise typer.Exit(1)
    return handler

def get_today() -> str:
    """Get today's date in YYYY-MM-DD format"""
    return datetime.now().strftime("%Y-%m-%d")

app = typer.Typer()

@app.command()
def add(title: str, branch: str = typer.Option(None, "--branch", help="Override git branch detection")) -> None:
    """Add a new task"""
    task_content = f"- [ ] {title}"
    _add_content_with_feedback(TODO_SECTION, task_content, "Task", branch)

@app.command()
def note(content: str, branch: str = typer.Option(None, "--branch", help="Override git branch detection")) -> None:
    """Add a note to today's section"""
    _add_content_with_feedback(NOTES_SECTION, content, "Note", branch)

@app.command()    
def idea(content: str, branch: str = typer.Option(None, "--branch", help="Override git branch detection")) -> None:
    """Add an idea to today's section"""
    _add_content_with_feedback(IDEAS_SECTION, content, "Idea", branch)

@app.command()
def list() -> None:
    """List all tasks"""
    handler = get_handler()
    result = handler.read_file()
    
    if result.success:
        typer.echo(result.content)
    else:
        typer.echo(f"Error reading file: {result.error}")
        raise typer.Exit(1)

@app.command()
def delete(task_id: str) -> None:
    """Delete a task by partial text match"""
    handler = get_handler()
    result = handler.delete_task(task_id)
    
    if result.success:
        typer.echo(f"Task containing '{task_id}' deleted")
    else:
        typer.echo(f"Failed to delete task: {result.error}")
        raise typer.Exit(1)



@app.command()
def done(partial_text: str) -> None:
    """Mark a task as complete by partial text match"""
    handler = get_handler()
    result = handler.mark_task_complete(partial_text)
    
    if result.success:
        typer.echo(f"Task containing '{partial_text}' marked as complete")
    else:
        typer.echo(f"Failed to mark task as complete: {result.error}")
        raise typer.Exit(1)

@app.command()
def today() -> None:
    """Show today's tasks and notes"""
    handler = get_handler()
    today_date = get_today()
    result = handler.parse_daily_section(today_date)
    
    if result.success:
        typer.echo(result.content)
    else:
        typer.echo(f"Error reading today's section: {result.error}")
        raise typer.Exit(1)

@app.command()
def search(query: str) -> None:
    """Search for content in dev notes"""
    handler = get_handler()
    result = handler.search_content(query)
    
    if result.success:
        typer.echo(result.content)
    else:
        typer.echo(result.error)
        raise typer.Exit(1)
