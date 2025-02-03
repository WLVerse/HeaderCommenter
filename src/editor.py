import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from datetime import datetime

# Allowed C++ file extensions
CPP_EXTENSIONS = {".h", ".hpp", ".c", ".cpp", ".inl"}

def save_last_opened_directory(directory):
    """Saves the last opened directory to the config file."""
    config_file = "headercommenter-config.txt"
    with open(config_file, "w") as file:
        file.write(directory)

def open_last_opened_directory():
    """Opens the last opened directory from the config file."""
    config_file = "headercommenter-config.txt"
    if os.path.exists(config_file):
        with open(config_file, "r") as file:
            directory = file.read()
            open_directory(directory)

def get_cpp_files(directory):
    """Recursively finds all C++ files and returns them as a list of (fullpath, relative path)."""
    cpp_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1].lower() in CPP_EXTENSIONS:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, directory)
                cpp_files.append((full_path, relative_path))
    return cpp_files

def open_directory(directory):
    """Opens a directory and lists all C++ files in a tree view."""
    file_tree.delete(*file_tree.get_children())  # Clear previous entries
    cpp_files = get_cpp_files(directory)

    if not cpp_files:
        messagebox.showinfo("No Files Found", "No C++ files found in the selected directory.")
        return

    # Insert directories and files into the tree view
    insert_tree_nodes(directory, cpp_files)

    # Store the last opened directory
    save_last_opened_directory(directory)

def insert_tree_nodes(directory, cpp_files):
    """Inserts directories and files into the tree view."""
    file_tree.delete(*file_tree.get_children())  # Clear existing tree
    
    # Create a dictionary to store directory nodes
    dir_nodes = {}
    
    for full_path, relative_path in cpp_files:
        parts = os.path.normpath(relative_path).split(os.sep)
        
        # Handle the file path components
        current_path = ""
        parent_id = ""
        
        # Create/get directory nodes for each level
        for i, part in enumerate(parts[:-1]):  # All parts except the filename
            current_path = os.path.join(current_path, part) if current_path else part
            
            if current_path not in dir_nodes:
                # Create new directory node
                dir_nodes[current_path] = file_tree.insert(parent_id, "end", text=part, open=True)
            
            parent_id = dir_nodes[current_path]
        
        # Insert the file under its parent directory (or root if no parent)
        file_name = parts[-1]
        if parent_id:  # If we have a parent directory
            file_tree.insert(parent_id, "end", text=file_name, values=[full_path])
        else:  # Root level files
            file_tree.insert("", "end", text=file_name, values=[full_path])

def open_selected_file(event):
    """Opens the file selected in the tree view."""
    selected_item = file_tree.selection()
    if selected_item:
        file_info = file_tree.item(selected_item, "values")
        if file_info:
            filepath = file_info[0]  # Get the file path
            open_file(filepath)

def create_header_template(filename=""):
    """Creates the header template with the given filename."""
    current_year = datetime.now().year
    return f"""// Team Name [website]
// {filename}
// 
// Description goes here, will automatically wrap at 80 characters when displaying
// in the editor. You can use multiple lines for the description.
//
// AUTHORS
// [50] First Last (first.l@digipen.edu)
//   - Contribution description point
// [50] First Last (first.l@digipen.edu)
//   - Contribution description point
// 
// Copyright (c) {current_year} DigiPen, All rights reserved.
"""

def wrap_text(text, width=80):
    """Wraps description text at specified width while ensuring all lines are comments."""
    lines = text.split('\n')
    wrapped_lines = []
    
    current_line = ''
    
    for line in lines:
        stripped_line = line.lstrip()
        leading_spaces = line[:len(line) - len(stripped_line)]  # Preserve indentation
        
        # Check if the line is a comment (starts with `//`) or plain text
        if stripped_line.startswith('//'):
            content = stripped_line[2:].strip()  # Remove `//`
        else:
            content = stripped_line.strip()  # Treat it as a comment even if `//` is missing
        
        if content:
            words = content.split()
            for word in words:
                if len(current_line) + len(word) + 1 <= width - len(leading_spaces) - 3:  # -3 for "// "
                    current_line += (word + ' ')
                else:
                    wrapped_lines.append(f"{leading_spaces}// {current_line.strip()}")
                    current_line = word + ' '
            if current_line:
                wrapped_lines.append(f"{leading_spaces}// {current_line.strip()}")
                current_line = ''
        else:
            wrapped_lines.append(leading_spaces + "//")  # Preserve empty comment lines
    
    return '\n'.join(wrapped_lines)

