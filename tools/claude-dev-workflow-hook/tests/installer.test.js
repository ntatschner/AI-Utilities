'use strict';

const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');

const {
  copyHook,
  mergeSettings,
  addClaudeMdBinding,
  verifyInstallation,
  HOOK_FILENAME,
  SETTINGS_FILENAME,
  CLAUDE_MD_MARKER,
} = require('../src/installer.js');
const { uninstall } = require('../src/uninstaller.js');

/**
 * Create a fresh temp directory for each test.
 */
function makeTempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'hook-test-'));
}

function cleanup(dir) {
  fs.rmSync(dir, { recursive: true, force: true });
}

// --------------------------------------------------------------------------- //
//  copyHook
// --------------------------------------------------------------------------- //

describe('copyHook', () => {
  let tmpDir;
  beforeEach(() => { tmpDir = makeTempDir(); });
  afterEach(() => { cleanup(tmpDir); });

  it('copies hook.js and protocol.js to hooks directory', () => {
    assert.ok(copyHook(tmpDir));
    assert.ok(fs.existsSync(path.join(tmpDir, 'hooks', HOOK_FILENAME)));
    assert.ok(fs.existsSync(path.join(tmpDir, 'hooks', 'protocol.js')));
  });

  it('is idempotent — second call skips', () => {
    copyHook(tmpDir);
    // Second call should succeed (skip)
    assert.ok(copyHook(tmpDir));
  });
});

// --------------------------------------------------------------------------- //
//  mergeSettings
// --------------------------------------------------------------------------- //

describe('mergeSettings', () => {
  let tmpDir;
  beforeEach(() => { tmpDir = makeTempDir(); });
  afterEach(() => { cleanup(tmpDir); });

  it('creates settings.json with SessionStart hook entry', () => {
    assert.ok(mergeSettings(tmpDir, true));

    const settings = JSON.parse(
      fs.readFileSync(path.join(tmpDir, SETTINGS_FILENAME), 'utf-8')
    );

    assert.ok(settings.hooks.SessionStart);
    assert.equal(settings.hooks.SessionStart.length, 1);

    const command = settings.hooks.SessionStart[0].hooks[0].command;
    assert.ok(command.includes('node'));
    assert.ok(command.includes(HOOK_FILENAME));
  });

  it('preserves existing settings when merging', () => {
    const existingSettings = {
      theme: 'dark',
      hooks: {
        PreToolUse: [{ hooks: [{ type: 'command', command: 'echo pre' }] }],
      },
    };
    fs.writeFileSync(
      path.join(tmpDir, SETTINGS_FILENAME),
      JSON.stringify(existingSettings),
      'utf-8'
    );

    mergeSettings(tmpDir, true);

    const settings = JSON.parse(
      fs.readFileSync(path.join(tmpDir, SETTINGS_FILENAME), 'utf-8')
    );
    assert.equal(settings.theme, 'dark');
    assert.ok(settings.hooks.PreToolUse);
    assert.ok(settings.hooks.SessionStart);
  });

  it('is idempotent — does not duplicate entries', () => {
    mergeSettings(tmpDir, true);
    mergeSettings(tmpDir, true);

    const settings = JSON.parse(
      fs.readFileSync(path.join(tmpDir, SETTINGS_FILENAME), 'utf-8')
    );
    assert.equal(settings.hooks.SessionStart.length, 1);
  });

  it('migrates UserPromptSubmit to SessionStart', () => {
    const oldSettings = {
      hooks: {
        UserPromptSubmit: [
          { hooks: [{ type: 'command', command: 'python3 ~/.claude/hooks/session-start.py' }] },
        ],
      },
    };
    fs.writeFileSync(
      path.join(tmpDir, SETTINGS_FILENAME),
      JSON.stringify(oldSettings),
      'utf-8'
    );

    mergeSettings(tmpDir, true);

    const settings = JSON.parse(
      fs.readFileSync(path.join(tmpDir, SETTINGS_FILENAME), 'utf-8')
    );
    assert.ok(!settings.hooks.UserPromptSubmit, 'UserPromptSubmit should be removed');
    assert.ok(settings.hooks.SessionStart, 'SessionStart should exist');
    assert.equal(settings.hooks.SessionStart.length, 1);
  });

  it('migrates Python command to Node.js under SessionStart', () => {
    const pySettings = {
      hooks: {
        SessionStart: [
          { hooks: [{ type: 'command', command: 'python3 ~/.claude/hooks/session-start.py' }] },
        ],
      },
    };
    fs.writeFileSync(
      path.join(tmpDir, SETTINGS_FILENAME),
      JSON.stringify(pySettings),
      'utf-8'
    );

    mergeSettings(tmpDir, true);

    const settings = JSON.parse(
      fs.readFileSync(path.join(tmpDir, SETTINGS_FILENAME), 'utf-8')
    );
    const command = settings.hooks.SessionStart[0].hooks[0].command;
    assert.ok(command.includes('node'), 'Should use node, not python');
    assert.ok(command.includes('session-start.js'), 'Should reference .js, not .py');
  });

  it('uses relative path for project scope', () => {
    mergeSettings(tmpDir, false);

    const settings = JSON.parse(
      fs.readFileSync(path.join(tmpDir, SETTINGS_FILENAME), 'utf-8')
    );
    const command = settings.hooks.SessionStart[0].hooks[0].command;
    assert.ok(command.startsWith('node .claude/hooks/'));
  });

  it('uses home path for global scope', () => {
    mergeSettings(tmpDir, true);

    const settings = JSON.parse(
      fs.readFileSync(path.join(tmpDir, SETTINGS_FILENAME), 'utf-8')
    );
    const command = settings.hooks.SessionStart[0].hooks[0].command;
    assert.ok(command.startsWith('node ~/.claude/hooks/'));
  });
});

