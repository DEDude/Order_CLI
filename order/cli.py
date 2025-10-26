import os
import typer
from datetime import datetime
from order.markdown_handler import MarkdownHandler, MarkdownResult

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
    
    handle_result(result, f"{content_type} added: {content}", "Failed to add content")

def get_handler() -> MarkdownHandler:
    """Get a MarkdownHandler instance, creating file if needed"""
    file_path = find_dev_notes_file()
    
    handler = MarkdownHandler(file_path)
    result = handler.read_file()
    if not result.success:
        create_result = handler.create_file()
        if not create_result.success:
            typer.echo(f"Error: Failed to create file - {create_result.error}")
            raise typer.Exit(1)
    return handler

def get_today() -> str:
    """Get today's date in YYYY-MM-DD format"""
    return datetime.now().strftime("%Y-%m-%d")

def handle_result(result: MarkdownResult, success_msg: str, error_action: str) -> None:
    """Handle MarkdownResult with consistent success/error patterns"""
    if result.success:
        typer.echo(success_msg)
    else:
        typer.echo(f"Error: {error_action} - {result.error}")

        raise typer.Exit(1)

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
        typer.echo(f"Error: Failed to read file - {result.error}")
        raise typer.Exit(1)

@app.command()
def delete(task_id: str) -> None:
    """Delete a task by partial text match"""
    handler = get_handler()
    result = handler.delete_task(task_id)
    
    handle_result(result, f"Task containing '{task_id}' deleted", "Failed to delete task")

@app.command()
def done(partial_text: str) -> None:
    """Mark a task as complete by partial text match"""
    handler = get_handler()
    result = handler.mark_task_complete(partial_text)
    
    handle_result(result, f"Task containing '{partial_text}' marked as complete", "Failed to mark task complete")

@app.command()
def today() -> None:
    """Show today's tasks and notes"""
    handler = get_handler()
    today_date = get_today()
    result = handler.parse_daily_section(today_date)
    
    if result.success:
        typer.echo(result.content)
    else:
        typer.echo(f"Error: Failed to read today's section - {result.error}")
        raise typer.Exit(1)

@app.command()
def search(query: str) -> None:
    """Search for content in dev notes"""
    handler = get_handler()
    result = handler.search_content(query)
    
    if result.success:
        typer.echo(result.content)
    else:
        typer.echo(f"Error: Search failed - {result.error}")
        raise typer.Exit(1)

@app.command()
def carry(partial_text: str) -> None:
    """Move a task to today with history trail"""
    handler = get_handler()
    result = handler.carry_task_forward(partial_text)

    handle_result(result, f"Task carried forward: {result.content}", "Failed to carry task")

@app.command("66")
def order_66() -> None:
    """Execute Order 66"""
    jedi_list = [
        "Master Yoda",
        "Obi-Wan Kenobi", 
        "Mace Windu",
        "Anakin Skywalker",
        "Ahsoka Tano",
        "Ki-Adi-Mundi",
        "Plo Koon",
        "Kit Fisto",
        "Aayla Secura",
        "Luminara Unduli"
    ]
    
    typer.echo("EXECUTING ORDER 66")
    typer.echo("The time has come. Execute Order 66.")
    typer.echo("\nJedi Target List:")
    for jedi in jedi_list:
        typer.echo(f"  {jedi}")
    typer.echo("\nGood soldiers follow orders.")

@app.command()
def install_hooks() -> None:
    """Install git hooks for automatic dev-notes.md integration"""
    handler = get_handler()
    result = handler.install_git_hooks()

    handle_result(result, "Git hooks installed successfully", "Failed to install git hooks")

