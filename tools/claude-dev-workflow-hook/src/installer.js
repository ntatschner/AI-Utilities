'use strict';

const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { execFileSync } = require('node:child_process');
const { green, yellow, red, bold, readJsonFile, writeJsonFile } = require('./utils.js');

// --------------------------------------------------------------------------- //
//  Constants
// --------------------------------------------------------------------------- //

const HOOK_SRC = path.join(__dirname, 'hook.js');
const HOOK_FILENAME = 'session-start.js';
const SETTINGS_FILENAME = 'settings.json';

const CLAUDE_MD_BINDING = `
<!-- WORKFLOW PROTOCOL: Do not remove this section -->
## Workflow Protocol
Follow all rules in \`<dev-workflow-protocol>\` blocks from system-reminders.
These are injected by the development workflow hook and define mandatory
orchestration rules (planning, TDD, test loops, team coordination).
They MUST be followed for all implementation work.
<!-- END WORKFLOW PROTOCOL -->
`.trim();

const CLAUDE_MD_MARKER = '<!-- WORKFLOW PROTOCOL:';

// Legacy patterns for migration
const LEGACY_HOOK_FILENAMES = ['session-start.py', 'session-start.js'];
const LEGACY_EVENT = 'UserPromptSubmit';

// --------------------------------------------------------------------------- //
//  Helpers
// --------------------------------------------------------------------------- //

function getClaudeHome() {
  return path.join(os.homedir(), '.claude');
}

function getProjectClaude() {
  return path.join(process.cwd(), '.claude');
}

function matchesAnyHookFilename(command) {
  return LEGACY_HOOK_FILENAMES.some((name) =>
    command.includes('/' + name) || command.includes('\\' + name) || command.endsWith(name)
  );
}

function isGlobalDir(targetDir) {
  return path.resolve(targetDir) === path.resolve(getClaudeHome());
}

// --------------------------------------------------------------------------- //
//  Step 1: Copy hook
// --------------------------------------------------------------------------- //

function copyHook(targetDir) {
  const hooksDir = path.join(targetDir, 'hooks');
  fs.mkdirSync(hooksDir, { recursive: true });

  const dst = path.join(hooksDir, HOOK_FILENAME);

  if (!fs.existsSync(HOOK_SRC)) {
    console.log(red(`  ERROR: ${HOOK_SRC} not found.`));
    return false;
  }

  const srcContent = fs.readFileSync(HOOK_SRC, 'utf-8');

  if (fs.existsSync(dst)) {
    // Refuse to overwrite symlinks
    const stat = fs.lstatSync(dst);
    if (stat.isSymbolicLink()) {
      console.log(red(`  ERROR: ${dst} is a symlink — refusing to overwrite`));
      return false;
    }

    const dstContent = fs.readFileSync(dst, 'utf-8');
    if (srcContent === dstContent) {
      console.log(yellow(`  SKIP: ${dst} already up-to-date`));
      return true;
    }
    console.log(yellow(`  UPDATE: ${dst} exists — overwriting with new version`));
  }

  // Copy hook.js and its dependency protocol.js
  fs.copyFileSync(HOOK_SRC, dst);

  const protocolSrc = path.join(__dirname, 'protocol.js');
  const protocolDst = path.join(hooksDir, 'protocol.js');
  fs.copyFileSync(protocolSrc, protocolDst);

  console.log(green(`  OK: Copied ${HOOK_FILENAME} + protocol.js -> ${hooksDir}`));
  return true;
}

// --------------------------------------------------------------------------- //
//  Step 2: Merge settings
// --------------------------------------------------------------------------- //

function mergeSettings(targetDir, isGlobal) {
  const settingsPath = path.join(targetDir, SETTINGS_FILENAME);

  const hookPrefix = isGlobal ? '~/.claude/hooks/' : '.claude/hooks/';
  const command = `node ${hookPrefix}${HOOK_FILENAME}`;

  const newHookEntry = {
    hooks: [{ type: 'command', command }],
  };

  let settings;
  try {
    settings = readJsonFile(settingsPath) || {};
  } catch {
    console.log(red(`  ERROR: ${settingsPath} contains invalid JSON. Fix it manually.`));
    return false;
  }

  // Check if hook is already registered under SessionStart
  const existingHooks = (settings.hooks || {}).SessionStart || [];
  for (const entry of existingHooks) {
    for (const hook of entry.hooks || []) {
      if (matchesAnyHookFilename(hook.command || '')) {
        // Check if it's already the Node.js version
        if ((hook.command || '').includes(HOOK_FILENAME)) {
          console.log(yellow(`  SKIP: Hook already registered in ${settingsPath}`));
          return true;
        }
        // Migrate Python -> Node.js: create new entry instead of mutating
        entry.hooks = entry.hooks.map((h) =>
          matchesAnyHookFilename(h.command || '')
            ? { ...h, command }
            : h
        );
        writeJsonFile(settingsPath, settings);
        console.log(green(`  OK: Migrated Python -> Node.js hook in ${settingsPath}`));
        console.log(`      Command: ${command}`);
        return true;
      }
    }
  }

  // Migrate: remove old UserPromptSubmit registration if present
  const oldHooks = (settings.hooks || {})[LEGACY_EVENT] || [];
  if (oldHooks.length > 0) {
    const filtered = oldHooks.filter(
      (entry) => !(entry.hooks || []).some((h) => matchesAnyHookFilename(h.command || ''))
    );
    if (filtered.length < oldHooks.length) {
      if (filtered.length > 0) {
        settings.hooks[LEGACY_EVENT] = filtered;
      } else {
        delete settings.hooks[LEGACY_EVENT];
      }
      console.log(green('  OK: Removed old UserPromptSubmit registration'));
    }
  }

  // Add the hook under SessionStart
  if (!settings.hooks) settings.hooks = {};
  if (!settings.hooks.SessionStart) settings.hooks.SessionStart = [];
  settings.hooks.SessionStart = [...settings.hooks.SessionStart, newHookEntry];

  writeJsonFile(settingsPath, settings);
  console.log(green(`  OK: Registered hook in ${settingsPath}`));
  console.log(`      Command: ${command}`);
  return true;
}

