import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Toplevel
import os
import configparser
import re
import datetime
import textwrap

try:
    import ctypes
    from ctypes import wintypes
    CTYPES_AVAILABLE = True
except ImportError:
    CTYPES_AVAILABLE = False

# Allowed C++ file extensions
CPP_EXTENSIONS = {".h", ".hpp", ".c", ".cpp", ".inl"}
CONFIG_FILE_NAME = "hc-config.ini"

# Compiled regex patterns for performance
TEMPLATE_VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')
ESCAPED_VAR_PATTERN = re.compile(r'\\\$\\\{([^}]+)\\\}')
COMMENT_END_PATTERN = re.compile(r'\*/\s*(?:/\*.*?\*/)?' , re.DOTALL)

# Template content cache
_template_cache = {'path': None, 'content': None, 'mtime': None}

# Global variables
config_path = ""
settings_window = None
metadata_window = None

def safe_read_file(file_path, encoding='utf-8', errors='replace'):
    """Safely read a file with consistent error handling."""
    try:
        with open(file_path, 'r', encoding=encoding, errors=errors) as f:
            return f.read()
    except Exception as e:
        log_message(f"Error reading {os.path.basename(file_path)}: {e}")
        return None

def safe_write_file(file_path, content, encoding='utf-8'):
    """Safely write to a file with consistent error handling."""
    try:
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        log_message(f"Error writing {os.path.basename(file_path)}: {e}")
        return False

def get_cached_template_content():
    """Get template content with caching for performance."""
    global _template_cache
    
    template_path = read_config('Settings', 'TemplatePath')
    if not template_path or not os.path.isfile(template_path):
        return ""
    
    try:
        current_mtime = os.path.getmtime(template_path)
        
        # Check if we have cached content and file hasn't changed
        if (_template_cache['path'] == template_path and 
            _template_cache['mtime'] == current_mtime and 
            _template_cache['content'] is not None):
            return _template_cache['content']
        
        # Read and cache new content
        content = safe_read_file(template_path)
        if content is not None:
            _template_cache['path'] = template_path
            _template_cache['content'] = content
            _template_cache['mtime'] = current_mtime
            return content
    except Exception:
        pass
    
    return ""

def extract_template_variables(content):
    """Extract template variables using compiled regex for performance."""
    if not content:
        return set()
    return {tag.upper() for tag in TEMPLATE_VAR_PATTERN.findall(content)}

def show_error_message(title, message, parent=None):
    """Show standardized error message with logging."""
    log_message(f"Error: {message}")
    messagebox.showerror(title, message, parent=parent)

def show_warning_message(title, message, parent=None):
    """Show standardized warning message with logging."""
    log_message(f"Warning: {message}")
    messagebox.showwarning(title, message, parent=parent)

def create_standard_button(parent, text, command, bg_color=None, **kwargs):
    """Create a standardized button with consistent styling."""
    if bg_color is None:
        bg_color = MENU_COLOR
    
    return tk.Button(parent, text=text, command=command,
                    bg=bg_color, fg=TEXT_COLOR, font=("Consolas", 10),
                    padx=6, pady=2, cursor="hand2", **kwargs)

def clamp_to_monitor_bounds(x, y, width, height, monitor):
    """Clamp window position to stay within monitor bounds."""
    if x < monitor['left']:
        x = monitor['left']
    elif x + width > monitor['right']:
        x = monitor['right'] - width
    
    if y < monitor['top']:
        y = monitor['top']
    elif y + height > monitor['bottom']:
        y = monitor['bottom'] - height
    
    return x, y

def create_dialog_buttons(parent, buttons_config):
    """Create standardized dialog buttons with consistent layout."""
    button_frame = tk.Frame(parent, bg=BG_COLOR)
    button_frame.pack(fill="x", padx=6, pady=10)
    
    for config in buttons_config:
        text = config['text']
        command = config['command']
        side = config.get('side', 'right')
        bg_color = config.get('bg_color', MENU_COLOR)
        
        btn = create_standard_button(button_frame, text, command, bg_color)
        btn.pack(side=side, padx=6)
    
    return button_frame

def log_message(message):
    """Logs a message to the logger area."""
    if 'logger_text' in globals():
        logger_text.config(state="normal")
        logger_text.insert(tk.END, f"{message}\n")
        logger_text.see(tk.END)
        logger_text.config(state="disabled")

def save_config(section, key, value):
    """Saves a key-value pair to the INI config file."""
    config = configparser.ConfigParser()
    global config_path

    # Use the stored config path or default to the local directory
    if not config_path:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE_NAME)
        
    if os.path.exists(config_path):
        config.read(config_path)

    if section not in config:
        config[section] = {}
    
    config[section][key] = value

    try:
        with open(config_path, "w") as file:
            config.write(file)
    except IOError as e:
        messagebox.showerror("File Error", f"Could not save config file: {e}")

def read_config(section, key):
    """Reads a value from the INI config file."""
    config = configparser.ConfigParser()
    global config_path
    
    # Use the stored config path or default to the local directory
    if not config_path:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE_NAME)
    
    # Try to read the config file
    try:
        if os.path.exists(config_path):
            config.read(config_path)
            if section in config and key in config[section]:
                return config[section][key]
    except Exception as e:
        log_message(f"Configuration error: {e}")
    
    return ""

def resolve_variable_value(key, value, var_type, target_file_path=None):
    """Resolve a variable value based on its type."""
    if var_type == "Custom":
        return value
    elif var_type == "File Name" and target_file_path:
        return os.path.basename(target_file_path)
    elif var_type == "File Name (no ext)" and target_file_path:
        return os.path.splitext(os.path.basename(target_file_path))[0]
    elif var_type == "Full Date":
        return datetime.datetime.now().strftime("%b %d, %Y")
    elif var_type == "Date":
        return datetime.datetime.now().strftime("%d/%m/%Y")
    elif var_type == "Year":
        return str(datetime.datetime.now().year)
    else:
        return value  # Fallback to stored value

def get_all_variables_with_types():
    """Get all variables (from template and metadata) with their resolved values."""
    variables = {}
    try:
        # Get all variables from template using cached content
        template_content = get_cached_template_content()
        template_vars = extract_template_variables(template_content)
        
        # Load config
        config = configparser.ConfigParser()
        if os.path.exists(config_path):
            config.read(config_path)
        
        # Process all template variables
        for var_name in template_vars:
            var_key = var_name.upper()  # Config uses uppercase keys
            var_type = "Custom"
            var_value = ""
            
            # Check if this variable exists in metadata
            if 'Metadata' in config and var_key in config['Metadata']:
                var_value = config['Metadata'][var_key]
            
            # Check if this variable has a type defined
            if 'MetadataTypes' in config and var_key in config['MetadataTypes']:
                var_type = config['MetadataTypes'][var_key]
            
            # For common variables, set default types if not configured
            if var_type == "Custom" and not var_value:
                if var_name == "CURRENTDATE":
                    var_type = "Full Date"
                elif var_name == "CURRENTYEAR":
                    var_type = "Year"
                elif var_name == "FILENAME":
                    var_type = "File Name"
                elif var_name == "EMAIL":
                    var_type = "Custom"
                    var_value = "your.email@example.com"
            
            variables[var_name] = {
                'value': var_value,
                'type': var_type,
                'resolved': resolve_variable_value(var_name, var_value, var_type)
            }
            
    except Exception as e:
        log_message(f"Error loading variables: {e}")
    
    return variables

def get_cpp_files(directory):
    """Recursively finds all C++ files and returns them as a list of (fullpath, relative path)."""
    cpp_files = []
    if not os.path.isdir(directory):
        messagebox.showerror("Error", f"Directory not found: {directory}")
        return cpp_files
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1].lower() in CPP_EXTENSIONS:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, directory)
                cpp_files.append((full_path, relative_path))
    return cpp_files

def open_directory(directory):
    """Opens a directory and lists all C++ files in a tree view."""
    if not directory:
        return
        
    file_tree.delete(*file_tree.get_children())  # Clear previous entries
    
    # Update root path label
    root_path_label.config(text=f"Root: {directory}")
    # Update wrapping for the new text
    root.after_idle(update_root_path_wrapping)
    
    cpp_files = get_cpp_files(directory)

    if not cpp_files:
        messagebox.showinfo("No Files Found", f"No C++ files found in the directory:\n{directory}")
        # Keep the path label even if no files found
        return

    insert_tree_nodes(directory, cpp_files)
    save_config('Settings', 'LastOpenedDirectory', directory)
    root.title(f"Header Commenter - {directory}")

def insert_tree_nodes(directory, cpp_files):
    """Inserts directories and files into the tree view."""
    dir_nodes = {}
    for full_path, relative_path in cpp_files:
        parts = os.path.normpath(relative_path).split(os.sep)
        parent_id = ""
        current_path = ""
        
        for part in parts[:-1]:
            current_path = os.path.join(current_path, part) if current_path else part
            if current_path not in dir_nodes:
                dir_nodes[current_path] = file_tree.insert(parent_id, "end", text=part, open=True)
            parent_id = dir_nodes[current_path]
        
        file_name = parts[-1]
        file_tree.insert(parent_id, "end", text=file_name, values=[full_path])

