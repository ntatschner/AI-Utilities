#!/usr/bin/env node
'use strict';

/**
 * Claude Code Development Workflow Protocol — SessionStart Hook
 *
 * Generic, project-agnostic version. Works in any repository.
 * Injects orchestration rules (sequencing, testing, team coordination)
 * once per session via SessionStart hookSpecificOutput.additionalContext.
 *
 * Registered as SessionStart so the protocol is injected once per session
 * (on startup, resume, clear, and compact) rather than on every prompt.
 */

const { PROTOCOL } = require('./protocol.js');

function emitOutput() {
  const output = {
    hookSpecificOutput: {
      hookEventName: 'SessionStart',
      additionalContext: PROTOCOL,
    },
  };
  process.stdout.write(JSON.stringify(output) + '\n');
  process.exit(0);
}

function main() {
  // Drain stdin — hook runner pipes JSON input; we must consume it.
  // The input is not used; SessionStart hooks only output additionalContext.
  process.stdin.on('data', () => {}); // discard chunks
  process.stdin.on('end', emitOutput);
  process.stdin.on('error', emitOutput); // emit output even if stdin errors

  // Handle stdin already closed (e.g. piped empty input)
  process.stdin.resume();
}

main();
