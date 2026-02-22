#!/usr/bin/env node
'use strict';

/**
 * CLI entry point for @thecodesaiyan/claude-dev-workflow-hook
 *
 * Usage:
 *   npx @thecodesaiyan/claude-dev-workflow-hook --global
 *   npx @thecodesaiyan/claude-dev-workflow-hook --project
 *   npx @thecodesaiyan/claude-dev-workflow-hook --uninstall --scope global
 */

const { install, getClaudeHome, getProjectClaude } = require('../src/installer.js');
const { uninstall } = require('../src/uninstaller.js');
const { bold } = require('../src/utils.js');

function printUsage() {
  console.log(bold('Claude Code Development Workflow Hook'));
  console.log('');
  console.log('Usage:');
  console.log('  npx @thecodesaiyan/claude-dev-workflow-hook --global     Install globally (~/.claude/)');
  console.log('  npx @thecodesaiyan/claude-dev-workflow-hook --project    Install in current project (.claude/)');
  console.log('  npx @thecodesaiyan/claude-dev-workflow-hook --uninstall --scope global');
  console.log('  npx @thecodesaiyan/claude-dev-workflow-hook --uninstall --scope project');
  console.log('  npx @thecodesaiyan/claude-dev-workflow-hook --help       Show this help');
}

function parseArgs(argv) {
  const args = argv.slice(2);
  const result = {
    global: false,
    project: false,
    uninstall: false,
    scope: null,
    help: false,
  };

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--global':
        result.global = true;
        break;
      case '--project':
        result.project = true;
        break;
      case '--uninstall':
        result.uninstall = true;
        break;
      case '--scope':
        result.scope = args[++i];
        break;
      case '--help':
      case '-h':
        result.help = true;
        break;
      default:
        console.error(`Unknown argument: ${args[i]}`);
        printUsage();
        process.exit(1);
    }
  }

  return result;
}

function main() {
  const args = parseArgs(process.argv);

  if (args.help) {
    printUsage();
    process.exit(0);
  }

  console.log(bold('Claude Code Development Workflow Hook'));
  console.log(`Node.js: ${process.version} | Platform: ${process.platform}`);

  if (args.uninstall) {
    if (!args.scope) {
      console.error('Error: --uninstall requires --scope (global or project)');
      printUsage();
      process.exit(1);
    }
    if (!['global', 'project'].includes(args.scope)) {
      console.error(`Error: --scope must be 'global' or 'project', got: '${args.scope}'`);
      process.exit(1);
    }
    const targetDir = args.scope === 'global' ? getClaudeHome() : getProjectClaude();
    uninstall(targetDir);
    return;
  }

  if (args.global && args.project) {
    console.error('Error: --global and --project are mutually exclusive');
    process.exit(1);
  }

  if (!args.global && !args.project) {
    console.error('Error: specify --global or --project');
    printUsage();
    process.exit(1);
  }

  const scopeIsGlobal = args.global;
  const targetDir = scopeIsGlobal ? getClaudeHome() : getProjectClaude();
  install(targetDir, scopeIsGlobal);
}

main();