def open_file(filepath):
    """Opens the selected file in the text editor."""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
            
            # Split content into header and code
            lines = content.split('\n')
            header_end = 0
            
            # Find the end of the header comment (look for copyright line)
            for i, line in enumerate(lines):
                if "Copyright (c)" in line:
                    header_end = i + 1
                    break
            
            # Separate header and code
            header = '\n'.join(lines[:header_end])
            code = '\n'.join(lines[header_end:]).strip()
            
            # Parse header content to fill form fields
            parse_header_to_form(header)
            
            # Update header preview
            header_text.delete("1.0", tk.END)
            header_text.insert(tk.END, header)
            
            # Update code area
            code_area.delete("1.0", tk.END)
            code_area.insert(tk.END, code)
            
        root.title(f"Text Editor - {filepath}")
        root.current_file = filepath
        
    except Exception as e:
        messagebox.showerror("Error", f"Could not open file:\n{e}")

def parse_header_to_form(header):
    """Parses the header comment and fills the form fields."""
    # Clear existing authors except the first one
    while len(header_form.author_frames) > 1:
        header_form.remove_author_frame()
    
    lines = header.split('\n')
    description_start = False
    description_end = False
    description_lines = []
    author_count = 1
    current_author = None
    contribution_points_count = 0
    temp_description = ""  # Temporary storage for joining wrapped sentences
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line.startswith('//'):
            continue
            
        # Remove comment marker and trim
        content = line[2:].strip()
        
        # Parse team and website from first line
        if '[' in content and ']' in content and not content.startswith('['):
            team_name = content.split('[')[0].strip()
            website = content.split('[')[1].split(']')[0].strip()
            header_form.team_name.delete(0, tk.END)
            header_form.team_name.insert(0, team_name)
            header_form.website.delete(0, tk.END)
            header_form.website.insert(0, website)
            continue
        
        # Handle description section
        if content == "" and not description_start and not description_end:
            # First empty line after file name, start collecting description
            description_start = True
            continue
        
        # Stop collecting description when we hit AUTHORS
        if content == "AUTHORS":
            description_end = True
            if description_lines and description_lines[-1] == "":
                description_lines.pop()  # Remove extra empty line
            continue
        
        # Collect description lines (joining wrapped sentences)
        if description_start and not description_end:
            if temp_description:
                if temp_description[-1] in ".!?":
                    # If previous sentence ended properly, start a new one
                    description_lines.append(temp_description.strip())
                    temp_description = content
                else:
                    # Otherwise, join it with the next line
                    temp_description += " " + content
            else:
                temp_description = content
            continue
        
        # Parse authors
        if content.startswith('['):
            try:
                # Extract percentage (remove the [] and trim)
                percentage = content[1:].split(']')[0].strip()
                percentage = percentage.replace('%', '')  # Remove % if present
                remaining = content.split(']')[1].strip()
                
                # Extract name and email
                name = remaining.split('(')[0].strip()
                email = remaining.split('(')[1].split('@')[0].strip().replace('\\', '')  # Remove escape character
                
                # Get or create author frame
                if len(header_form.author_frames) < author_count:
                    header_form.add_author_frame()
                
                current_author = header_form.author_frames[-1]
                current_author['contribution'].delete(0, tk.END)
                current_author['contribution'].insert(0, percentage)
                current_author['name'].delete(0, tk.END)
                current_author['name'].insert(0, name)
                current_author['email'].delete(0, tk.END)
                current_author['email'].insert(0, email)
                
                # Clear any existing contribution points
                for point in current_author['contribution_points']:
                    point['frame'].destroy()
                current_author['contribution_points'].clear()

                author_count += 1
            except Exception as e:
                print(f"Error parsing author line: {e}")
                continue
        
        # Parse contribution points
        if content.startswith('-') and current_author is not None:
            desc = content[1:].strip()

            # Add contribution point to the current author
            header_form.add_contribution_point(current_author['points_container'])

            current_author['contribution_points'][-1]['entry'].delete(0, tk.END)
            current_author['contribution_points'][-1]['entry'].insert(0, desc)

            contribution_points_count += 1
    
    # Update description text
    header_form.description.delete("1.0", tk.END)
    if description_lines:
        header_form.description.insert("1.0", '\n'.join(description_lines))