def center_window_on_screen(window, width, height):
    """Centers a tkinter window on the primary screen."""
    window.update_idletasks()
    
    try:
        # Try to get primary monitor bounds for better multi-monitor support
        monitor = get_monitor_bounds(0, 0)  # Primary monitor typically at 0,0
        x = monitor['left'] + (monitor['width'] // 2) - (width // 2)
        y = monitor['top'] + (monitor['height'] // 2) - (height // 2)
        
        # Ensure window stays within monitor bounds
        x, y = clamp_to_monitor_bounds(x, y, width, height, monitor)
            
    except:
        # Fallback to simple screen centering
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
    
    window.geometry(f'{int(width)}x{int(height)}+{int(x)}+{int(y)}')

def get_screen_dimensions():
    """Get primary screen dimensions using existing root or fallback."""
    try:
        # Use existing root window if available
        if 'root' in globals() and root.winfo_exists():
            return root.winfo_screenwidth(), root.winfo_screenheight()
        else:
            # Create temporary root only if needed
            temp_root = tk.Tk()
            temp_root.withdraw()
            screen_width = temp_root.winfo_screenwidth()
            screen_height = temp_root.winfo_screenheight()
            temp_root.destroy()
            return screen_width, screen_height
    except:
        return 1920, 1080  # Ultimate fallback

def get_all_monitor_bounds():
    """Get bounds of all available monitors."""
    monitors = []
    if not CTYPES_AVAILABLE:
        # Fallback to screen dimensions if ctypes not available
        screen_width, screen_height = get_screen_dimensions()
        return [{
            'left': 0, 'top': 0, 'right': screen_width, 'bottom': screen_height,
            'width': screen_width, 'height': screen_height
        }]
    
    try:
        
        def monitor_enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
            try:
                user32 = ctypes.windll.user32
                
                class MONITORINFO(ctypes.Structure):
                    _fields_ = [
                        ('cbSize', wintypes.DWORD),
                        ('rcMonitor', wintypes.RECT),
                        ('rcWork', wintypes.RECT),
                        ('dwFlags', wintypes.DWORD)
                    ]
                
                monitor_info = MONITORINFO()
                monitor_info.cbSize = ctypes.sizeof(MONITORINFO)
                
                if user32.GetMonitorInfoW(hMonitor, ctypes.byref(monitor_info)):
                    work_area = monitor_info.rcWork
                    monitors.append({
                        'left': work_area.left,
                        'top': work_area.top,
                        'right': work_area.right,
                        'bottom': work_area.bottom,
                        'width': work_area.right - work_area.left,
                        'height': work_area.bottom - work_area.top
                    })
            except:
                pass
            return True  # Continue enumeration
        
        # Define the callback type
        MONITORENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
        
        # Enumerate all monitors
        user32 = ctypes.windll.user32
        user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(monitor_enum_proc), 0)
        
    except:
        pass
    
    # Fallback if no monitors found via API
    if not monitors:
        screen_width, screen_height = get_screen_dimensions()
        
        monitors.append({
            'left': 0,
            'top': 0,
            'right': screen_width,
            'bottom': screen_height,
            'width': screen_width,
            'height': screen_height
        })
    
    return monitors

def is_window_position_valid(x, y, width, height):
    """Check if a window position is visible on any current monitor."""
    try:
        monitors = get_all_monitor_bounds()
        
        # Check if at least part of the window is visible on any monitor
        for monitor in monitors:
            # Check if window overlaps with this monitor
            window_right = x + width
            window_bottom = y + height
            
            # Window overlaps if there's intersection
            if (x < monitor['right'] and window_right > monitor['left'] and
                y < monitor['bottom'] and window_bottom > monitor['top']):
                
                # Check if at least 100x100 pixels are visible (enough for title bar)
                visible_left = max(x, monitor['left'])
                visible_top = max(y, monitor['top'])
                visible_right = min(window_right, monitor['right'])
                visible_bottom = min(window_bottom, monitor['bottom'])
                
                visible_width = visible_right - visible_left
                visible_height = visible_bottom - visible_top
                
                if visible_width >= 100 and visible_height >= 100:
                    return True
        
        return False
    except:
        return False  # If we can't determine, assume invalid for safety

def get_safe_window_position(width, height):
    """Get a safe window position on the primary monitor."""
    try:
        monitors = get_all_monitor_bounds()
        if monitors:
            # Use the first monitor (usually primary)
            primary = monitors[0]
            x = primary['left'] + (primary['width'] // 2) - (width // 2)
            y = primary['top'] + (primary['height'] // 2) - (height // 2)
            
            # Ensure it fits within the monitor
            x, y = clamp_to_monitor_bounds(x, y, width, height, primary)
            
            return x, y
    except:
        pass
    
    # Ultimate fallback
    return 100, 100

def get_monitor_bounds(x, y):
    """Get the bounds of the monitor containing the given point."""
    if not CTYPES_AVAILABLE:
        # Fallback if ctypes not available
        screen_width, screen_height = get_screen_dimensions()
        return {
            'left': 0, 'top': 0, 'right': screen_width, 'bottom': screen_height,
            'width': screen_width, 'height': screen_height
        }
        
    try:
        
        # Windows API to get monitor info
        user32 = ctypes.windll.user32
        
        # Get monitor handle for the point
        monitor = user32.MonitorFromPoint(
            wintypes.POINT(int(x), int(y)), 
            2  # MONITOR_DEFAULTTONEAREST
        )
        
        if monitor:
            # Get monitor info
            class MONITORINFO(ctypes.Structure):
                _fields_ = [
                    ('cbSize', wintypes.DWORD),
                    ('rcMonitor', wintypes.RECT),
                    ('rcWork', wintypes.RECT),
                    ('dwFlags', wintypes.DWORD)
                ]
            
            monitor_info = MONITORINFO()
            monitor_info.cbSize = ctypes.sizeof(MONITORINFO)
            
            if user32.GetMonitorInfoW(monitor, ctypes.byref(monitor_info)):
                work_area = monitor_info.rcWork
                return {
                    'left': work_area.left,
                    'top': work_area.top,
                    'right': work_area.right,
                    'bottom': work_area.bottom,
                    'width': work_area.right - work_area.left,
                    'height': work_area.bottom - work_area.top
                }
    except:
        pass
    
    # Fallback to full screen dimensions if Windows API fails
    screen_width, screen_height = get_screen_dimensions()
    
    return {
        'left': 0,
        'top': 0,
        'right': screen_width,
        'bottom': screen_height,
        'width': screen_width,
        'height': screen_height
    }

def center_window(window, width, height):
    """Centers a tkinter window on the main application window, respecting multiple monitors."""
    def do_center():
        window.update_idletasks()
        root.update_idletasks()  # Ensure main window is fully realized
        
        try:
            # Get main window position and size
            main_x = root.winfo_x()
            main_y = root.winfo_y()
            main_width = root.winfo_width()
            main_height = root.winfo_height()
            
            # Only use main window centering if it has valid dimensions and position
            if main_width > 100 and main_height > 100 and main_x >= 0 and main_y >= 0:
                # Calculate center position relative to main window
                x = main_x + (main_width // 2) - (width // 2)
                y = main_y + (main_height // 2) - (height // 2)
                
                # Get the monitor bounds where the main window is located
                main_center_x = main_x + main_width // 2
                main_center_y = main_y + main_height // 2
                monitor = get_monitor_bounds(main_center_x, main_center_y)
                
                # Ensure window stays within the same monitor as the main window
                x, y = clamp_to_monitor_bounds(x, y, width, height, monitor)
                
            else:
                # Fallback to screen centering if main window isn't ready
                screen_width = window.winfo_screenwidth()
                screen_height = window.winfo_screenheight()
                x = (screen_width // 2) - (width // 2)
                y = (screen_height // 2) - (height // 2)
                
                # Basic screen bounds check for fallback
                if x < 0:
                    x = 0
                elif x + width > screen_width:
                    x = screen_width - width
                
                if y < 0:
                    y = 0
                elif y + height > screen_height:
                    y = screen_height - height
            
            window.geometry(f'{int(width)}x{int(height)}+{int(x)}+{int(y)}')
            
        except tk.TclError:
            # If there's any error getting main window info, fallback to screen centering
            center_window_on_screen(window, width, height)
    
    # Center immediately
    try:
        root.update_idletasks()
        do_center()
    except:
        # Fallback to screen centering
        center_window_on_screen(window, width, height)

def open_settings_window():
    """Opens the settings window."""
    global settings_window
    if settings_window and settings_window.winfo_exists():
        settings_window.lift()
        return

    settings_window = Toplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("500x300")
    center_window(settings_window, 500, 300)
    settings_window.config(bg=BG_COLOR)
    
    def close_settings_window():
        global settings_window
        if settings_window:
            settings_window.destroy()
            settings_window = None

    settings_window.protocol("WM_DELETE_WINDOW", close_settings_window)

    # INI File Location Section
    ini_frame = tk.LabelFrame(settings_window, text="INI File Location", bg=BG_COLOR, fg=TEXT_COLOR)
    ini_frame.pack(fill="x", padx=6, pady=5)
    
    ini_path_var = tk.StringVar()
    ini_path_entry = tk.Entry(ini_frame, textvariable=ini_path_var, bg=BG_COLOR, fg=TEXT_COLOR, insertbackground=CURSOR_COLOR)
    ini_path_entry.pack(side="left", fill="x", expand=True, padx=6, pady=5)
    ini_path_var.set(os.path.dirname(config_path) if config_path else "")
    
    def auto_save_ini_folder(*args):
        """Auto-save when ini folder path changes."""
        global config_path
        new_config_folder = ini_path_var.get().strip()
        
        if new_config_folder and new_config_folder != os.path.dirname(config_path):
            old_config_path = config_path
            config_path = os.path.join(new_config_folder, "hc-config.ini")
            save_config('Settings', 'ConfigFolder', new_config_folder)
            log_message(f"Config location changed to: {config_path}")
    
    def select_ini_folder():
        folder_path = filedialog.askdirectory(parent=settings_window)
        if folder_path:
            ini_path_var.set(folder_path)
    
    create_standard_button(ini_frame, "Browse", select_ini_folder).pack(side="right", padx=6)

    # Template File Section
    template_frame = tk.LabelFrame(settings_window, text="Template File (.fmt)", bg=BG_COLOR, fg=TEXT_COLOR)
    template_frame.pack(fill="x", padx=6, pady=5)
    
    template_path_var = tk.StringVar()
    template_path_entry = tk.Entry(template_frame, textvariable=template_path_var, bg=BG_COLOR, fg=TEXT_COLOR, insertbackground=CURSOR_COLOR)
    template_path_entry.pack(side="left", fill="x", expand=True, padx=6, pady=5)
    
    # Load current template path
    current_template_path = read_config('Settings', 'TemplatePath')
    if current_template_path:
        template_path_var.set(current_template_path)
    
    def auto_save_template_path(*args):
        """Auto-save when template path changes."""
        new_template_path = template_path_var.get().strip()
        old_template_path = read_config('Settings', 'TemplatePath')
        
        if new_template_path and new_template_path != old_template_path:
            save_config('Settings', 'TemplatePath', new_template_path)
            log_message(f"Template file updated: {os.path.basename(new_template_path)}")

    
    def select_template_file():
        file_path = filedialog.askopenfilename(
            title="Select Template File",
            filetypes=[("Format files", "*.fmt"), ("All files", "*.*")],
            defaultextension=".fmt",
            parent=settings_window
        )
        if file_path:
            template_path_var.set(file_path)
    
    create_standard_button(template_frame, "Browse", select_template_file).pack(side="right", padx=6)

    # Set up auto-save triggers (use a delay to avoid saving while typing)
    def delayed_auto_save_ini():
        settings_window.after(1000, auto_save_ini_folder)  # 1 second delay
    
    def delayed_auto_save_template():
        settings_window.after(1000, auto_save_template_path)  # 1 second delay
    
    # Bind auto-save to variable changes
    ini_path_var.trace_add("write", lambda *args: delayed_auto_save_ini())
    template_path_var.trace_add("write", lambda *args: delayed_auto_save_template())

    # Close button only (no save button needed)
    button_frame = tk.Frame(settings_window, bg=BG_COLOR)
    button_frame.pack(fill="x", padx=6, pady=10)

    create_standard_button(button_frame, "Close", close_settings_window).pack(side="right", padx=6)

def open_last_opened_directory():
    """Opens the last opened directory from the config file."""
    directory = read_config('Settings', 'LastOpenedDirectory')
    if directory and os.path.isdir(directory):
        log_message(f"Restored previous directory: {os.path.basename(directory)}")
        open_directory(directory)
    else:
        log_message("No previous directory to restore")
    


def save_window_state():
    """Saves the current window size and splitter positions to config."""
    try:
        # Check if anything has actually changed before saving
        geometry = root.geometry()
        current_geometry = read_config('WindowState', 'Geometry')
        
        current_main_sash = read_config('WindowState', 'MainSashPosition')
        current_top_sash = read_config('WindowState', 'TopSashPosition')
        
        # Get current positions
        main_sash_pos = main_paned.sash_coord(0)[1] if 'main_paned' in globals() and len(main_paned.panes()) > 1 else 500
        top_sash_pos = top_paned.sash_coord(0)[0] if 'top_paned' in globals() and len(top_paned.panes()) > 1 else 300
        
        # Only save if something changed
        changed = False
        if geometry != current_geometry:
            save_config('WindowState', 'Geometry', geometry)
            changed = True
            
        if str(main_sash_pos) != current_main_sash:
            save_config('WindowState', 'MainSashPosition', str(main_sash_pos))
            changed = True
        
        if str(top_sash_pos) != current_top_sash:
            save_config('WindowState', 'TopSashPosition', str(top_sash_pos))
            changed = True
            
        if changed:
            log_message("Layout preferences saved")
            
        root.lift()
    except Exception as e:
        log_message(f"Window preferences save failed: {e}")
        root.lift()

def restore_window_state():
    """Restores the window size and splitter positions from config with monitor validation."""
    try:
        restored_something = False
        
        # Restore window geometry with validation
        geometry = read_config('WindowState', 'Geometry')
        if geometry:
            try:
                # Parse geometry string (e.g., "1200x700+100+50")
                if 'x' in geometry and '+' in geometry:
                    # Split into size and position parts
                    size_part = geometry.split('+')[0]
                    pos_parts = geometry.split('+')[1:]
                    
                    if len(pos_parts) >= 2:
                        width, height = map(int, size_part.split('x'))
                        x, y = int(pos_parts[0]), int(pos_parts[1])
                        
                        # Validate the position is still accessible
                        if is_window_position_valid(x, y, width, height):
                            root.geometry(geometry)
                            log_message("Window position restored and validated")
                        else:
                            # Position is no longer valid, use safe position
                            safe_x, safe_y = get_safe_window_position(width, height)
                            safe_geometry = f"{width}x{height}+{safe_x}+{safe_y}"
                            root.geometry(safe_geometry)
                            # Update config with new safe position
                            save_config('WindowState', 'Geometry', safe_geometry)
                            log_message("Window moved to safe position (monitor configuration changed)")
                        
                        root.update_idletasks()
                        restored_something = True
                    else:
                        # Invalid geometry format, use default safe position
                        safe_x, safe_y = get_safe_window_position(1200, 700)
                        safe_geometry = f"1200x700+{safe_x}+{safe_y}"
                        root.geometry(safe_geometry)
                        save_config('WindowState', 'Geometry', safe_geometry)
                        log_message("Used default window size and safe position")
                        restored_something = True
                else:
                    # Invalid geometry format
                    raise ValueError("Invalid geometry format")
                    
            except (ValueError, IndexError) as e:
                log_message(f"Invalid saved geometry: {e}, using safe defaults")
                safe_x, safe_y = get_safe_window_position(1200, 700)
                safe_geometry = f"1200x700+{safe_x}+{safe_y}"
                root.geometry(safe_geometry)
                save_config('WindowState', 'Geometry', safe_geometry)
                restored_something = True
        
        # Restore splitter positions after a short delay to ensure widgets are created
        def restore_splitters():
            try:
                splitter_restored = False
                
                main_sash_pos = read_config('WindowState', 'MainSashPosition')
                if main_sash_pos and 'main_paned' in globals():
                    main_paned.sash_place(0, 0, int(main_sash_pos))
                    splitter_restored = True
                
                top_sash_pos = read_config('WindowState', 'TopSashPosition')
                if top_sash_pos and 'top_paned' in globals():
                    top_paned.sash_place(0, int(top_sash_pos), 0)
                    splitter_restored = True
                    
                if splitter_restored or restored_something:
                    log_message("Window layout restored")
            except Exception as e:
                log_message(f"Window layout restore failed: {e}")
        
        # Schedule splitter restoration after GUI is fully loaded
        root.after(100, restore_splitters)
        
    except Exception as e:
        log_message(f"Could not restore previous window layout: {e}")
        # Final fallback - ensure window is at least visible
        try:
            safe_x, safe_y = get_safe_window_position(1200, 700)
            root.geometry(f"1200x700+{safe_x}+{safe_y}")
            log_message("Applied emergency safe window position")
        except:
            pass

def on_closing():
    """Handle application closing - save state before quitting."""
    save_window_state()
    root.quit()

def open_template_editor():
    """Opens the template editor window."""
    global settings_window
    
    # Check if template editor is already open
    for widget in root.winfo_children():
        if hasattr(widget, 'title') and widget.title() == "Template Editor":
            widget.lift()
            return
    
    template_path = read_config('Settings', 'TemplatePath')
    if not template_path:
        messagebox.showwarning("No Template", "Please set a template file path in Settings first.")
        return
    
    if not os.path.exists(template_path):
        show_error_message("Template Not Found", f"Template file not found:\n{template_path}")
        return
    
    # Create template editor window
    editor_window = Toplevel(root)
    editor_window.title("Template Editor")
    editor_window.config(bg=BG_COLOR)
    center_window(editor_window, 800, 600)
    
    # Template info frame
    info_frame = tk.Frame(editor_window, bg=BG_COLOR)
    info_frame.pack(fill="x", padx=6, pady=5)
    
    tk.Label(info_frame, text=f"Editing: {os.path.basename(template_path)}", 
             bg=BG_COLOR, fg=TEXT_COLOR, font=("Arial", 10, "bold")).pack(side="left")
    
    # Main content frame with horizontal split
    main_frame = tk.Frame(editor_window, bg=BG_COLOR)
    main_frame.pack(fill="both", expand=True, padx=6, pady=5)
    
    # Template text editor (left side)
    text_frame = tk.Frame(main_frame, bg=BG_COLOR)
    text_frame.pack(side="left", fill="both", expand=True)
    
    # Add scrollbar for text
    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side="right", fill="y")
    
    template_text = tk.Text(text_frame, wrap="none", bg=BG_COLOR, fg=TEXT_COLOR, 
                           insertbackground=CURSOR_COLOR, font=("Consolas", 11),
                           yscrollcommand=scrollbar.set)
    template_text.pack(fill="both", expand=True)
    scrollbar.config(command=template_text.yview)
    
    # Variables info frame (right side)
    vars_frame = tk.LabelFrame(main_frame, text="Variables", bg=BG_COLOR, fg=TEXT_COLOR)
    vars_frame.pack(side="right", fill="y", padx=(6, 0))
    
    # Load template content
    try:
        with open(template_path, "r", encoding="utf-8") as file:
            content = file.read()
            template_text.insert("1.0", content)
    except Exception as e:
        show_error_message("Template Load Error", f"Could not load template file:\n{e}")
        editor_window.destroy()
        return
    
    def get_variables_text():
        """Get variables detected in the current template."""
        try:
            # Get current template content
            template_content = get_cached_template_content()
            if not template_content:
                return "No template"
            
            # Extract variables from template
            detected_vars = extract_template_variables(template_content)
            
            if detected_vars:
                var_list = sorted(detected_vars)
                return "\n".join(var_list)
            else:
                return "No variables"
                
        except Exception as e:
            log_message(f"Error detecting variables: {e}")
            return "Error"
    
    # Variables display with proper auto-resizing
    variables_label = tk.Label(vars_frame, text="", bg=BG_COLOR, fg=TEXT_COLOR, 
                              font=("Consolas", 10), justify="left", anchor="nw")
    variables_label.pack(padx=6, pady=8)
    
    # Variables refresh function
    def refresh_variables():
        new_text = get_variables_text()
        variables_label.config(text=new_text)
        
        # Force proper resizing by updating the label and frame
        variables_label.update_idletasks()
        
        # Calculate the required width based on text content
        if new_text:
            lines = new_text.split('\n')
            max_length = max(len(line) for line in lines) if lines else 0
            # Set minimum width based on content (approximate character width)
            min_width = max(120, max_length * 8 + 20)  # 8 pixels per char + padding
            vars_frame.config(width=min_width)
            vars_frame.pack_propagate(False)  # Prevent frame from shrinking
    
    # Buttons frame
    button_frame = tk.Frame(editor_window, bg=BG_COLOR)
    button_frame.pack(fill="x", padx=6, pady=5)
    
    def save_template():
        try:
            content = template_text.get("1.0", "end-1c")
            with open(template_path, "w", encoding="utf-8") as file:
                file.write(content)
            log_message("Template saved successfully")
            # Refresh variables display after saving
            refresh_variables()
        except Exception as e:
            messagebox.showerror("Error", f"Could not save template file:\n{e}", parent=editor_window)
    
    def close_editor():
        editor_window.destroy()
    
    create_standard_button(button_frame, "Close", close_editor).pack(side="right", padx=6)
    create_standard_button(button_frame, "Save", save_template, bg_color="#2d7d32").pack(side="right", padx=6)

    # Keyboard shortcuts
    editor_window.bind('<Control-s>', lambda e: save_template())
    editor_window.bind('<Escape>', lambda e: close_editor())
    
    # Initial refresh to size the variables panel properly
    editor_window.after(100, refresh_variables)

def open_metadata_editor():
    """Opens the metadata editor window for managing key-value pairs."""
    global config_path, metadata_window
    
    # Check if window already exists
    if metadata_window and metadata_window.winfo_exists():
        metadata_window.lift()
        return
    
    log_message("Opening metadata editor")
    
    metadata_window = tk.Toplevel(root)
    metadata_window.title("Metadata Editor")
    metadata_window.config(bg=BG_COLOR)
    center_window(metadata_window, 600, 500)
    
    # Simple focus management
    metadata_window.focus_set()
    
    # Main frame with scrollbar
    main_frame = tk.Frame(metadata_window, bg=BG_COLOR)
    main_frame.pack(fill="both", expand=True, padx=6, pady=10)
    
    # Instructions
    instructions = tk.Label(main_frame, text="Add custom variables for template substitution. Keys must be UPPERCASE.", 
                           bg=BG_COLOR, fg=TEXT_COLOR, font=("Consolas", 10))
    instructions.pack(anchor="w", pady=(0, 10))
    
    # Scrollable frame for metadata entries
    canvas = tk.Canvas(main_frame, bg=BG_COLOR, highlightthickness=0)
    scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=BG_COLOR)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # List to store metadata entry frames
    metadata_entries = []
    loading_metadata = False  # Flag to prevent auto-save during loading
    
    def load_metadata():
        """Load existing metadata from config."""
        nonlocal loading_metadata
        try:
            loading_metadata = True  # Disable auto-save during loading
            
            config = configparser.ConfigParser()
            if os.path.exists(config_path):
                config.read(config_path)
                
                if 'Metadata' in config:
                    loaded_count = 0
                    for key, value in config['Metadata'].items():
                        # Get the variable type if it exists - handle both cases
                        var_type = "Custom"  # Default
                        if 'MetadataTypes' in config:
                            if key in config['MetadataTypes']:
                                var_type = config['MetadataTypes'][key]
                            elif key.upper() in config['MetadataTypes']:
                                var_type = config['MetadataTypes'][key.upper()]
                            elif key.lower() in config['MetadataTypes']:
                                var_type = config['MetadataTypes'][key.lower()]
                        add_metadata_entry(key.upper(), value, var_type)
                        loaded_count += 1
                    
                    if loaded_count > 0:
                        log_message(f"Loaded {loaded_count} metadata entries")
                    else:
                        log_message("No metadata entries found")
                else:
                    log_message("No metadata section found in config")
            else:
                log_message(f"Config file not found: {config_path}")
        except Exception as e:
            log_message(f"Metadata load error: {e}")
            import traceback
            log_message(f"Load error traceback: {traceback.format_exc()}")
        finally:
            loading_metadata = False  # Re-enable auto-save after loading complete
    
    def save_metadata():
        """Save all metadata entries to config."""
        try:
            # Skip saving during loading process
            if loading_metadata:
                return
            # Debug: Check if config_path is set
            if not config_path:
                log_message("ERROR: Config path not set - cannot save")
                return
                
            config = configparser.ConfigParser()
            if os.path.exists(config_path):
                config.read(config_path)
            
            # Clear existing metadata sections
            if 'Metadata' in config:
                config.remove_section('Metadata')
            if 'MetadataTypes' in config:
                config.remove_section('MetadataTypes')
            config.add_section('Metadata')
            config.add_section('MetadataTypes')
            
            # Count entries being saved
            saved_count = 0
            
            # Save all current entries
            for entry_frame, key_var, value_var, type_var in metadata_entries:
                key = key_var.get().strip().upper()
                value = value_var.get().strip()
                var_type = type_var.get()
                if key:  # Only need key to be non-empty
                    config['Metadata'][key] = value
                    config['MetadataTypes'][key] = var_type
                    saved_count += 1
            
            # Write to file
            with open(config_path, 'w') as f:
                config.write(f)
            
            if saved_count > 0:
                log_message(f"Saved {saved_count} metadata entries")
            else:
                log_message("Metadata cleared (no entries to save)")
                
        except Exception as e:
            log_message(f"Metadata save error: {e}")
    
    def add_metadata_entry(key="", value="", var_type="Custom"):
        """Add a new metadata entry row."""

        entry_frame = tk.Frame(scrollable_frame, bg=BG_COLOR)
        entry_frame.pack(fill="x", pady=2)
        
        # Key entry (left side)
        key_var = tk.StringVar(value=key)
        key_entry = tk.Entry(entry_frame, textvariable=key_var, bg="#333333", fg=TEXT_COLOR, 
                            font=("Consolas", 10), width=15)
        key_entry.pack(side="left", padx=(0, 6))
        
        # Equals label
        equals_label = tk.Label(entry_frame, text="=", bg=BG_COLOR, fg=TEXT_COLOR, font=("Consolas", 10))
        equals_label.pack(side="left", padx=2)
        
        # Variable type dropdown
        type_var = tk.StringVar(value=var_type)
        type_options = ["Custom", "File Name", "File Name (no ext)", "Full Date", "Date", "Year"]
        type_combo = ttk.Combobox(entry_frame, textvariable=type_var, values=type_options,
                                 font=("Consolas", 9), width=15, state="readonly")
        type_combo.pack(side="left", padx=6)
        
        # Value entry (middle) - will be enabled/disabled based on type
        value_var = tk.StringVar(value=value)
        value_entry = tk.Entry(entry_frame, textvariable=value_var, bg="#333333", fg=TEXT_COLOR, 
                              font=("Consolas", 10), width=20)
        value_entry.pack(side="left", padx=6)
        
        # Remove button
        remove_btn = tk.Button(entry_frame, text="Remove", bg="#c73e1d", fg="white", 
                              font=("Consolas", 10), padx=6, pady=2, command=lambda: remove_metadata_entry(entry_frame, key_var, value_var, type_var))
        remove_btn.pack(side="right", padx=6)
        
        # Auto-save on value changes and force uppercase on key focus out
        def on_key_focus_out(event):
            """Force uppercase when user finishes editing key."""
            current = key_var.get()
            if current != current.upper():
                key_var.set(current.upper())
            save_metadata()
        
        def on_value_change(*args):
            save_metadata()
            
        def on_type_change(*args):
            """Handle variable type changes."""
            current_type = type_var.get()
            # Disable value entry for auto-generated types
            if current_type in ["File Name", "File Name (no ext)", "Full Date", "Date", "Year"]:
                value_entry.config(state="disabled", bg="#555555")
                value_var.set(f"[Auto: {current_type}]")
            else:
                value_entry.config(state="normal", bg="#333333")
                if value_var.get().startswith("[Auto:"):
                    value_var.set("")  # Clear auto text
            save_metadata()
        
        # Bind events
        key_entry.bind("<FocusOut>", on_key_focus_out)
        key_entry.bind("<Return>", on_key_focus_out)  # Also trigger on Enter key
        value_var.trace_add("write", on_value_change)
        type_var.trace_add("write", on_type_change)
        
        # Initialize the type-based state
        on_type_change()
        
        # Store the entry components
        metadata_entries.append((entry_frame, key_var, value_var, type_var))
        
        # Update canvas scroll region
        metadata_window.after(10, lambda: canvas.configure(scrollregion=canvas.bbox("all")))
    
    def remove_metadata_entry(entry_frame, key_var, value_var, type_var):
        """Remove a metadata entry."""
        # Remove from list
        metadata_entries[:] = [(f, k, v, t) for f, k, v, t in metadata_entries if f != entry_frame]
        # Destroy the frame
        entry_frame.destroy()
        # Save changes
        save_metadata()
        # Update canvas scroll region
        metadata_window.after(10, lambda: canvas.configure(scrollregion=canvas.bbox("all")))
    
    # Bottom buttons frame
    button_frame = tk.Frame(metadata_window, bg=BG_COLOR)
    button_frame.pack(fill="x", padx=6, pady=10)
    
    def parse_tags_from_template():
        """Parse ${} tags from the current template file and create metadata entries."""
        try:
            # Get template path from config
            template_path = read_config('Settings', 'TemplatePath')
            if not template_path:
                template_path = 'hc.fmt'  # Default fallback
            
            if not os.path.exists(template_path):
                # Try to find any .fmt file if the configured one doesn't exist
                fmt_files = []
                for file in os.listdir('.'):
                    if file.endswith('.fmt'):
                        fmt_files.append(file)
                
                if fmt_files:
                    template_path = fmt_files[0]  # Use the first .fmt file found
                    log_message(f"Using template file: {os.path.basename(template_path)}")
                else:
                    messagebox.showerror("Error", f"Template file not found: {template_path}\n\nPlease set a valid template file path in Settings.", parent=metadata_window)
                    return
            
            # Read template file
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all ${} tags using regex
            tags = re.findall(r'\$\{([^}]+)\}', content)
            
            # All tags are custom - convert to uppercase and remove duplicates
            custom_tags = list(set([tag.upper() for tag in tags]))
            
            if custom_tags:
                log_message(f"Found {len(custom_tags)} variables in template")
            
            if not custom_tags:
                messagebox.showinfo("No Tags Found", 
                    f"No ${{}} tags found in the template file.\n\n" +
                    f"Template file: {os.path.basename(template_path)}",
                    parent=metadata_window)
                return
            
            # Show confirmation dialog
            tag_list = '\n'.join([f"${{{tag}}}" for tag in custom_tags])
            result = messagebox.askyesno(
                "Parse Tags from Template", 
                f"Found {len(custom_tags)} custom tags in template:\n\n{tag_list}\n\nThis will overwrite your current metadata list.\nDo you want to continue?",
                icon="warning",
                parent=metadata_window
            )
            
            if result:
                # Clear existing entries
                for entry_frame, key_var, value_var, type_var in metadata_entries[:]:
                    remove_metadata_entry(entry_frame, key_var, value_var, type_var)
                
                # Add new entries for found tags
                for tag in custom_tags:
                    add_metadata_entry(tag, "", "Custom")  # Empty value for user to fill
                
                log_message(f"Created {len(custom_tags)} metadata entries")
                
        except Exception as e:
            log_message(f"Template parsing error: {e}")
            messagebox.showerror("Parse Error", f"Failed to parse template file:\n\n{str(e)}", parent=metadata_window)
    
    add_btn = tk.Button(button_frame, text="Add Entry", bg="#6a4c93", fg="white",
                       font=("Consolas", 10), padx=6, pady=2, command=lambda: add_metadata_entry())
    add_btn.pack(side="left", padx=6)
    
    parse_btn = tk.Button(button_frame, text="Parse from Template", bg="#4a90e2", fg="white", 
                         font=("Consolas", 10), padx=6, pady=2, command=parse_tags_from_template)
    parse_btn.pack(side="left", padx=6)
    
    # Manual save button
    def manual_save():
        save_metadata()
        log_message("Manual save completed")
    
    close_btn = tk.Button(button_frame, text="Close", bg=MENU_COLOR, fg=TEXT_COLOR, 
                         font=("Consolas", 10), padx=6, pady=2, command=metadata_window.destroy)
    close_btn.pack(side="right", padx=6)
    
    save_btn = tk.Button(button_frame, text="Save", bg="#2d7d32", fg="white", 
                        font=("Consolas", 10), padx=6, pady=2, command=manual_save)
    save_btn.pack(side="right", padx=6)
    
    # Load existing metadata
    load_metadata()
    
    # If no entries loaded, add one empty entry
    if not metadata_entries:
        add_metadata_entry()
    

    
    def close_metadata_window():
        """Handle window close event."""
        global metadata_window
        if metadata_window:
            metadata_window.destroy()
            metadata_window = None
    
    metadata_window.protocol("WM_DELETE_WINDOW", close_metadata_window)

# GUI Setup
root = tk.Tk()
root.title("Header Commenter")

# Dark Mode Colors
BG_COLOR = "#1e1e1e"
TEXT_COLOR = "#d4d4d4"
MENU_COLOR = "#333333"
CURSOR_COLOR = "#ffffff"
root.config(bg=BG_COLOR)

# Set initial geometry and center - will be overridden by saved settings if available
root.geometry("1200x700")
center_window_on_screen(root, 1200, 700)

style = ttk.Style()
style.theme_use('default')
style.configure("Treeview", background=BG_COLOR, foreground=TEXT_COLOR, fieldbackground=BG_COLOR)
style.map('Treeview', background=[('selected', '#4a4a4a')], foreground=[('selected', 'white')])

# Main container with vertical splitter
main_paned = tk.PanedWindow(root, orient=tk.VERTICAL, bg=BG_COLOR, sashrelief=tk.RAISED, sashwidth=3)
main_paned.pack(fill="both", expand=True, padx=5, pady=5)

# Top section with horizontal splitter for file tree and content
top_paned = tk.PanedWindow(main_paned, orient=tk.HORIZONTAL, bg=BG_COLOR, sashrelief=tk.RAISED, sashwidth=3)
main_paned.add(top_paned, minsize=300)

# File Tree Panel (Left side, resizable)
tree_frame = tk.Frame(top_paned, bg=BG_COLOR)
top_paned.add(tree_frame, minsize=200)

# Root path label above treeview
root_path_label = tk.Label(tree_frame, text="No directory selected", bg=BG_COLOR, fg=TEXT_COLOR, 
                          font=("Consolas", 9), anchor="w", justify="left")
root_path_label.pack(fill="x", padx=5, pady=(5, 0))

def update_root_path_wrapping(event=None):
    """Update the wraplength of root path label based on current frame width."""
    if root_path_label.winfo_exists():
        frame_width = tree_frame.winfo_width()
        if frame_width > 10:  # Only update if frame has been drawn
            wrap_width = max(100, frame_width - 20)  # Leave some padding
            root_path_label.config(wraplength=wrap_width)

# Bind the wrapping update to frame resize events
tree_frame.bind("<Configure>", update_root_path_wrapping)

def on_file_double_click(event):
    """Handle double-click on a file in the tree view to display its contents."""
    selected_item = file_tree.selection()
    if not selected_item:
        return
    
    # Get the file path from the tree item
    item = selected_item[0]
    item_values = file_tree.item(item, "values")
    if not item_values:
        return  # This is a directory, not a file
    
    file_path = item_values[0]
    display_file_content(file_path)

def template_to_regex_pattern(template_content):
    """Convert template content to a regex pattern, treating ${} tags as wildcards."""
    
    # Escape special regex characters in the template
    escaped = re.escape(template_content)
    
    # Find all variable patterns in the template using compiled regex
    variables = ESCAPED_VAR_PATTERN.findall(escaped)
    
    # Replace escaped ${VARIABLE} patterns with appropriate regex wildcards
    for var in variables:
        var_pattern = r'\\\$\\\{' + re.escape(var) + r'\\\}'
        
        if var.upper() == 'DESCRIPTION':
            # For DESCRIPTION, use a very permissive pattern that captures multiline content
            # Use lazy matching to stop at the next template element or Copyright
            replacement = r'(.*?)'
        else:
            # For other variables, use standard non-greedy match for single line values
            replacement = r'([^\r\n]*?)'
        
        escaped = re.sub(var_pattern, replacement, escaped)
    
    return escaped

def check_template_match(file_content, template_content):
    """Check if the beginning of file_content matches the template pattern."""
    
    if not template_content.strip():
        return False, "No template loaded"
    
    try:
        # Convert template to regex pattern
        pattern = template_to_regex_pattern(template_content)
        
        # Try direct pattern matching against the full file content first
        # This works best when the header format is exact
        match = re.match(pattern, file_content, re.DOTALL | re.MULTILINE)
        
        if not match:
            # If full content match fails, try with just the header portion
            # For multiline descriptions, find the end of the header comment block
            if 'DESCRIPTION' in template_content.upper() or '${DESCRIPTION}' in template_content:
                # Look for the specific comment end pattern from template
                template_end_pattern = r'\*/\s*/\*_{50,}\*/\s*'
                header_end = re.search(template_end_pattern, file_content)
                
                if header_end:
                    file_start = file_content[:header_end.end()]
                else:
                    # Fallback: find any comment block end
                    comment_end = re.search(r'\*/\s*(?:/\*.*?\*/)?', file_content, re.DOTALL)
                    if comment_end:
                        file_start = file_content[:comment_end.end()]
                    else:
                        # Last resort: use first portion of file
                        file_start = file_content[:2000]
            else:
                # For non-description templates, use original logic
                template_lines = template_content.count('\n') + 1
                file_lines = file_content.split('\n')[:template_lines + 2]
                file_start = '\n'.join(file_lines)
            
            # Try matching with the extracted header portion
            match = re.match(pattern, file_start, re.DOTALL | re.MULTILINE)
        
        if match:
            return True, "Template matches header", match.groups()
        else:
            return False, "Header does not match template"
            
    except Exception as e:
        return False, f"Error checking template: {str(e)}"

def get_current_template_content():
    """Get the current template content from the configured template file."""
    return get_cached_template_content()

def get_template_max_line_length(template_content):
    """Get the maximum line length from the template content."""
    if not template_content:
        return 80  # Default fallback
    
    lines = template_content.split('\n')
    max_length = 0
    
    for line in lines:
        # Remove any template variables from line length calculation using compiled regex
        line_without_vars = TEMPLATE_VAR_PATTERN.sub('', line)
        max_length = max(max_length, len(line_without_vars))
    
    return max_length if max_length > 0 else 80

def wrap_description_text(text, max_width):
    """Wrap description text to fit within the specified width."""
    if not text or not text.strip():
        return text
    
    # Split into paragraphs (preserve intentional line breaks)
    paragraphs = text.split('\n\n')
    wrapped_paragraphs = []
    
    for paragraph in paragraphs:
        # Remove existing line breaks within the paragraph
        paragraph = ' '.join(paragraph.split())
        
        if len(paragraph) <= max_width:
            wrapped_paragraphs.append(paragraph)
        else:
            # Wrap the paragraph
            wrapped_lines = textwrap.wrap(paragraph, width=max_width, 
                                        break_long_words=False, 
                                        break_on_hyphens=True)
            wrapped_paragraphs.append('\n'.join(wrapped_lines))
    
    return '\n\n'.join(wrapped_paragraphs)

def create_editable_regions(file_content, template_content, match_groups):
    """Create editable regions for template variables in the text widget."""
    
    # Clear existing tags
    for tag in content_text.tag_names():
        if tag.startswith('editable_'):
            content_text.tag_delete(tag)
    
    # Get template variables in order
    variables = re.findall(r'\$\{([^}]+)\}', template_content)
    
    if len(variables) != len(match_groups):
        return
    
    # Find and tag each variable in the content
    search_start = '1.0'
    for i, (var_name, value) in enumerate(zip(variables, match_groups)):
        # Find the value in the text
        start_pos = content_text.search(value, search_start, tk.END)
        if start_pos:
            end_pos = f"{start_pos}+{len(value)}c"
            
            # Create a tag for this editable region
            tag_name = f'editable_{i}_{var_name.lower()}'
            content_text.tag_add(tag_name, start_pos, end_pos)
            
            # Configure the tag appearance
            content_text.tag_config(tag_name, 
                                  background='#FFFF99',  # Yellow background
                                  foreground='#000000',  # Black text
                                  relief='raised',
                                  borderwidth=1)
            
            # Bind click events to make region editable
            content_text.tag_bind(tag_name, '<Button-1>', 
                                lambda e, start=start_pos, end=end_pos, var=var_name: 
                                enable_region_editing(start, end, var))
            
            # Move search start past this match
            search_start = end_pos
            
            log_message(f"Created editable region for {var_name}: {start_pos} to {end_pos}")

def enable_region_editing(start_pos, end_pos, variable_name):
    """Enable editing for a specific region of text."""
    global current_file_path, editing_region
    
    # Store the region being edited
    editing_region = {'start': start_pos, 'end': end_pos, 'variable': variable_name}
    
    # Get current value from text widget
    current_text_value = content_text.get(start_pos, end_pos)
    
    # Get metadata value and type
    variable_key = variable_name.upper()  # Config uses uppercase keys
    metadata_value = read_config('Metadata', variable_key) or current_text_value
    metadata_type = read_config('MetadataTypes', variable_key) or "Custom"
    
    # If it's an auto-generated type, resolve it to the actual value
    if metadata_value.startswith('[Auto:') and metadata_type != "Custom":
        resolved_value = resolve_variable_value(variable_name, metadata_value, metadata_type, current_file_path)
    else:
        resolved_value = metadata_value
    
    # Special handling for DESCRIPTION - use Text widget for multi-line editing
    is_description = variable_name.upper() == "DESCRIPTION"
    
    # Create a popup widget for editing
    edit_popup = tk.Toplevel(root)
    edit_popup.title(f"Edit {variable_name}")
    
    if is_description:
        edit_popup.geometry("600x320")
        center_window(edit_popup, 600, 320)
    else:
        edit_popup.geometry("520x190")
        center_window(edit_popup, 520, 190)
    
    edit_popup.config(bg=BG_COLOR)  # Dark background for popup
    edit_popup.transient(root)
    edit_popup.grab_set()  # Make it modal
    edit_popup.resizable(False, False)  # Prevent resizing
    
    # Create widgets
    tk.Label(edit_popup, text=f"Editing {variable_name}:", font=("Arial", 11, "bold"), 
            bg=BG_COLOR, fg=TEXT_COLOR).pack(pady=5)
    
    # Show current value info
    info_frame = tk.Frame(edit_popup, bg=BG_COLOR)
    info_frame.pack(pady=2)
    current_display = resolved_value[:60] + ('...' if len(resolved_value) > 60 else '')
    tk.Label(info_frame, text=f"Current: {current_display}", 
             font=("Arial", 9), fg="#888888", bg=BG_COLOR).pack()
    
    # Input widget - Text box for DESCRIPTION, Entry for others
    if is_description:
        # Create frame for text widget with scrollbar
        text_frame = tk.Frame(edit_popup, bg=BG_COLOR)
        text_frame.pack(pady=(5, 10), padx=15, fill="both", expand=True)
        
        # Text widget with scrollbar
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        entry = tk.Text(text_frame, font=("Consolas", 10), height=6, wrap="word",
                       bg=BG_COLOR, fg=TEXT_COLOR, insertbackground=CURSOR_COLOR,
                       selectbackground="#264f78", selectforeground=TEXT_COLOR,
                       yscrollcommand=scrollbar.set)
        entry.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=entry.yview)
        
        entry.insert("1.0", resolved_value)
        entry.focus_set()
        
        def get_entry_value():
            return entry.get("1.0", "end-1c")
    else:
        # Regular entry for other fields
        entry = tk.Entry(edit_popup, font=("Consolas", 10), width=60, 
                        bg=BG_COLOR, fg=TEXT_COLOR, insertbackground=CURSOR_COLOR,
                        selectbackground="#264f78", selectforeground=TEXT_COLOR)
        entry.pack(pady=(5, 10), padx=15, fill="x")
        entry.insert(0, resolved_value)
        entry.select_range(0, tk.END)
        entry.focus_set()
        
        def get_entry_value():
            return entry.get()
    
    # Add separator
    separator = tk.Frame(edit_popup, height=1, bg="#444444")
    separator.pack(fill="x", padx=10, pady=(10, 5))
    
    # Button frame with explicit sizing
    button_frame = tk.Frame(edit_popup, bg=BG_COLOR)
    button_frame.pack(pady=10, fill="x", expand=False)
    
    def save_edit():
        new_value = get_entry_value()
        
        # Apply text wrapping for DESCRIPTION fields based on template's maximum line length
        if is_description:
            template_content = get_current_template_content()
            if template_content:
                max_width = get_template_max_line_length(template_content)
                original_value = new_value
                new_value = wrap_description_text(new_value, max_width)
                
                # Check if wrapping was applied
                if original_value != new_value:
                    log_message(f"Applied text wrapping to fit within {max_width} characters")
        
        # Save to file directly with the entered value
        save_region_edit_with_value(new_value)
        log_message(f"Saved changes to {variable_name}: {new_value}")
        
        # Restore normal status message
        template_status_label.config(text='✅ Template matches - Click highlighted fields to edit', fg="#90EE90")
        
        edit_popup.destroy()
    
    def cancel_edit():
        log_message(f"Cancelled editing {variable_name}")
        
        # Restore normal status message
        template_status_label.config(text='✅ Template matches - Click highlighted fields to edit', fg="#90EE90")
        
        edit_popup.destroy()
    
    # Create styled buttons with hover effects
    cancel_btn = tk.Button(button_frame, text="Cancel", command=cancel_edit,
                          bg="#f44336", fg="white", font=("Consolas", 10),
                          padx=6, pady=2, cursor="hand2")
    cancel_btn.pack(side="right", padx=6)

    save_btn = tk.Button(button_frame, text="Save", command=save_edit, 
                        bg="#4CAF50", fg="white", font=("Consolas", 10), 
                        padx=6, pady=2, cursor="hand2")
    save_btn.pack(side="right", padx=6)
    
    # Force button frame to update and be visible
    button_frame.update_idletasks()
    
    # Handle window close button (X button)
    def on_popup_close():
        log_message(f"Popup closed for {variable_name}")
        # Restore normal status message
        template_status_label.config(text='✅ Template matches - Click highlighted fields to edit', fg="#90EE90")
        edit_popup.destroy()
    
    edit_popup.protocol("WM_DELETE_WINDOW", on_popup_close)
    
    # Bind keys (different for Text vs Entry)
    if is_description:
        # For Text widget, Ctrl+Enter saves, Escape cancels
        entry.bind('<Control-Return>', lambda e: save_edit())
        edit_popup.bind('<Escape>', lambda e: cancel_edit())
    else:
        # For Entry widget, Enter saves, Escape cancels
        entry.bind('<Return>', lambda e: save_edit())
        entry.bind('<Escape>', lambda e: cancel_edit())
        edit_popup.bind('<Escape>', lambda e: cancel_edit())
    
    # Update status
    template_status_label.config(text=f'📝 Editing {variable_name} in popup window')
    
    log_message(f"Opened edit dialog for {variable_name}")

def save_region_edit_with_value(new_value):
    """Save the edited region with a specific value back to the file and update metadata."""
    global current_file_path, editing_region
    
    if not editing_region or not current_file_path:
        return
    
    try:
        # Get the old value from the current text widget
        old_value = content_text.get(editing_region['start'], editing_region['end'])
        
        # Read the entire file
        file_content = safe_read_file(current_file_path)
        if file_content is None:
            log_message("Error: Could not read file for saving edits")
            return
        
        # Replace the old value with the new value in the file content
        new_file_content = file_content.replace(old_value, new_value, 1)
        
        # Write back to file
        if not safe_write_file(current_file_path, new_file_content):
            log_message("Error: Could not write file after editing")
            return
        
        log_message(f"Saved {editing_region['variable']}: '{old_value}' → '{new_value}' to file")
        
        # Refresh the display
        display_file_content(current_file_path)
        
    except Exception as e:
        log_message(f"Error saving edit: {str(e)}")
    
    # Clean up
    cleanup_region_editing()



def cleanup_region_editing():
    """Clean up after region editing."""
    global editing_region
    
    # Clear selection
    try:
        content_text.tag_remove('sel', '1.0', 'end')
    except:
        pass
    
    # Unbind editing keys
    content_text.unbind('<Return>')
    content_text.unbind('<Escape>')
    content_text.unbind('<FocusOut>')
    
    # Make text widget read-only again
    content_text.config(state='disabled')
    
    # Clear editing region
    editing_region = None
    
    # Restore status
    template_status_label.config(text='✅ Template matches - Click highlighted fields to edit')

# Global variable for tracking current editing region
editing_region = None
current_file_path = None

def display_file_content(file_path):
    """Display the contents of a file in the content area."""
    global current_file_path
    current_file_path = file_path
    
    content = safe_read_file(file_path)
    if content is None:
        error_msg = f"Error reading file {os.path.basename(file_path)}"
        log_message(error_msg)
        
        # Update status bar with error info
        file_status_label.config(text=f"❌ {os.path.basename(file_path)}")
        template_status_label.config(text="Read Error", fg="#FFB6C1")
        
        # Disable both buttons on error
        button1.config(state="disabled", bg="#555555")
        button2.config(state="disabled", bg="#555555")
        
        # Show error in content area
        content_text.config(state="normal")
        content_text.delete("1.0", tk.END)
        content_text.insert("1.0", f"Error reading file:\n{error_msg}")
        content_text.config(state="disabled")
        return
    
    try:
        
        # Check if the file matches the template
        template_content = get_current_template_content()
        match_result = check_template_match(content, template_content)
        matches = match_result[0]
        match_status = match_result[1]
        match_groups = match_result[2] if len(match_result) > 2 else None
        
        # Update status bar with file and template match info
        match_indicator = "✅" if matches else "❌"
        file_status_label.config(text=f"📁 {os.path.basename(file_path)}")
        template_status_label.config(text=f"{match_indicator} {match_status}")
        
        # Set status bar colors based on match result
        if matches:
            template_status_label.config(fg="#90EE90")  # Light green for match
            # Disable Insert Header button if template already matches
            button1.config(state="disabled", bg="#555555")
            # Enable Update All Metadata button if template matches
            button2.config(state="normal", bg=MENU_COLOR)
        else:
            template_status_label.config(fg="#FFB6C1")  # Light pink for no match
            # Enable Insert Header button if template doesn't match
            button1.config(state="normal", bg=MENU_COLOR)
            # Disable Update All Metadata button if template doesn't match
            button2.config(state="disabled", bg="#555555")
        
        # Update the content display (just the file content, no metadata)
        content_text.config(state="normal")
        content_text.delete("1.0", tk.END)
        content_text.insert("1.0", content)
        content_text.config(state="disabled")
        
        # If template matches, create editable regions
        if matches and match_groups:
            create_editable_regions(content, template_content, match_groups)
            template_status_label.config(text=f"✅ {match_status} - Click highlighted fields to edit")
        
        # Log the file opening with match status
        log_message(f"Opened file: {os.path.basename(file_path)} - {match_status}")
        
    except Exception as e:
        error_msg = f"Error reading file {os.path.basename(file_path)}: {str(e)}"
        log_message(error_msg)
        
        # Update status bar with error info
        file_status_label.config(text=f"❌ {os.path.basename(file_path)}")
        template_status_label.config(text="Read Error", fg="#FFB6C1")
        
        # Disable both buttons on error
        button1.config(state="disabled", bg="#555555")
        button2.config(state="disabled", bg="#555555")
        
        # Show error in content area
        content_text.config(state="normal")
        content_text.delete("1.0", tk.END)
        content_text.insert("1.0", f"Error reading file:\n{error_msg}")
        content_text.config(state="disabled")

file_tree = ttk.Treeview(tree_frame, show="tree")
file_tree.pack(fill="both", expand=True, padx=5, pady=(2, 5))

# Bind double-click event to open file
file_tree.bind("<Double-1>", on_file_double_click)

# Content area (Right side, resizable)
content_frame = tk.Frame(top_paned, bg=BG_COLOR)
top_paned.add(content_frame, minsize=400)

# Status bar for file info and template match status
status_frame = tk.Frame(content_frame, bg="#404040", height=30, relief="sunken", bd=1)
status_frame.pack(fill="x", pady=(0, 2))
status_frame.pack_propagate(False)  # Maintain fixed height

file_status_label = tk.Label(status_frame, text="No file selected", bg="#404040", fg=TEXT_COLOR, 
                            font=("Consolas", 9), anchor="w")
file_status_label.pack(side="left", padx=10, pady=5)

template_status_label = tk.Label(status_frame, text="", bg="#404040", fg=TEXT_COLOR, 
                               font=("Consolas", 9), anchor="e")
template_status_label.pack(side="right", padx=10, pady=5)

# Button frame below status bar
button_frame = tk.Frame(content_frame, bg=BG_COLOR, height=35)
button_frame.pack(fill="x", pady=(0, 2))
button_frame.pack_propagate(False)  # Maintain fixed height

# Add two buttons
def insert_header_action():
    """Insert template header at the beginning of the current file"""
    global current_file_path
    
    if not current_file_path:
        log_message("No file selected to insert header")
        show_warning_message("No File", "Please select a file first.")
        return
    
    # Get template content
    template_content = get_current_template_content()
    if not template_content:
        log_message("No template available")
        messagebox.showwarning("No Template", "Please configure a template file in Settings first.")
        return
    
    try:
        # Read current file content
        current_content = safe_read_file(current_file_path)
        if current_content is None:
            messagebox.showerror("Read Error", f"Could not read file: {os.path.basename(current_file_path)}")
            return
        
        # Generate header with resolved variables
        resolved_header = resolve_template_variables(template_content, current_file_path)
        
        # Insert header at the beginning
        new_content = resolved_header + "\n" + current_content
        
        # Write back to file
        if not safe_write_file(current_file_path, new_content):
            messagebox.showerror("Write Error", f"Could not write to file: {os.path.basename(current_file_path)}")
            return
        
        log_message(f"Header inserted into {os.path.basename(current_file_path)}")
        
        # Reopen the file to show the changes and enable editing
        display_file_content(current_file_path)
        
    except Exception as e:
        error_msg = f"Error inserting header: {str(e)}"
        log_message(error_msg)
        messagebox.showerror("Insert Error", error_msg)

def update_all_metadata_action():
    """Apply metadata values to the currently opened file by updating the header"""
    global current_file_path
    
    if not current_file_path:
        log_message("No file selected to update metadata")
        show_warning_message("No File", "Please select a file first.")
        return
    
    # Check if file matches template first
    try:
        current_content = safe_read_file(current_file_path)
        if current_content is None:
            messagebox.showerror("Read Error", f"Could not read file: {os.path.basename(current_file_path)}")
            return
        
        template_content = get_current_template_content()
        if not template_content:
            log_message("No template available")
            messagebox.showwarning("No Template", "Please configure a template file in Settings first.")
            return
        
        match_result = check_template_match(current_content, template_content)
        matches = match_result[0]
        match_status = match_result[1]
        if not matches:
            log_message("File doesn't match template - cannot update metadata")
            messagebox.showwarning("Template Mismatch", "File header doesn't match template. Use 'Insert Header' first.")
            return
        
        # Generate updated header with current metadata
        resolved_header = resolve_template_variables(template_content, current_file_path)
        
        # Find the template section in the file and replace it using improved matching
        pattern = template_to_regex_pattern(template_content)
        
        # Try direct pattern matching against the full file content first
        match = re.match(pattern, current_content, re.DOTALL | re.MULTILINE)
        
        if match:
            # Find the end of the matched header
            matched_text = match.group(0)
            remaining_content = current_content[len(matched_text):]
            
            # Replace with updated header
            new_content = resolved_header + remaining_content
            
            # Write back to file
            if not safe_write_file(current_file_path, new_content):
                messagebox.showerror("Write Error", f"Could not write to file: {os.path.basename(current_file_path)}")
                return
            
            log_message(f"Updated metadata in {os.path.basename(current_file_path)}")
            
            # Refresh the display to show changes
            display_file_content(current_file_path)
        else:
            log_message("Could not locate header section for update")
            messagebox.showerror("Update Error", "Could not locate the header section to update.")
            
    except Exception as e:
        error_msg = f"Error updating metadata in file: {str(e)}"
        log_message(error_msg)
        messagebox.showerror("Update Error", error_msg)

def resolve_template_variables(template_content, file_path):
    """Resolve all variables in template content with current values"""
    
    # Find all variables in template using compiled regex
    variables = TEMPLATE_VAR_PATTERN.findall(template_content)
    resolved_content = template_content
    
    for var_name in variables:
        var_key = var_name.upper()
        
        # Get metadata value and type
        metadata_value = read_config('Metadata', var_key)
        metadata_type = read_config('MetadataTypes', var_key) or "Custom"
        
        # Resolve the variable value
        if metadata_value:
            if metadata_value.startswith('[Auto:') and metadata_type != "Custom":
                resolved_value = resolve_variable_value(var_name, metadata_value, metadata_type, file_path)
            else:
                resolved_value = metadata_value
        else:
            # If metadata exists but is empty and Custom type, preserve the existing file value
            if metadata_type == "Custom":
                # Find the current value in the file to preserve it
                try:
                    # Get current file content and extract existing value for this variable
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        current_content = f.read()
                    
                    template_content = get_current_template_content()
                    pattern = template_to_regex_pattern(template_content)
                    
                    # Use improved full-file matching like in check_template_match
                    match = re.match(pattern, current_content, re.DOTALL | re.MULTILINE)
                    if match:
                        # Find which group corresponds to this variable
                        template_vars = TEMPLATE_VAR_PATTERN.findall(template_content)
                        if var_name in template_vars:
                            var_index = template_vars.index(var_name)
                            if var_index < len(match.groups()):
                                existing_value = match.groups()[var_index].strip()
                                # Only preserve non-empty, non-placeholder values
                                if existing_value and not (existing_value.startswith('[') and existing_value.endswith(']')):
                                    resolved_value = existing_value  # Preserve existing value
                                else:
                                    resolved_value = ""  # Empty for missing/placeholder content
                            else:
                                resolved_value = ""  # Empty when index out of bounds
                        else:
                            resolved_value = ""  # Empty when variable not found
                    else:
                        resolved_value = ""  # Empty when pattern doesn't match
                except:
                    resolved_value = ""  # Empty on any error instead of placeholder
            else:
                # Use default resolution for common variables
                if var_name == "CURRENTDATE":
                    resolved_value = resolve_variable_value(var_name, "", "Full Date", file_path)
                elif var_name == "CURRENTYEAR":
                    resolved_value = resolve_variable_value(var_name, "", "Year", file_path)
                elif var_name == "FILENAME":
                    resolved_value = resolve_variable_value(var_name, "", "File Name", file_path)
                else:
                    resolved_value = ""  # Empty for unresolved variables instead of placeholder
        
        # Apply text wrapping for DESCRIPTION fields
        if var_name.upper() == 'DESCRIPTION' and resolved_value:
            template_content_for_width = get_current_template_content()
            if template_content_for_width:
                max_width = get_template_max_line_length(template_content_for_width)
                resolved_value = wrap_description_text(resolved_value, max_width)
        
        # Replace the variable in template
        resolved_content = resolved_content.replace(f"${{{var_name}}}", resolved_value)
    
    return resolved_content

button2 = tk.Button(button_frame, text="Update All Metadata", command=update_all_metadata_action,
                   bg="#555555", fg=TEXT_COLOR, font=("Consolas", 10),
                   padx=6, pady=2, cursor="hand2", state="disabled")
button2.pack(side="right", padx=6)

button1 = tk.Button(button_frame, text="Insert Header", command=insert_header_action,
                   bg="#555555", fg=TEXT_COLOR, font=("Consolas", 10),
                   padx=6, pady=2, cursor="hand2", state="disabled")
button1.pack(side="right", padx=6)

# File content display area
content_text = tk.Text(content_frame, wrap="none", bg=BG_COLOR, fg=TEXT_COLOR, 
                      insertbackground=CURSOR_COLOR, font=("Consolas", 10),
                      state="disabled")
content_scrollbar_v = ttk.Scrollbar(content_frame, orient="vertical", command=content_text.yview)
content_scrollbar_h = ttk.Scrollbar(content_frame, orient="horizontal", command=content_text.xview)
content_text.config(yscrollcommand=content_scrollbar_v.set, xscrollcommand=content_scrollbar_h.set)

# Pack scrollbars and text widget (order matters for proper layout)
content_scrollbar_v.pack(side="right", fill="y")
content_scrollbar_h.pack(side="bottom", fill="x") 
content_text.pack(side="left", fill="both", expand=True)

# Initially show placeholder text
content_text.config(state="normal")
content_text.insert("1.0", "Select a file to view its contents")
content_text.config(state="disabled")

# Logger Area (Bottom, resizable)
logger_frame = tk.LabelFrame(main_paned, text="Log", bg=BG_COLOR, fg=TEXT_COLOR)
main_paned.add(logger_frame, minsize=100)

logger_text = tk.Text(logger_frame, height=8, wrap="word", bg=BG_COLOR, fg=TEXT_COLOR, 
                     insertbackground=CURSOR_COLOR, state="disabled")
logger_text.pack(fill="both", expand=True, padx=5, pady=5)

# Menu Bar
menu = tk.Menu(root, bg=MENU_COLOR, fg=TEXT_COLOR, activebackground="#444", activeforeground="white")
root.config(menu=menu)

# File Menu
file_menu = tk.Menu(menu, tearoff=0, bg=MENU_COLOR, fg=TEXT_COLOR, activebackground="#444", activeforeground="white")
menu.add_cascade(label="File", menu=file_menu)
def open_directory_dialog():
    directory = filedialog.askdirectory(parent=root)
    if directory:
        open_directory(directory)


file_menu.add_command(label="Open Directory", command=open_directory_dialog)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=on_closing)

# Other menu items
menu.add_command(label="Template Editor", command=open_template_editor)
menu.add_command(label="Metadata Editor", command=open_metadata_editor)
menu.add_command(label="Settings", command=open_settings_window)

# Bindings
root.bind('<Control-q>', lambda e: on_closing())

# Set the window close protocol
root.protocol("WM_DELETE_WINDOW", on_closing)

# Initialize config path - check multiple possible locations
def initialize_config():
    global config_path
    
    # First check if there's already a configured folder
    config_folder_from_settings = read_config('Settings', 'ConfigFolder')
    if config_folder_from_settings and os.path.isdir(config_folder_from_settings):
        config_path = os.path.join(config_folder_from_settings, "hc-config.ini")
        return
    
    # Check for hc-config.ini in current directory (preferred name)
    hc_config_path = os.path.join(os.getcwd(), "hc-config.ini")
    if os.path.exists(hc_config_path):
        config_path = hc_config_path
        return
    
    # Check for standard config file in current directory (fallback)
    current_dir_config = os.path.join(os.getcwd(), CONFIG_FILE_NAME)
    if os.path.exists(current_dir_config):
        config_path = current_dir_config
        return
    
    # Default to current directory with preferred name
    config_path = os.path.join(os.getcwd(), "hc-config.ini")

# Initialize configuration and start application
initialize_config()

# Try to open last opened directory
open_last_opened_directory()

# Restore window state after everything is set up
restore_window_state()

# Run the Application
root.mainloop()