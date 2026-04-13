/**
 * query_validator — OpenClaw skill
 *
 * Validates SQL queries before they reach the PostgreSQL skill.
 * Blocks any statement that could mutate data (defense-in-depth on top
 * of the read-only DB user). Logs every query attempt to an audit file.
 */

const fs   = require("fs");
const path = require("path");

const LOG_FILE = path.join(__dirname, "../logs/queries.log");

// Patterns that must never appear in a safe read query.
// Checked case-insensitively against the full SQL string.
const BLOCKED_PATTERNS = [
  /\bINSERT\b/i,
  /\bUPDATE\b/i,
  /\bDELETE\b/i,
  /\bDROP\b/i,
  /\bTRUNCATE\b/i,
  /\bALTER\b/i,
  /\bCREATE\b/i,
  /\bGRANT\b/i,
  /\bREVOKE\b/i,
  /\bEXECUTE\b/i,
  /\bCALL\b/i,
  /\bCOPY\b/i,
  // Block stacked statements (multiple queries in one string)
  /;[\s\S]*\bSELECT\b/i,
];

function appendLog(entry) {
  try {
    fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
    fs.appendFileSync(LOG_FILE, entry + "\n", "utf8");
  } catch {
    // Non-fatal — don't crash the agent if logging fails
  }
}

function validateQuery(sql) {
  for (const pattern of BLOCKED_PATTERNS) {
    if (pattern.test(sql)) {
      return {
        safe: false,
        reason: `Query blocked: matched forbidden pattern /${pattern.source}/`,
      };
    }
  }
  return { safe: true };
}

module.exports = {
  name: "query_validator",
  description:
    "Validates a SQL query for safety before execution. " +
    "Call this with the exact SQL string before passing it to the postgresql skill. " +
    "Returns { safe: true } if the query is allowed, or { safe: false, reason } if blocked.",

  parameters: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "The SQL query string to validate.",
      },
    },
    required: ["query"],
  },

  async handler({ query }) {
    const timestamp = new Date().toISOString();
    const result    = validateQuery(query);

    const logEntry = [
      `[${timestamp}]`,
      `STATUS: ${result.safe ? "ALLOWED" : "BLOCKED"}`,
      `QUERY: ${query.replace(/\s+/g, " ").trim()}`,
      result.safe ? "" : `REASON: ${result.reason}`,
    ]
      .filter(Boolean)
      .join(" | ");

    appendLog(logEntry);

    if (!result.safe) {
      return {
        safe: false,
        reason: result.reason,
        message:
          "This query has been blocked by the security validator. " +
          "Only SELECT statements are permitted. " +
          `Reason: ${result.reason}`,
      };
    }

    return { safe: true, query };
  },
};