def save_file_with_shortcut(event=None):
    """Saves the content directly to the current file."""
    if hasattr(root, 'current_file'):
        try:
            # Combine header and code with a newline in between
            header_content = header_text.get("1.0", "end-1c")
            code_content = code_area.get("1.0", "end-1c")
            content = f"{header_content}\n\n{code_content}"
            
            with open(root.current_file, "w", encoding="utf-8") as file:
                file.write(content)
            
            messagebox.showinfo("Success", "File saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}")
    else:
        messagebox.showwarning("Warning", "No file is currently open.")

class HeaderForm(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.config(bg=BG_COLOR)
        
        # Store authors frames for dynamic addition/removal
        self.author_frames = []
        
        # Create form fields
        self.create_form_fields()
        
        # Create update button
        update_btn = tk.Button(self, text="Update Header Preview", command=self.update_header_text,
                             bg=MENU_COLOR, fg=TEXT_COLOR)
        update_btn.pack(pady=5)

    def create_form_fields(self):
        # Team Info
        team_frame = tk.Frame(self, bg=BG_COLOR)
        team_frame.pack(fill="x", padx=5, pady=2)
        
        tk.Label(team_frame, text="Team Name:", bg=BG_COLOR, fg=TEXT_COLOR).pack(side="left")
        self.team_name = tk.Entry(team_frame, bg=BG_COLOR, fg=TEXT_COLOR, insertbackground=CURSOR_COLOR)
        self.team_name.pack(side="left", fill="x", expand=True, padx=5)
        self.team_name.bind("<KeyRelease>", lambda e: self.update_header_text)
        
        tk.Label(team_frame, text="Website:", bg=BG_COLOR, fg=TEXT_COLOR).pack(side="left")
        self.website = tk.Entry(team_frame, bg=BG_COLOR, fg=TEXT_COLOR, insertbackground=CURSOR_COLOR)
        self.website.pack(side="left", fill="x", expand=True, padx=5)
        self.website.bind("<KeyRelease>", lambda e: self.update_header_text)

        # Description
        desc_frame = tk.Frame(self, bg=BG_COLOR)
        desc_frame.pack(fill="x", padx=5, pady=2)
        tk.Label(desc_frame, text="Description:", bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor="w")
        self.description = tk.Text(desc_frame, height=4, bg=BG_COLOR, fg=TEXT_COLOR, 
                                 insertbackground=CURSOR_COLOR, wrap="word")
        self.description.pack(fill="x", pady=2)
        self.description.bind("<KeyRelease>", lambda e: self.update_header_text)

        # Authors Section
        self.authors_container = tk.Frame(self, bg=BG_COLOR)
        self.authors_container.pack(fill="x", padx=5, pady=2)
        
        # Add first author by default
        self.add_author_frame()
        
        # Add/Remove author buttons
        btn_frame = tk.Frame(self, bg=BG_COLOR)
        btn_frame.pack(fill="x", padx=5, pady=2)
        tk.Button(btn_frame, text="Add Author", command=self.add_author_frame,
                 bg=MENU_COLOR, fg=TEXT_COLOR).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Remove Author", command=self.remove_author_frame,
                 bg=MENU_COLOR, fg=TEXT_COLOR).pack(side="left")

    def add_contribution_point(self, container):
        point_frame = tk.Frame(container, bg=BG_COLOR)
        point_frame.pack(fill="x", pady=1)
        
        tk.Label(point_frame, text="•", bg=BG_COLOR, fg=TEXT_COLOR).pack(side="left")
        point_entry = tk.Entry(point_frame, bg=BG_COLOR, fg=TEXT_COLOR)
        point_entry.pack(side="left", fill="x", expand=True, padx=5)
        point_entry.bind("<KeyRelease>", lambda e: self.update_header_text)
        
        # Find the corresponding author frame and add this point to their list
        for author in self.author_frames:
            if author['points_container'] == container:
                author['contribution_points'].append({
                    'frame': point_frame,
                    'entry': point_entry
                })
                break

    def remove_contribution_point(self, container):
        for author in self.author_frames:
            if author['points_container'] == container:
                if len(author['contribution_points']) > 1:  # Keep at least one point
                    point_data = author['contribution_points'].pop()
                    point_data['frame'].destroy()
                break

    def add_author_frame(self):
        author_frame = tk.Frame(self.authors_container, bg=BG_COLOR)
        author_frame.pack(fill="x", pady=2)
        
        # Author number label
        tk.Label(author_frame, text=f"Author {len(self.author_frames) + 1}:",
                bg=BG_COLOR, fg=TEXT_COLOR).pack(side="left")
        
        # Author fields container
        fields_frame = tk.Frame(author_frame, bg=BG_COLOR)
        fields_frame.pack(side="left", fill="x", expand=True, padx=5)
        
        # Author info
        top_row = tk.Frame(fields_frame, bg=BG_COLOR)
        top_row.pack(fill="x")
        
        tk.Label(top_row, text="Contribution %:", bg=BG_COLOR, fg=TEXT_COLOR).pack(side="left")
        contribution = tk.Entry(top_row, width=5, bg=BG_COLOR, fg=TEXT_COLOR)
        contribution.pack(side="left", padx=5)
        contribution.bind("<KeyRelease>", lambda e: self.update_header_text)
        
        tk.Label(top_row, text="Name:", bg=BG_COLOR, fg=TEXT_COLOR).pack(side="left")
        name = tk.Entry(top_row, bg=BG_COLOR, fg=TEXT_COLOR)
        name.pack(side="left", fill="x", expand=True, padx=5)
        name.bind("<KeyRelease>", lambda e: self.update_header_text)
        
        tk.Label(top_row, text="Email:", bg=BG_COLOR, fg=TEXT_COLOR).pack(side="left")
        email = tk.Entry(top_row, bg=BG_COLOR, fg=TEXT_COLOR)
        email.pack(side="left", fill="x", expand=True, padx=5)
        email.bind("<KeyRelease>", lambda e: self.update_header_text)
        
        # Contributions container
        contributions_frame = tk.Frame(fields_frame, bg=BG_COLOR)
        contributions_frame.pack(fill="x", pady=2)
        
        # Container for contribution points
        points_container = tk.Frame(contributions_frame, bg=BG_COLOR)
        points_container.pack(fill="x", side="left", expand=True)
        
        # Buttons for managing contribution points
        btn_frame = tk.Frame(contributions_frame, bg=BG_COLOR)
        btn_frame.pack(side="right")
        
        add_point_btn = tk.Button(btn_frame, text="+", command=lambda: self.add_contribution_point(points_container),
                                bg=MENU_COLOR, fg=TEXT_COLOR, width=2)
        add_point_btn.pack(side="left", padx=2)
        
        remove_point_btn = tk.Button(btn_frame, text="-", command=lambda: self.remove_contribution_point(points_container),
                                   bg=MENU_COLOR, fg=TEXT_COLOR, width=2)
        remove_point_btn.pack(side="left", padx=2)
        
        self.author_frames.append({
            'frame': author_frame,
            'contribution': contribution,
            'name': name,
            'email': email,
            'points_container': points_container,
            'contribution_points': []  # Will store the Entry widgets for contribution points
        })

    def remove_author_frame(self):
        if len(self.author_frames) > 1:  # Keep at least one author
            author_data = self.author_frames.pop()
            author_data['frame'].destroy()

    def update_header_text(self):
      """Updates the header text area with the current form values."""
      filename = os.path.basename(root.current_file) if hasattr(root, 'current_file') else "filename.ext"
      year = datetime.now().year
      
      # Build header comment
      header = f"// {self.team_name.get()} [{self.website.get()}]\n"
      header += f"// {filename}\n"
      header += "//\n"
      
      # Add description (wrap at 80 chars)
      desc_text = self.description.get("1.0", tk.END).strip()
      if desc_text:
          # Use the wrap_text function to properly format description
          wrapped_desc = wrap_text(desc_text)
          header += wrapped_desc + "\n"
      header += "//\n"
      
      # Add authors
      header += "// AUTHORS\n"
      for author in self.author_frames:
          contrib = author['contribution'].get().strip()
          name = author['name'].get().strip()
          email = author['email'].get().strip()
          
          # Add author line
          header += f"// [{contrib}%] {name} ({email}\\@digipen.edu)\n"
          
          # Add contribution points
          for point in author['contribution_points']:
              point_text = point['entry'].get().strip()
              if point_text:  # Only add non-empty points
                  header += f"//   - {point_text}\n"
      
      header += "//\n"
      header += f"// Copyright (c) {year} DigiPen, All rights reserved."
      
      # Update header text area
      header_text.delete("1.0", tk.END)
      header_text.insert("1.0", header)

