/**
 * send_chart — OpenClaw skill
 *
 * Calls chart_generator.py to produce a PNG, then returns the file path
 * for OpenClaw to send as a photo via Telegram.
 *
 * The agent should call this skill when the user asks for a chart/graph.
 */

const { execFile } = require("child_process");
const path         = require("path");

module.exports = {
  name: "send_chart",
  description:
    "Generates a chart from query result data and sends it as an image via Telegram. " +
    "Call this after getting SQL results when the user asks for a chart or visualization. " +
    "Returns the file path of the generated PNG.",

  parameters: {
    type: "object",
    properties: {
      chart_type: {
        type: "string",
        enum: ["bar", "line", "pie", "heatmap"],
        description: "Type of chart to generate.",
      },
      title: {
        type: "string",
        description: "Chart title (include the time period if relevant).",
      },
      xlabel: {
        type: "string",
        description: "X-axis label.",
        default: "",
      },
      ylabel: {
        type: "string",
        description: "Y-axis label.",
        default: "",
      },
      data: {
        type: "array",
        description:
          "Data points as an array of objects. " +
          "For bar/line/pie: [{label, value}, ...]. " +
          "For heatmap: [{row, col, value}, ...].",
        items: { type: "object" },
      },
    },
    required: ["chart_type", "title", "data"],
  },

  handler({ chart_type, title, xlabel = "", ylabel = "", data }, { config }) {
    return new Promise((resolve, reject) => {
      const pythonPath  = config?.pythonPath  || "python";
      const chartScript = config?.chartScript
        ? path.resolve(__dirname, "..", config.chartScript)
        : path.join(__dirname, "chart_generator.py");

      const args = [
        chartScript,
        "--type",   chart_type,
        "--title",  title,
        "--xlabel", xlabel,
        "--ylabel", ylabel,
        "--data",   JSON.stringify(data),
      ];

      execFile(pythonPath, args, { timeout: 30_000 }, (err, stdout, stderr) => {
        if (err) {
          return reject(
            new Error(`chart_generator.py failed: ${stderr || err.message}`)
          );
        }

        const outputPath = stdout.trim();
        if (!outputPath) {
          return reject(new Error("chart_generator.py produced no output path."));
        }

        resolve({
          success: true,
          file_path: outputPath,
          message: `Chart saved to ${outputPath}. Send this file as a Telegram photo.`,
        });
      });
    });
  },
};
