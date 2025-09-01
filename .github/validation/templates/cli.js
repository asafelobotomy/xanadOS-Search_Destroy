#!/usr/bin/env node

/**
 * Template Validation CLI
 * Command-line interface for the template validation system
 */

import { program } from 'commander';
import { TemplateValidationSystem } from './template-validation-system.js';
import { promises as fs } from 'fs';
import { join } from 'path';
import chalk from 'chalk';

program
  .name('template-validator')
  .description('Comprehensive template validation for GitHub Copilot instructions')
  .version('1.0.0');

program
  .command('validate')
  .description('Run template validation')
  .option('-c, --config <path>', 'Path to validation configuration file')
  .option('-o, --output <dir>', 'Output directory for reports')
  .option('-f, --format <format>', 'Report format (json, markdown, both)', 'both')
  .option('-s, --strict', 'Enable strict validation mode')
  .option('-v, --verbose', 'Enable verbose output')
  .option('--no-integration', 'Skip integration tests')
  .option('--no-performance', 'Skip performance tests')
  .action(async (options) => {
    try {
      console.log(chalk.blue('🔧 GitHub Copilot Template Validation System\n'));

      // Load configuration
      const config = await loadConfiguration(options.config);

      // Override config with CLI options
      if (options.output) config.validation.outputDirectory = options.output;
      if (options.format) config.validation.reportFormat = options.format;
      if (options.strict) config.validation.strictMode = true;
      if (options.noIntegration) config.integration.enabled = false;
      if (options.noPerformance) config.performance.enabled = false;

      // Create validation system
      const validator = new TemplateValidationSystem({
        rootPath: process.cwd(),
        config: config,
        verbose: options.verbose
      });

      // Run validation
      const result = await validator.validateTemplateSystem();

      if (result.success) {
        console.log(chalk.green('\n✅ Template validation completed successfully!'));
        process.exit(0);
      } else {
        console.log(chalk.red('\n❌ Template validation failed!'));
        process.exit(1);
      }

    } catch (error) {
      console.error(chalk.red('❌ Validation error:'), error.message);
      if (options.verbose) {
        console.error(error.stack);
      }
      process.exit(1);
    }
  });

program
  .command('init')
  .description('Initialize template validation configuration')
  .option('-o, --output <dir>', 'Output directory for configuration', '.github/validation/templates')
  .action(async (options) => {
    try {
      console.log(chalk.blue('🔧 Initializing template validation configuration...\n'));

      const configDir = options.output;
      const configFile = join(configDir, 'validation-config.json');

      // Create directory if it doesn't exist
      await fs.mkdir(configDir, { recursive: true });

      // Check if config already exists
      try {
        await fs.access(configFile);
        console.log(chalk.yellow('⚠️  Configuration file already exists:'), configFile);
        console.log('Use --force to overwrite');
        return;
      } catch (error) {
        // File doesn't exist, continue
      }

      // Create default configuration
      const defaultConfig = await getDefaultConfiguration();
      await fs.writeFile(configFile, JSON.stringify(defaultConfig, null, 2));

      console.log(chalk.green('✅ Configuration initialized:'), configFile);
      console.log(chalk.blue('Next steps:'));
      console.log('  1. Review and customize the configuration');
      console.log('  2. Run validation: template-validator validate');

    } catch (error) {
      console.error(chalk.red('❌ Initialization error:'), error.message);
      process.exit(1);
    }
  });

