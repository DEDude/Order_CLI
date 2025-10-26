# Order - Developer Notes & Task Management CLI

A terminal-based productivity tool for developers to manage daily tasks, notes, and ideas in a git-friendly markdown format.

## Features

- **Quick task management** - Add, complete, delete, and carry forward tasks
- **Daily notes & ideas** - Capture context and brainstorm in organized sections  
- **Git integration** - Auto-commit dev notes with code changes
- **Team collaboration** - Branch-aware user sections prevent merge conflicts
- **Smart file discovery** - Finds dev-notes.md in project root automatically
- **Markdown storage** - Human-readable, searchable, git-friendly format

## Installation

```bash
pip install order
```

## Quick Start

```bash
# Add tasks, notes, and ideas
order add "Fix login bug"
order note "Left off debugging OAuth flow"  
order idea "Consider Redis for session storage"

# View and manage tasks
order list                    # Show all content
order today                   # Show today's section only
order done "Fix login"       # Mark task complete
order carry "Fix login"      # Move task to today with history

# Search and organize
order search "OAuth"          # Find content across dates
order delete "old task"      # Remove completed tasks

# Git integration
order install-hooks          # Auto-commit dev notes with code
```

## Commands

### Adding Content
- `order add "task description"` - Add new task to today's todo list
- `order note "context info"` - Add note to today's section  
- `order idea "feature idea"` - Add idea to today's section
- `order --branch feature add "task"` - Override git branch detection

### Managing Tasks  
- `order done "partial text"` - Mark task as complete
- `order carry "partial text"` - Move task to today with history trail
- `order delete "partial text"` - Remove task entirely

### Viewing Content
- `order list` - Show all dev notes content
- `order today` - Show only today's section
- `order search "query"` - Find content across all dates

### Git Integration
- `order install-hooks` - Set up automatic dev-notes.md commits

## File Format

Order creates a `dev-notes.md` file with this structure:

```markdown
# Dev Notes

## Project Context

*Add project-level context, goals, and background information here.*

## 2025-10-26

### username-branch (@username)
#### Todo
- [ ] Fix login bug
- [x] Update authentication tests (carried from 2025-10-25)

#### Notes
- Left off debugging OAuth flow
- Database connection seems slow

#### Ideas
- Consider Redis for session storage
```

## Team Collaboration

Order supports team workflows with branch-aware user sections:

- **User sections** - Each team member gets their own subsection
- **Branch awareness** - Different branches create separate sections  
- **Merge friendly** - Markdown format reduces git conflicts
- **History preservation** - Task carryover maintains context

## Configuration

### Environment Variables
- `ORDER_NOTES_FILE` - Custom path to dev notes file

### Git Integration
After running `order install-hooks`, your dev notes are automatically committed with code changes:

```bash
git commit -m "Fix login bug"  # dev-notes.md auto-staged and committed
```

## Development

```bash
# Clone and install
git clone <repo-url>
cd order
poetry install

# Run tests
poetry run pytest

# Build package
poetry build
```

## Dependencies

This project uses several open source packages including:
- [typer](https://github.com/tiangolo/typer) (BSD-3-Clause) - Modern CLI framework
- [rich](https://github.com/Textualize/rich) (MIT) - Beautiful terminal output

## License

MIT License - see LICENSE file for details.
