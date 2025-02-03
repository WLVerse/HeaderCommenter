# HeaderCommenter
A GUI desktop application to quickly edit header comments in a repo.

This is currently designed specifically for DigiPen students. More customization options will be added in the future to generify it.

## Features
- File tree that accurately represents the directory structure.
- Custom GUI to edit each field in the file header.
- Supports h, hpp, c, cpp, inl files.
- Reopens the last open directory when opening the app.

## How to use
- Launch the exe.
- Open your source repo using [Ctrl + O] or click the "Open directory" button.
- Browse the file tree on the left for the file you want to edit, double click the file to open it.
- Edit the text fields on the top third and press [Enter] or click the "Update Header Preview" button.
- Save the header using [Ctrl + S] or click the "Save" button.
- Enjoy!

## Supported keybinds
- [Ctrl + O] Open directory
- [Ctrl + S] Save currently open file
- [Ctrl + Q] Quit application (will not save)

## Todo list
- Write your own custom formats
- Set default values for all editable fields in the header

## Default File Header Format
```cpp
// Team Name [https://websitelink.web.app]
// filename.ext
// 
// A description of the what the file does.
//
// AUTHORS
// [70%] Full Name (email\@digipen.edu)
//   - Main Author
//   - Contributions
// [30%] Full Name (email\@digipen.edu)
//   - Contributions
// 
// Copyright (c) Year DigiPen, All rights reserved.
```