// --------------------------------------------------------------------------- //
//  addClaudeMdBinding
// --------------------------------------------------------------------------- //

describe('addClaudeMdBinding', () => {
  let tmpDir;
  let projectRoot;

  beforeEach(() => {
    // Simulate project structure: projectRoot/.claude/ (tmpDir = .claude dir)
    projectRoot = makeTempDir();
    tmpDir = path.join(projectRoot, '.claude');
    fs.mkdirSync(tmpDir, { recursive: true });
  });
  afterEach(() => { cleanup(projectRoot); });

  it('creates CLAUDE.md if it does not exist', () => {
    addClaudeMdBinding(tmpDir);
    const claudeMd = path.join(projectRoot, 'CLAUDE.md');
    assert.ok(fs.existsSync(claudeMd));
    const content = fs.readFileSync(claudeMd, 'utf-8');
    assert.ok(content.includes(CLAUDE_MD_MARKER));
  });

  it('appends binding to existing CLAUDE.md', () => {
    const claudeMd = path.join(projectRoot, 'CLAUDE.md');
    fs.writeFileSync(claudeMd, '# My Project\n\nSome content.\n', 'utf-8');

    addClaudeMdBinding(tmpDir);

    const content = fs.readFileSync(claudeMd, 'utf-8');
    assert.ok(content.includes(CLAUDE_MD_MARKER));
    assert.ok(content.includes('Some content.'));
  });

  it('is idempotent — does not duplicate binding', () => {
    const claudeMd = path.join(projectRoot, 'CLAUDE.md');
    fs.writeFileSync(claudeMd, '# My Project\n\nSome content.\n', 'utf-8');

    addClaudeMdBinding(tmpDir);
    addClaudeMdBinding(tmpDir);

    const content = fs.readFileSync(claudeMd, 'utf-8');
    const occurrences = content.split(CLAUDE_MD_MARKER).length - 1;
    assert.equal(occurrences, 1, 'Should appear exactly once');
  });
});

// --------------------------------------------------------------------------- //
//  verifyInstallation
// --------------------------------------------------------------------------- //

describe('verifyInstallation', () => {
  let tmpDir;
  beforeEach(() => { tmpDir = makeTempDir(); });
  afterEach(() => { cleanup(tmpDir); });

  it('returns true when hook is properly installed', () => {
    copyHook(tmpDir);
    assert.ok(verifyInstallation(tmpDir));
  });

  it('returns false when hook file is missing', () => {
    assert.ok(!verifyInstallation(tmpDir));
  });
});

// --------------------------------------------------------------------------- //
//  uninstall
// --------------------------------------------------------------------------- //

describe('uninstall', () => {
  let tmpDir;
  let projectRoot;

  beforeEach(() => {
    projectRoot = makeTempDir();
    tmpDir = path.join(projectRoot, '.claude');
    fs.mkdirSync(tmpDir, { recursive: true });
  });
  afterEach(() => { cleanup(projectRoot); });

  it('removes hook files', () => {
    copyHook(tmpDir);
    assert.ok(fs.existsSync(path.join(tmpDir, 'hooks', HOOK_FILENAME)));

    uninstall(tmpDir);
    assert.ok(!fs.existsSync(path.join(tmpDir, 'hooks', HOOK_FILENAME)));
  });

  it('removes settings entry', () => {
    mergeSettings(tmpDir, false);
    uninstall(tmpDir);

    const settings = JSON.parse(
      fs.readFileSync(path.join(tmpDir, SETTINGS_FILENAME), 'utf-8')
    );
    assert.ok(!settings.hooks, 'hooks key should be removed');
  });

  it('removes CLAUDE.md binding', () => {
    const claudeMd = path.join(projectRoot, 'CLAUDE.md');
    fs.writeFileSync(claudeMd, '# My Project\n\nSome content.\n', 'utf-8');
    addClaudeMdBinding(tmpDir);

    assert.ok(fs.readFileSync(claudeMd, 'utf-8').includes(CLAUDE_MD_MARKER));

    uninstall(tmpDir);

    const content = fs.readFileSync(claudeMd, 'utf-8');
    assert.ok(!content.includes(CLAUDE_MD_MARKER), 'Binding should be removed');
    assert.ok(content.includes('Some content.'), 'Original content preserved');
  });

  it('removes legacy UserPromptSubmit entries', () => {
    const settingsPath = path.join(tmpDir, SETTINGS_FILENAME);
    const settings = {
      hooks: {
        UserPromptSubmit: [
          { hooks: [{ type: 'command', command: 'python3 ~/.claude/hooks/session-start.py' }] },
        ],
      },
    };
    fs.writeFileSync(settingsPath, JSON.stringify(settings), 'utf-8');

    uninstall(tmpDir);

    const updated = JSON.parse(fs.readFileSync(settingsPath, 'utf-8'));
    assert.ok(!updated.hooks, 'hooks key should be removed');
  });

  it('completes without error when nothing is installed', () => {
    // No copyHook, no mergeSettings, no addClaudeMdBinding
    uninstall(tmpDir);
    // Should not throw — the SKIP messages are printed but no crash
    assert.ok(!fs.existsSync(path.join(tmpDir, 'hooks')));
  });
});