# GUI Setup
root = tk.Tk()
root.title("Header Commenter")
root.geometry("1000x800")

# Dark Mode Colors
BG_COLOR = "#1e1e1e"
TEXT_COLOR = "#d4d4d4"
MENU_COLOR = "#333333"
CURSOR_COLOR = "#ffffff"
FONT = ("Consolas", 12)

# Layout (Tree View + Text Editor)
frame = tk.Frame(root)
frame.pack(fill="both", expand=True)

# File Tree (Left Panel)
tree_frame = tk.Frame(frame, bg=BG_COLOR)
tree_frame.pack(side="left", fill="y")

file_tree = ttk.Treeview(tree_frame)
file_tree.pack(fill="both", expand=True)
file_tree.bind("<Double-1>", open_selected_file)

# Text Editor Frame (Right Panel)
editor_frame = tk.Frame(frame)
editor_frame.pack(side="right", expand=True, fill="both")

# Split editor frame into form and preview sections
header_form_frame = tk.LabelFrame(editor_frame, text="Header Form", bg=BG_COLOR, fg=TEXT_COLOR)
header_form_frame.pack(side="top", fill="x", padx=5, pady=5)

header_form = HeaderForm(header_form_frame)
header_form.pack(fill="x", padx=5, pady=5)

header_preview_frame = tk.LabelFrame(editor_frame, text="Header Preview", bg=BG_COLOR, fg=TEXT_COLOR)
header_preview_frame.pack(side="top", fill="x", padx=5, pady=5)

