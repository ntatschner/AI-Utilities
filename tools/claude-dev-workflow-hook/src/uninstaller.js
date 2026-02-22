'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { green, yellow, bold, readJsonFile, writeJsonFile } = require('./utils.js');
const {
  getClaudeHome,
  HOOK_FILENAME,
  SETTINGS_FILENAME,
  CLAUDE_MD_MARKER,
  LEGACY_HOOK_FILENAMES,
  LEGACY_EVENT,
} = require('./installer.js');

// --------------------------------------------------------------------------- //
//  Helpers
// --------------------------------------------------------------------------- //

function matchesAnyHookFilename(command) {
  return LEGACY_HOOK_FILENAMES.some((name) =>
    command.includes('/' + name) || command.includes('\\' + name) || command.endsWith(name)
  );
}

// --------------------------------------------------------------------------- //
//  Uninstall
// --------------------------------------------------------------------------- //

function uninstall(targetDir) {
  console.log(bold('\nUninstalling workflow hook...'));

  // Remove hook files (both .js and .py variants + protocol.js)
  const hooksDir = path.join(targetDir, 'hooks');
  const hookVariants = ['session-start.js', 'session-start.py', 'protocol.js'];
  let deletedAny = false;

  for (const filename of hookVariants) {
    const hookPath = path.join(hooksDir, filename);
    if (fs.existsSync(hookPath)) {
      fs.unlinkSync(hookPath);
      deletedAny = true;
      console.log(green(`  OK: Removed ${hookPath}`));
    }
  }

  if (!deletedAny) {
    console.log(yellow(`  SKIP: No hook files found in ${hooksDir}`));
  }

  // Remove from settings.json (check both SessionStart and legacy UserPromptSubmit)
  const settingsPath = path.join(targetDir, SETTINGS_FILENAME);
  if (fs.existsSync(settingsPath)) {
    try {
      const settings = readJsonFile(settingsPath);
      if (settings === null) {
        console.log(yellow(`  SKIP: ${settingsPath} is empty`));
      } else {
        let removedAny = false;

        for (const eventName of ['SessionStart', LEGACY_EVENT]) {
          const hooksList = (settings.hooks || {})[eventName] || [];
          const originalLen = hooksList.length;

          const filtered = hooksList.filter(
            (entry) => !(entry.hooks || []).some((h) => matchesAnyHookFilename(h.command || ''))
          );

          if (filtered.length < originalLen) {
            if (filtered.length > 0) {
              settings.hooks[eventName] = filtered;
            } else {
              delete settings.hooks[eventName];
            }
            removedAny = true;
          }
        }

        if (removedAny) {
          if (settings.hooks && Object.keys(settings.hooks).length === 0) {
            delete settings.hooks;
          }
          writeJsonFile(settingsPath, settings);
          console.log(green(`  OK: Removed hook entry from ${settingsPath}`));
        } else {
          console.log(yellow(`  SKIP: No hook entry found in ${settingsPath}`));
        }
      }
    } catch {
      console.log(yellow(`  SKIP: ${settingsPath} has invalid JSON — edit manually`));
    }
  }

  // Remove CLAUDE.md binding
  const claudeHome = getClaudeHome();
  const claudeMdPath = path.resolve(targetDir) === path.resolve(claudeHome)
    ? path.join(claudeHome, 'CLAUDE.md')
    : path.join(path.dirname(targetDir), 'CLAUDE.md');

  if (fs.existsSync(claudeMdPath)) {
    const content = fs.readFileSync(claudeMdPath, 'utf-8');
    if (content.includes(CLAUDE_MD_MARKER)) {
      const lines = content.split('\n');
      const newLines = [];
      let skip = false;

      for (const line of lines) {
        if (line.includes(CLAUDE_MD_MARKER)) {
          skip = true;
          // Remove blank line before marker
          if (newLines.length > 0 && newLines[newLines.length - 1].trim() === '') {
            newLines.pop();
          }
          continue;
        }
        if (skip && line.includes('<!-- END WORKFLOW PROTOCOL -->')) {
          skip = false;
          continue;
        }
        if (!skip) {
          newLines.push(line);
        }
      }

      // Clean up double blank lines
      let cleaned = newLines.join('\n');
      while (cleaned.includes('\n\n\n')) {
        cleaned = cleaned.replace(/\n\n\n/g, '\n\n');
      }

      fs.writeFileSync(claudeMdPath, cleaned, 'utf-8');
      console.log(green(`  OK: Removed authority binding from ${claudeMdPath}`));
    } else {
      console.log(yellow(`  SKIP: No authority binding found in ${claudeMdPath}`));
    }
  }

  // Clean up empty hooks directory
  if (fs.existsSync(hooksDir)) {
    const remaining = fs.readdirSync(hooksDir);
    if (remaining.length === 0) {
      fs.rmdirSync(hooksDir);
      console.log(green(`  OK: Removed empty ${hooksDir}`));
    }
  }

  console.log(green('\nUninstall complete.'));
}

module.exports = { uninstall };
