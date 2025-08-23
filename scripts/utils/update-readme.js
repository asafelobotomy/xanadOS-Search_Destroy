#!/usr/bin/env node

/**
 * Automated README Generator for GitHub Copilot Enhancement Framework
 * Based on patterns from github/awesome-copilot
 */

const fs = require('fs');
const path = require('path');

// Configuration
const REPO_BASE_URL = "https://raw.githubusercontent.com/YOUR_ORG/YOUR_REPO/main";
const VSCODE_BASE_URL = "https://vscode.dev/redirect?url=";
const VSCODE_INSIDERS_BASE_URL = "https://insiders.vscode.dev/redirect?url=";

const VSCODE_INSTALL_BADGE = "https://img.shields.io/badge/VS_Code-Install-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white";
const VSCODE_INSIDERS_INSTALL_BADGE = "https://img.shields.io/badge/VS_Code_Insiders-Install-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white";

/**
 * Generate install URLs for a file
 */
function generateInstallUrls(filePath, fileType) {
  const encodedPath = encodeURIComponent(`${REPO_BASE_URL}/${filePath}`);

  let vscodeUrl, vscodeInsidersUrl;

  switch (fileType) {
    case 'chatmode':
      vscodeUrl = `${VSCODE_BASE_URL}vscode%3Achat-mode%2Finstall%3Furl%3D${encodedPath}`;
      vscodeInsidersUrl = `${VSCODE_INSIDERS_BASE_URL}vscode-insiders%3Achat-mode%2Finstall%3Furl%3D${encodedPath}`;
      break;
    case 'prompt':
      vscodeUrl = `${VSCODE_BASE_URL}vscode%3Achat-prompt%2Finstall%3Furl%3D${encodedPath}`;
      vscodeInsidersUrl = `${VSCODE_INSIDERS_BASE_URL}vscode-insiders%3Achat-prompt%2Finstall%3Furl%3D${encodedPath}`;
      break;
    case 'instructions':
      vscodeUrl = `${VSCODE_BASE_URL}vscode%3Achat-instructions%2Finstall%3Furl%3D${encodedPath}`;
      vscodeInsidersUrl = `${VSCODE_INSIDERS_BASE_URL}vscode-insiders%3Achat-instructions%2Finstall%3Furl%3D${encodedPath}`;
      break;
    default:
      throw new Error(`Unknown file type: ${fileType}`);
  }

  return {
    vscode: vscodeUrl,
    vscodeInsiders: vscodeInsidersUrl
  };
}

/**
 * Generate badge markdown
 */
function generateBadges(urls) {
  return `[![Install in VS Code](${VSCODE_INSTALL_BADGE})](${urls.vscode})<br />[![Install in VS Code Insiders](${VSCODE_INSIDERS_INSTALL_BADGE})](${urls.vscodeInsiders})`;
}

/**
 * Extract frontmatter from a file
 */
function extractFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return {};

  const frontmatter = {};
  const lines = match[1].split('\n');

  for (const line of lines) {
    const colonIndex = line.indexOf(':');
    if (colonIndex > 0) {
      const key = line.substring(0, colonIndex).trim();
      const value = line.substring(colonIndex + 1).trim().replace(/^['"]|['"]$/g, '');
      frontmatter[key] = value;
    }
  }

  return frontmatter;
}

/**
 * Process files in a directory
 */
function processDirectory(dirPath, fileType, extension) {
  if (!fs.existsSync(dirPath)) {
    console.log(`Directory ${dirPath} not found`);
    return [];
  }

  const files = fs.readdirSync(dirPath)
    .filter(file => file.endsWith(`.${extension}.md`))
    .map(file => {
      const filePath = path.join(dirPath, file);
      const content = fs.readFileSync(filePath, 'utf8');
      const frontmatter = extractFrontmatter(content);
      const title = frontmatter.title || frontmatter.description || file.replace(`.${extension}.md`, '');
      const description = frontmatter.description || 'No description available';

      const relativePath = `${dirPath}/${file}`;
      const urls = generateInstallUrls(relativePath, fileType);
      const badges = generateBadges(urls);

      return {
        file,
        title,
        description,
        badges,
        priority: frontmatter.priority || 50,
        category: frontmatter.category || 'General',
        model: frontmatter.model || '',
        reasoning: frontmatter.reasoning || '',
        specialized_for: frontmatter.specialized_for || ''
      };
    });

  // Sort by priority (higher first) then by title
  return files.sort((a, b) => {
    if (b.priority !== a.priority) {
      return b.priority - a.priority;
    }
    return a.title.localeCompare(b.title);
  });
}

/**
 * Generate table for files
 */
function generateTable(files) {
  if (files.length === 0) return 'No files found.';

  let table = '| Title | Description | Model | Install |\n';
  table += '| ----- | ----------- | ----- | ------- |\n';

  for (const file of files) {
    const modelInfo = file.model || 'General';
    table += `| [${file.title}](${file.file}) | ${file.description} | ${modelInfo} | ${file.badges} |\n`;
  }

  return table;
}

/**
 * Generate the main README content
 */
function generateReadme() {
  const chatmodes = processDirectory('.github/chatmodes', 'chatmode', 'chatmode');
  const prompts = processDirectory('.github/prompts', 'prompt', 'prompt');
  const instructions = processDirectory('.github/instructions', 'instructions', 'instructions');

  const readme = `# GitHub Copilot Enhancement Framework

## Project Overview

This repository provides a comprehensive GitHub Copilot enhancement framework that enables organizations to create, validate, and deploy custom Copilot instructions at scale. The framework includes chat modes, prompts, validation systems, and automation tools.

## Quick Start

### Installation

1. **Clone the repository:**
   \`\`\`bash
   git clone https://github.com/YOUR_ORG/YOUR_REPO.git
   cd YOUR_REPO
   \`\`\`

2. **Set up VS Code:**
   - Install recommended extensions from \`.vscode/extensions.json\`
   - VS Code settings are automatically configured for optimal Copilot experience

3. **Install components:**
   - Click the VS Code install buttons below for direct installation
   - Or manually copy files to your workspace

## 🧩 Custom Chat Modes

Chat modes define specific behaviors and tools for GitHub Copilot Chat, enabling enhanced context-aware assistance for particular tasks or workflows.

### How to Use Custom Chat Modes

**To Install:**
- Click the **VS Code** or **VS Code Insiders** install button for the chat mode you want to use
- Download the \`*.chatmode.md\` file and manually install it in VS Code using the Command Palette

**To Activate/Use:**
- Import the chat mode configuration into your VS Code settings
- Access the installed chat modes through the VS Code Chat interface
- Select the desired chat mode from the available options in VS Code Chat

${generateTable(chatmodes)}

## 🎯 Reusable Prompts

Ready-to-use prompt templates for specific development scenarios and tasks, defining prompt text with a specific mode, model, and available set of tools.

### How to Use Reusable Prompts

**To Install:**
- Click the **VS Code** or **VS Code Insiders** install button for the prompt you want to use
- Download the \`*.prompt.md\` file and manually add it to your prompt collection

**To Run/Execute:**
- Use \`/prompt-name\` in VS Code chat after installation
- Run the \`Chat: Run Prompt\` command from the Command Palette
- Hit the run button while you have a prompt file open in VS Code

${generateTable(prompts)}

## 📋 Custom Instructions

Team and project-specific instructions to enhance GitHub Copilot's behavior for specific technologies and coding practices.

### How to Use Custom Instructions

**To Install:**
- Click the **VS Code** or **VS Code Insiders** install button for the instruction you want to use
- Download the \`*.instructions.md\` file and manually add it to your project's instruction collection

**To Use/Apply:**
- Copy these instructions to your \`.github/copilot-instructions.md\` file in your workspace
- Create task-specific \`.github/.instructions.md\` files in your workspace's \`.github/instructions\` folder
- Instructions automatically apply to Copilot behavior once installed in your workspace

${generateTable(instructions)}

## 🛠️ Development Configuration

This repository uses various configuration files to ensure consistent code style and optimal VS Code integration:

- [\`.editorconfig\`](.editorconfig) - Defines coding styles across different editors and IDEs
- [\`.gitattributes\`](.gitattributes) - Ensures consistent line endings in text files
- [\`.vscode/settings.json\`](.vscode/settings.json) - Enhanced VS Code settings for Copilot integration
- [\`.vscode/extensions.json\`](.vscode/extensions.json) - Recommended VS Code extensions

### VS Code Features

- **Enhanced Chat Integration**: Direct model selection and command center
- **Prompt Files Support**: \`"chat.promptFiles": true\` enables attachment in VS Code chat
- **File Associations**: Automatic markdown preview for Copilot files
- **Optimized Settings**: Configured for best Copilot experience

## 📚 Additional Resources

- [VS Code Copilot Customization Documentation](https://code.visualstudio.com/docs/copilot/copilot-customization) - Official Microsoft documentation
- [GitHub Copilot Chat Documentation](https://code.visualstudio.com/docs/copilot/chat/copilot-chat) - Complete chat feature guide
- [Custom Chat Modes](https://code.visualstudio.com/docs/copilot/chat/chat-modes) - Advanced chat configuration
- [GitHub Awesome Copilot](https://github.com/github/awesome-copilot) - Official GitHub repository for Copilot customizations

## 🚀 Advanced Features

### Model Targeting
Many templates support model-specific features:
- **GPT-4.1**: Advanced reasoning for complex architectural decisions
- **GPT-4**: Standard model for most development tasks
- **Agent Mode**: Autonomous operation with comprehensive tool access

### Tool Integration
Templates include sophisticated tool configurations:
- **Codebase Analysis**: \`codebase\`, \`search\`, \`usages\`, \`findTestFiles\`
- **Development**: \`editFiles\`, \`runCommands\`, \`runTasks\`, \`runTests\`
- **External Resources**: \`fetch\`, \`githubRepo\`, \`openSimpleBrowser\`
- **VS Code Integration**: \`vscodeAPI\`, \`extensions\`, \`problems\`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to submit new instructions, prompts, and chat modes.

---

> 💡 **Pro Tip:** Custom instructions only affect Copilot Chat (not inline code completions). You can combine all three customization types - use custom instructions for general guidelines, prompt files for specific tasks, and chat modes to control the interaction context.
`;

  return readme;
}

// Main execution
if (require.main === module) {
  try {
    const readmeContent = generateReadme();
    fs.writeFileSync('README.md', readmeContent);
    console.log('✅ README.md generated successfully');
    console.log('📝 Remember to update repository URLs in the configuration');
  } catch (error) {
    console.error('❌ Error generating README:', error.message);
    process.exit(1);
  }
}

module.exports = {
  generateReadme,
  generateInstallUrls,
  generateBadges,
  extractFrontmatter,
  processDirectory,
  generateTable
};