header_text = tk.Text(header_preview_frame, height=15, wrap="word", font=FONT, 
                     bg=BG_COLOR, fg=TEXT_COLOR, insertbackground=CURSOR_COLOR)
header_text.pack(fill="x", padx=5, pady=5)

# Code Area (Bottom)
code_frame = tk.LabelFrame(editor_frame, text="Code", bg=BG_COLOR, fg=TEXT_COLOR)
code_frame.pack(side="bottom", fill="both", expand=True, padx=5, pady=5)

code_area = tk.Text(code_frame, wrap="word", font=FONT, bg=BG_COLOR, fg=TEXT_COLOR, 
                   insertbackground=CURSOR_COLOR)
code_area.pack(fill="both", expand=True, padx=5, pady=5)

# Menu Bar
menu = tk.Menu(root, bg=MENU_COLOR, fg=TEXT_COLOR, activebackground="#444", activeforeground="white")
root.config(menu=menu)
menu.add_command(label="Open Directory", command=lambda: open_directory(filedialog.askdirectory()))
menu.add_command(label="Save", command=save_file_with_shortcut)
menu.add_command(label="Quit", command=root.quit)

# Bind Ctrl+Q to quit
root.bind('<Control-q>', lambda e: root.quit())

# Bind Ctrl+O to open file
root.bind('<Control-o>', lambda e: open_file(filedialog.askopenfilename))

# Bind Ctrl+S to save
root.bind('<Control-s>', save_file_with_shortcut)

# Bind Enter key to update header preview
root.bind('<Return>', lambda e: header_form.update_header_text)

# try to open the last opened directory
open_last_opened_directory()

# Run the Application
root.mainloop()