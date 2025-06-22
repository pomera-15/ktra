# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ktra (カトレア) is a personal AI agent built using the OpenAI Agent SDK. It provides task management, safe command execution, and natural language interaction through a CLI interface.

## Essential Commands

### Environment Setup
- Create virtual environment: `python3 -m venv venv`
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Set up API key: `echo 'OPENAI_API_KEY=your_key_here' > .env`

### Development
- Run application: `python main.py`
- Run all tests: `python -m pytest tests/ -v`
- Run specific test file: `python -m pytest tests/test_task.py -v`
- Run single test: `python -m pytest tests/test_task.py::TestTaskFunctions::test_add_task_basic -v`

## Architecture

### Core Components

**Agent Creation (agent.py)**
- `create_ktra_agent()`: Main factory function that creates the OpenAI Agent with tools
- Uses OpenAI Agent SDK's `Agent` class with 5 registered tools
- Loads system prompt from `prompts/system.txt`
- Model: gpt-3.5-turbo

**Tool Pattern**
All tools follow a specific pattern due to OpenAI Agent SDK requirements:
- Internal functions prefixed with `_` (e.g., `_add_task`)
- Public tools created via `function_tool()` decorator
- Example: `add_task = function_tool(_add_task)`

**Tool Registration**
Tools are imported and passed to Agent constructor:
```python
tools=[add_task, list_tasks, update_task, execute_command, get_system_info]
```

### Data Flow

1. **CLI Input** (main.py) → **Agent** (agent.py) → **Tools** (tools/)
2. **Task Storage**: JSON-based persistence in `memory/store.json`
3. **Command Execution**: Allowlist-based security with timeout protection

### Security Architecture

**Shell Command Protection** (tools/shell.py):
- Dangerous commands blocked: `rm -rf`, `sudo`, `chmod 777`, etc.
- Allowlist: `ls`, `pwd`, `git status`, `git log`, `git diff`, `curl`, `ping`, `date`, `whoami`, `echo`
- 30-second timeout on all commands
- Working directory isolation

**API Key Validation** (main.py):
- Format validation: must start with `sk-` or `sk-proj-`
- Length validation: minimum 10 characters
- Comprehensive error messages with setup instructions

### Testing Structure

**Test Organization**:
- Unit tests for each component in `tests/`
- Tool functions tested via internal `_function` versions
- Mocking patterns for TaskManager and subprocess calls
- API key validation edge cases covered

**Key Testing Pattern**:
```python
# Import internal functions for testing
from tools.task import _add_task as add_task
```

This is necessary because `@function_tool` decorator wraps functions, making them non-callable in tests.

## Important Implementation Details

### OpenAI Agent SDK Integration
- Uses `agents.Agent` and `agents.Runner` from openai-agents package
- Tools must be created with `@function_tool` decorator or `function_tool()` function
- Agent execution via `Runner.run_sync(agent, user_input)`

### Task Management Schema
Tasks stored with fields: id, title, description, deadline, priority, status, created_at, updated_at
- Priority levels: low, medium, high
- Status values: pending, completed
- Unique UUID for each task

### Error Handling
- API key validation with clear setup instructions
- Agent initialization failure handling
- Runtime error recovery with user guidance
- Graceful exit on KeyboardInterrupt