program
  .command('check')
  .description('Quick validation check without full reports')
  .option('-t, --type <type>', 'Template type to check (chat-mode, prompt, mcp-server, documentation)')
  .option('-f, --file <path>', 'Specific file to validate')
  .action(async (options) => {
    try {
      console.log(chalk.blue('🔍 Quick template validation check...\n'));

      const validator = new TemplateValidationSystem({
        rootPath: process.cwd(),
        quickCheck: true
      });

      let files = [];

      if (options.file) {
        files = [options.file];
      } else {
        files = await validator.discoverTemplateFiles();

        if (options.type) {
          files = files.filter(file =>
            validator.determineTemplateType(file, '') === options.type
          );
        }
      }

      console.log(chalk.gray(`Checking ${files.length} file(s)...`));

      let errors = 0;
      let warnings = 0;

      for (const file of files) {
        const result = await validator.validateTemplateStructure(file);

        if (result.errors > 0) {
          console.log(chalk.red('❌'), file.replace(process.cwd() + '/', ''));
          errors += result.errors;
        } else if (result.warnings > 0) {
          console.log(chalk.yellow('⚠️ '), file.replace(process.cwd() + '/', ''));
          warnings += result.warnings;
        } else {
          console.log(chalk.green('✅'), file.replace(process.cwd() + '/', ''));
        }
      }

      console.log(chalk.blue('\nSummary:'));
      console.log(`  Files checked: ${files.length}`);
      console.log(`  Errors: ${errors}`);
      console.log(`  Warnings: ${warnings}`);

      if (errors > 0) {
        console.log(chalk.red('\nRun full validation for detailed error information.'));
        process.exit(1);
      } else {
        console.log(chalk.green('\n✅ Quick check completed successfully!'));
        process.exit(0);
      }

    } catch (error) {
      console.error(chalk.red('❌ Check error:'), error.message);
      process.exit(1);
    }
  });

program
  .command('report')
  .description('Generate validation report from existing results')
  .option('-i, --input <dir>', 'Input directory with validation results')
  .option('-o, --output <file>', 'Output file for the report')
  .option('-f, --format <format>', 'Report format (json, markdown)', 'markdown')
  .action(async (options) => {
    try {
      console.log(chalk.blue('📊 Generating validation report...\n'));

      // Implementation for generating reports from existing data
      console.log(chalk.yellow('📋 Report generation functionality coming soon...'));

    } catch (error) {
      console.error(chalk.red('❌ Report error:'), error.message);
      process.exit(1);
    }
  });

async function loadConfiguration(configPath) {
  const defaultConfigPath = join(process.cwd(), '.github/validation/templates/validation-config.json');
  const targetPath = configPath || defaultConfigPath;

  try {
    const configContent = await fs.readFile(targetPath, 'utf8');
    return JSON.parse(configContent);
  } catch (error) {
    if (configPath) {
      throw new Error(`Could not load configuration from ${configPath}: ${error.message}`);
    }

    // Return default configuration if no config file found
    console.log(chalk.yellow('⚠️  No configuration file found, using defaults'));
    return await getDefaultConfiguration();
  }
}

async function getDefaultConfiguration() {
  return {
    validation: {
      enabled: true,
      strictMode: false,
      reportFormat: "both",
      outputDirectory: ".github/validation/reports/templates"
    },
    templates: {
      searchPaths: [
        ".github/chatmodes",
        ".github/prompts",
        ".github/mcp",
        ".github/validation"
      ],
      fileExtensions: [".md", ".json"],
      excludePatterns: [
        "**/node_modules/**",
        "**/reports/**",
        "**/.git/**"
      ]
    },
    contentStandards: {
      accessibility: {
        enabled: true,
        minimumScore: 0.8
      },
      formatting: {
        enabled: true,
        minimumScore: 0.8
      },
      style: {
        enabled: true,
        minimumScore: 0.7
      },
      internationalization: {
        enabled: true,
        minimumScore: 0.8
      }
    },
    integration: {
      enabled: true,
      testMCPServers: true,
      testChatModes: true,
      testTemplateGeneration: true,
      testEndToEndWorkflows: true,
      timeout: 30000
    },
    performance: {
      enabled: true,
      maxProcessingTime: 100,
      minThroughput: 5
    },
    reporting: {
      includeDetails: true,
      includeRecommendations: true,
      includePerformanceMetrics: true,
      generateSummary: true
    }
  };
}

// Handle uncaught errors
process.on('uncaughtException', (error) => {
  console.error(chalk.red('💥 Uncaught exception:'), error.message);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error(chalk.red('💥 Unhandled rejection:'), reason);
  process.exit(1);
});

program.parse();
