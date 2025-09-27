# HeaderCommenter

A modern, optimized GUI desktop application for managing standardized C++ file headers with template-based variable substitution.

Originally designed for DigiPen students but now features extensive customization options making it suitable for any C++ project requiring consistent header formatting.

## ✨ Features

### **Core Functionality**
- **File Tree** - Hierarchical directory view
- **Template-Based Headers** - Customizable `.fmt` template files with variable substitution
- **Live Template Matching** - Real-time detection of existing headers with template validation
- **Interactive Editing** - Click-to-edit highlighted fields in matched templates
- **Multi-line Description Support** - Automatic text wrapping based on template width

### **Advanced Capabilities**
- **Template Editor** - Built-in editor with live variable detection and syntax highlighting
- **Metadata Management** - Visual editor for custom variables with type support (Custom, Date, File Name, etc.)
- **Auto-save Configuration** - Persistent settings with automatic state restoration
- **Multi-Monitor Support** - Intelligent window positioning across multiple displays
- **Performance Optimized** - Cached template loading, compiled regex patterns, efficient file I/O

### **File Support**
- **Extensions**: `.h`, `.hpp`, `.c`, `.cpp`, `.inl`
- **Smart Text Wrapping**: Automatic description wrapping based on template line length
- **Header Validation**: Template matching with support for multiline content

## 🚀 Quick Start

### **Installation**
1. Download the latest release executable
2. Launch `HeaderCommenter_<version>.exe`
3. Configure your template file (Settings → Template File)
4. Set up metadata variables (Metadata Editor)

### **Basic Usage**
1. **Open Directory**: File → Open Directory or `Ctrl+O`
2. **Select File**: Double click any C++ file in the tree view
3. **Edit Headers**: Click highlighted template fields to edit
4. **Insert Headers**: Use "Insert Header" for files without headers
5. **Update Metadata**: Use "Update All Metadata" to refresh existing headers

## 📝 Template System

### **Template Format**
Templates use `${VARIABLE}` syntax for variable substitution.
The included `digipen-gam300.fmt` provides a DigiPen-compatible format:

```cpp
/**
@file    ${FILENAME}
@author  ${EMAIL}
@date    ${CURRENTDATE}

${DESCRIPTION}

Copyright (C) ${CURRENTYEAR} DigiPen Institute of Technology.
Reproduction or disclosure of this file or its contents without the prior
written consent of DigiPen Institute of Technology is prohibited.
*/
```

### **Custom Variables**
Create custom variables in the Metadata Editor:
- **Custom Text**: Static text values
- **File Name**: Dynamic file name insertion
- **Date/Year**: Auto-generated date values

## ⌨️ Keyboard Shortcuts

### **Global**
- `Ctrl+O` - Open directory
- `Ctrl+Q` - Quit application

### **Template Editor**
- `Ctrl+S` - Save template (auto-refreshes variables)
- `Escape` - Close editor

### **Edit Popups**
- `Enter` - Save changes (single-line fields)
- `Ctrl+Enter` - Save changes (multiline descriptions)
- `Escape` - Cancel editing

## 🔧 Building from Source

### **Requirements**
- Python 3.6+
- Standard library modules (tkinter, configparser, re, os, etc.)

### **Build Process**
```bash
# Clone repository
git clone <repository-url>
cd HeaderCommenter

# Run directly
python src/editor.py

# Build executable (Windows)
./build.bat
```

## 📄 License

Licensed under the MIT License. See `LICENSE` file for details.