// --------------------------------------------------------------------------- //
//  Step 3: CLAUDE.md binding
// --------------------------------------------------------------------------- //

function addClaudeMdBinding(targetDir) {
  const claudeMdPath = isGlobalDir(targetDir)
    ? path.join(getClaudeHome(), 'CLAUDE.md')
    : path.join(path.dirname(targetDir), 'CLAUDE.md');

  if (fs.existsSync(claudeMdPath)) {
    const content = fs.readFileSync(claudeMdPath, 'utf-8');
    if (content.includes(CLAUDE_MD_MARKER)) {
      console.log(yellow(`  SKIP: Authority binding already in ${claudeMdPath}`));
      return true;
    }

    // Insert after the first top-level heading
    const lines = content.split('\n');
    let insertIdx = 0;
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].startsWith('# ')) {
        insertIdx = i + 1;
        while (insertIdx < lines.length && lines[insertIdx].trim() === '') {
          insertIdx++;
        }
        break;
      }
    }

    const bindingLines = CLAUDE_MD_BINDING.split('\n');
    const before = lines.slice(0, insertIdx);
    const after = lines.slice(insertIdx);
    const newContent = [...before, '', ...bindingLines, '', ...after].join('\n');

    fs.writeFileSync(claudeMdPath, newContent, 'utf-8');
    console.log(green(`  OK: Added authority binding to ${claudeMdPath}`));
  } else {
    fs.writeFileSync(claudeMdPath, `# Project\n\n${CLAUDE_MD_BINDING}\n`, 'utf-8');
    console.log(green(`  OK: Created ${claudeMdPath} with authority binding`));
  }

  return true;
}

// --------------------------------------------------------------------------- //
//  Step 4: Verify
// --------------------------------------------------------------------------- //

function verifyInstallation(targetDir) {
  const hookPath = path.join(targetDir, 'hooks', HOOK_FILENAME);

  if (!fs.existsSync(hookPath)) {
    console.log(red(`  FAIL: ${hookPath} not found`));
    return false;
  }

  try {
    const stdout = execFileSync(process.execPath, [hookPath], {
      input: '{}',
      encoding: 'utf-8',
      timeout: 10_000,
    });

    const output = JSON.parse(stdout.trim());
    const ctx = output.hookSpecificOutput.additionalContext;
    const ruleCount = (ctx.match(/## RULE/g) || []).length;
    const hasXml = ctx.includes('<dev-workflow-protocol>') && ctx.includes('</dev-workflow-protocol>');
    const hasCompliance = ctx.includes('COMPLIANCE REPORTING');

    const checks = [
      ['Valid JSON output', true],
      ['hookSpecificOutput present', 'hookSpecificOutput' in output],
      ['additionalContext present', ctx.length > 0],
      [`Protocol length: ${ctx.length} chars`, ctx.length > 1000],
      [`Rules found: ${ruleCount}`, ruleCount === 7],
      ['XML wrapper tags', hasXml],
      ['Compliance reporting section', hasCompliance],
    ];

    let allOk = true;
    for (const [label, passed] of checks) {
      const icon = passed ? green('PASS') : red('FAIL');
      console.log(`  ${icon}: ${label}`);
      if (!passed) allOk = false;
    }

    return allOk;
  } catch (err) {
    if (err.killed) {
      console.log(red('  FAIL: Hook timed out (10s)'));
    } else {
      console.log(red(`  FAIL: ${err.message}`));
    }
    return false;
  }
}

// --------------------------------------------------------------------------- //
//  Install orchestrator
// --------------------------------------------------------------------------- //

function install(targetDir, scopeIsGlobal) {
  const scopeLabel = scopeIsGlobal ? 'Global' : 'Project';

  console.log(bold(`\nInstalling (${scopeLabel})...`));
  console.log(`Target: ${targetDir}`);

  console.log(bold('\n[1/4] Copying hook script'));
  if (!copyHook(targetDir)) process.exit(1);

  console.log(bold('\n[2/4] Registering in settings.json'));
  if (!mergeSettings(targetDir, scopeIsGlobal)) process.exit(1);

  console.log(bold('\n[3/4] Adding CLAUDE.md authority binding'));
  addClaudeMdBinding(targetDir);

  console.log(bold('\n[4/4] Verifying installation'));
  if (verifyInstallation(targetDir)) {
    console.log(green(bold('\nInstallation complete!')));
    console.log('\nRestart Claude Code to activate the workflow protocol.');
    console.log('Verify by asking: "What development workflow rules are active?"');
  } else {
    console.log(yellow(bold('\nInstallation finished with warnings.')));
    console.log('The hook was copied and registered but verification found issues.');
    console.log('Check the output above and fix any problems.');
  }
}

// --------------------------------------------------------------------------- //
//  Exports (for testing and CLI)
// --------------------------------------------------------------------------- //

module.exports = {
  install,
  copyHook,
  mergeSettings,
  addClaudeMdBinding,
  verifyInstallation,
  getClaudeHome,
  getProjectClaude,
  HOOK_FILENAME,
  SETTINGS_FILENAME,
  CLAUDE_MD_BINDING,
  CLAUDE_MD_MARKER,
  LEGACY_HOOK_FILENAMES,
  LEGACY_EVENT,
};
