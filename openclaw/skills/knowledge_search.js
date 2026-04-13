/**
 * knowledge_search — RAG skill for SQLClaw
 *
 * Calls knowledge_search.py via execFile (same pattern as send_chart.js).
 * The Python script handles Cohere embedding + ChromaDB similarity search.
 *
 * Parameters:
 *   query  (string) — natural language question or topic to look up
 *   top_k  (number, optional) — number of chunks to return (default: 3)
 */

const { execFile } = require("child_process");
const path = require("path");

const SEARCH_SCRIPT = path.join(__dirname, "knowledge_search.py");

module.exports = {
  name: "knowledge_search",
  description:
    "Search the business knowledge base (KNOWLEDGE.md) using semantic similarity. " +
    "Use this when the user asks about business metrics, KPI definitions, Brazilian " +
    "e-commerce context, data limitations, or analytical patterns.",

  parameters: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "The question or topic to search for in the knowledge base",
      },
      top_k: {
        type: "number",
        description: "Number of relevant chunks to return (default: 3)",
      },
    },
    required: ["query"],
  },

  handler({ query, top_k }, config) {
    const pythonPath = config.pythonPath || process.env.PYTHON_PATH || "python";
    const topK = top_k || 3;

    const args = ["--query", query, "--top_k", String(topK)];

    const env = {
      ...process.env,
      COHERE_API_KEY: config.cohereApiKey || process.env.COHERE_API_KEY || "",
    };

    return new Promise((resolve) => {
      execFile(pythonPath, [SEARCH_SCRIPT, ...args], { env }, (err, stdout, stderr) => {
        if (err) {
          resolve({ error: `knowledge_search failed: ${stderr || err.message}` });
          return;
        }
        try {
          resolve(JSON.parse(stdout.trim()));
        } catch {
          resolve({ error: `Invalid JSON from knowledge_search.py: ${stdout}` });
        }
      });
    });
  },
};
