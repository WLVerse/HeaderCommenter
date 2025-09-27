# HeaderCommenter AI Instructions

## Project Overview
HeaderCommenter is a Tkinter-based GUI application for managing standardized C++ file headers, specifically designed for DigiPen academic projects. The tool provides a file tree browser for C++ files (`.h`, `.hpp`, `.c`, `.cpp`, `.inl`) and facilitates editing header comment templates.

## Architecture & Key Components

### Core Application Structure
- **Main Module**: `src/editor.py` - Single-file application using Tkinter
- **Configuration System**: INI-based config using `configparser` with global `config_path` variable
- **Template System**: `.fmt` files with variable substitution (`${FILENAME}`, `${EMAIL}`, etc.)
- **File Discovery**: Recursive directory scanning for C++ files only
- **UI Pattern**: Left panel file tree + right panel editor (currently minimal in v1.4)

### Critical Global Variables
```python
config_path = ""  # Managed globally, initialized from config or defaults
settings_window = None  # Singleton pattern for settings dialog
CPP_EXTENSIONS = {".h", ".hpp", ".c", ".cpp", ".inl"}  # Immutable file filter
```

### Configuration Management Pattern
The app uses a hybrid config approach:
- **Legacy**: `headercommenter-config.txt` (simple text file from old version)
- **Current**: `headercommenter-config.ini` with sections `[Settings]`
- **Key Functions**: `save_config(section, key, value)` and `read_config(section, key)`
- **Persistence**: Last opened directory, config folder, template path

## Development Workflows

### Building & Packaging
```bash
# Auto-increment version and build executable
./create-installer.bat
# Uses PyInstaller with --onefile --windowed flags
# Generates versioned .exe files and .spec files
```

### Version Management
- Version stored in `version.txt` (simple format like "1.4")
- Build script auto-increments minor version
- PyInstaller specs generated per version (e.g., `HeaderCommenter_v1.3.exe.spec`)

### Key File Relationships
- `headercommenter.fmt`: Default template with DigiPen-specific format
- `headercommenter-config.ini`: Persistent settings
- `src/editor_old.py`: Previous version with complex form-based editor (keep for reference)

## Project-Specific Patterns

### UI Theming
Dark mode is hardcoded with consistent color variables:
```python
BG_COLOR = "#1e1e1e"
TEXT_COLOR = "#d4d4d4" 
MENU_COLOR = "#333333"
CURSOR_COLOR = "#ffffff"
```

### File Tree Construction
The `insert_tree_nodes()` function builds hierarchical directory structure using `ttk.Treeview` with:
- Directory nodes cached in `dir_nodes` dict
- Files stored with full path in `values=[full_path]`
- Recursive directory creation for nested paths

### Settings Window Pattern
- Global singleton pattern prevents multiple instances
- Modal-like behavior with `Toplevel` widget
- `center_window()` utility for consistent positioning
- Save operations update global `config_path`

### Template Variable System
Current template uses `${VARIABLE}` placeholders:
- `${FILENAME}` - Current file name
- `${EMAIL}` - Author email
- `${CURRENTDATE}` - Current date
- `${CURRENTYEAR}` - Current year
- `${DESCRIPTION}` - File description

## Evolution Context & Development Roadmap
**CRITICAL**: The app is currently in a simplified state. `src/editor_old.py` contains the full-featured implementation that represents the target architecture:

### Current State (`editor.py`)
- Minimal file browser with settings dialog
- Template editing in settings only
- No file editing capabilities

### Target State (`editor_old.py` - Reference Implementation)
- **Dynamic Author Management**: Add/remove author forms with contribution percentages
- **Live Header Preview**: Real-time header generation as user types
- **Form-Based Editing**: Structured fields for team name, website, description, authors
- **Contribution Points**: Dynamic bullet points per author with add/remove buttons  
- **Auto-save Option**: Toggle between manual and automatic saving
- **Code/Header Split View**: Separate areas for header comments vs actual code

### Key Patterns from `editor_old.py` to Implement
```python
# Dynamic form management
self.author_frames = []  # List of author form dictionaries
self.add_author_frame()  # Dynamic UI creation
self.remove_author_frame()  # Dynamic UI cleanup

# Live preview updates
header_form.update_header_text()  # Real-time header generation
header_text.config(state="normal")  # Enable/disable preview editing

# Multi-panel layout
header_form_frame, header_preview_frame, code_frame  # Three-section layout
```

## Build Dependencies
- **PyInstaller**: For executable generation
- **tkinter**: Built-in GUI framework (no external deps)
- **configparser**: Built-in config management
- **Windows-focused**: Batch scripts and PyInstaller targeting Windows

## When Working on This Project
- **Always reference `editor_old.py`** for implementation patterns and UI structure
- Maintain the dark theme consistency across new UI elements
- Use the established config pattern for any new settings
- Keep C++ file filtering consistent with `CPP_EXTENSIONS`
- Follow the singleton pattern for modal dialogs
- **Goal**: Restore full editor functionality from `editor_old.py` with current config system
- Test build process with `create-installer.bat` for distribution