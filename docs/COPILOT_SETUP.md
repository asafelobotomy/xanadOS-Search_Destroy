# Copilot Instructions Setup

This project uses GitHub Copilot with custom instructions to ensure consistent coding practices and adherence to project standards.

## How It Works

### 1. Main Instructions File

- **Location**: `.copilot-instructions.md` (in the project root)
- **Purpose**: Contains all coding standards, best practices, and project-specific rules
- **Format**: Standard Markdown for easy reading and editing

### 2. VS Code Integration

- **Settings**: `.vscode/settings.json` configures Copilot behavior
- **Tasks**: `.vscode/tasks.json` provides quick access to view instructions
- **Workspace**: `xanadOS-Search_Destroy.code-workspace` for workspace-level settings

## Using the Instructions

### Quick Access
1. **Command Palette**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Show Copilot Instructions"
2. **Terminal**: `cat .copilot-instructions.md`
3. **Direct Edit**: Open `.copilot-instructions.md` in VS Code

### How Copilot Reads Instructions
- Copilot automatically reads `.copilot-instructions.md` when present in the project root
- Instructions are applied context-aware during code generation
- The file is referenced during chat conversations for consistent responses

### Customization
To modify instructions for this project:
1. Edit `.copilot-instructions.md`
2. Follow the existing structure (Rules, Directory Structure, Resources)
3. Test changes by asking Copilot to perform a simple task

## File Structure
```
.copilot-instructions.md          # Main Copilot instructions
.vscode/
  ├── settings.json              # VS Code + Copilot settings
  ├── tasks.json                 # Quick access tasks
  └── ...
xanadOS-Search_Destroy.code-workspace        # Workspace configuration
```

## Tips for Effective Use

1. **Be Specific**: The more detailed your instructions, the better Copilot follows them
2. **Use Examples**: Include code examples in instructions when possible
3. **Test Regularly**: Verify Copilot is following your guidelines
4. **Version Control**: Keep instructions in Git to track changes
5. **Team Sync**: Ensure all team members understand the instruction format

## Troubleshooting

### Copilot Not Following Instructions
1. Check file exists: `.copilot-instructions.md`
2. Verify VS Code settings are correct
3. Restart VS Code to reload settings
4. Use the "Show Copilot Instructions" task to confirm content

### Instructions Not Loading
1. Ensure GitHub Copilot extension is installed and enabled
2. Check VS Code settings for `github.copilot.enable`
3. Verify file permissions and encoding (should be UTF-8)

## Best Practices

- **Keep Updated**: Review and update instructions regularly
- **Stay Consistent**: Follow the same format across all projects
- **Document Changes**: Update `CHANGELOG.md` when modifying instructions
- **Collaborate**: Get team input on instruction changes
- **Test Impact**: Verify instruction changes work as expected
