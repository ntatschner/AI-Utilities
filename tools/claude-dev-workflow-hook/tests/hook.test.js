'use strict';

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const path = require('node:path');

const hookPath = path.join(__dirname, '..', 'src', 'hook.js');

/**
 * Run the hook script with the given stdin and return parsed JSON output.
 */
function runHook(stdin = '{}') {
  const stdout = execFileSync(process.execPath, [hookPath], {
    input: stdin,
    encoding: 'utf-8',
    timeout: 10_000,
  });
  return JSON.parse(stdout.trim());
}

describe('hook.js — SessionStart hook output', () => {
  it('outputs valid JSON', () => {
    const output = runHook();
    assert.equal(typeof output, 'object');
  });

  it('has hookSpecificOutput with hookEventName', () => {
    const output = runHook();
    assert.ok(output.hookSpecificOutput, 'missing hookSpecificOutput');
    assert.equal(output.hookSpecificOutput.hookEventName, 'SessionStart');
  });

  it('has non-empty additionalContext', () => {
    const output = runHook();
    const ctx = output.hookSpecificOutput.additionalContext;
    assert.ok(ctx, 'additionalContext is falsy');
    assert.ok(ctx.length > 1000, `additionalContext too short: ${ctx.length} chars`);
  });

  it('contains exactly 7 rules (RULE 0 through RULE 6)', () => {
    const output = runHook();
    const ctx = output.hookSpecificOutput.additionalContext;
    const ruleMatches = ctx.match(/## RULE \d/g);
    assert.equal(ruleMatches.length, 7, `Expected 7 rules, found ${ruleMatches.length}`);
  });

  it('has XML wrapper tags', () => {
    const output = runHook();
    const ctx = output.hookSpecificOutput.additionalContext;
    assert.ok(ctx.includes('<dev-workflow-protocol>'), 'missing opening XML tag');
    assert.ok(ctx.includes('</dev-workflow-protocol>'), 'missing closing XML tag');
  });

  it('has compliance reporting section', () => {
    const output = runHook();
    const ctx = output.hookSpecificOutput.additionalContext;
    assert.ok(ctx.includes('COMPLIANCE REPORTING'), 'missing COMPLIANCE REPORTING section');
  });

  it('handles empty stdin gracefully', () => {
    const output = runHook('');
    assert.ok(output.hookSpecificOutput.additionalContext.length > 1000);
  });

  it('handles malformed stdin gracefully', () => {
    const output = runHook('not json at all');
    assert.ok(output.hookSpecificOutput.additionalContext.length > 1000);
  });
});

describe('protocol.js — PROTOCOL string', () => {
  it('exports a non-empty PROTOCOL string', () => {
    const { PROTOCOL } = require('../src/protocol.js');
    assert.equal(typeof PROTOCOL, 'string');
    assert.ok(PROTOCOL.length > 1000);
  });

  it('starts with XML opening tag and ends with closing tag', () => {
    const { PROTOCOL } = require('../src/protocol.js');
    assert.ok(PROTOCOL.startsWith('<dev-workflow-protocol>'));
    assert.ok(PROTOCOL.endsWith('</dev-workflow-protocol>'));
  });

  it('matches Python version rule count', () => {
    const { PROTOCOL } = require('../src/protocol.js');
    const ruleCount = (PROTOCOL.match(/## RULE \d/g) || []).length;
    assert.equal(ruleCount, 7, `Expected 7 rules, got ${ruleCount}`);
  });

  it('detects Agent Teams via env var check, not shell echo', () => {
    const { PROTOCOL } = require('../src/protocol.js');
    // Should NOT tell the model to run `echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`
    assert.ok(
      !PROTOCOL.includes('Run: `echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`'),
      'Protocol should not use shell echo for Agent Teams detection'
    );
    // Should reference the env var name for detection
    assert.ok(
      PROTOCOL.includes('CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS'),
      'Protocol should reference the Agent Teams env var'
    );
  });
});
