// Idiomatic Design D enforcement via eslint-plugin-boundaries (ESLint 9 flat
// config). This is the "real" tool for the job; it is NOT run in this
// npm-install-free scaffold (eslint + eslint-plugin-boundaries aren't
// installed here). CI installs them and runs this config for real — see
// .github/workflows/ci.yml. scripts/check-boundaries.mjs is the zero-install
// stdlib fallback that enforces the identical edge table below, so the
// boundary rule holds even before/without `npm install`.
import boundaries from "eslint-plugin-boundaries";

export default [
  {
    files: ["src/**/*.{ts,tsx}"],
    plugins: { boundaries },
    settings: {
      "boundaries/elements": [
        { type: "core", pattern: "src/core/**" },
        { type: "users", pattern: "src/features/users/**" },
        { type: "tasks", pattern: "src/features/tasks/**" },
        { type: "composition", pattern: "src/composition/**" },
        { type: "app", pattern: "src/app/**" },
      ],
    },
    rules: {
      // Mirrors scripts/lib/rules.mjs's ALLOWED_EDGES exactly:
      //   core        -> core only
      //   users       -> core, users            (never tasks)
      //   tasks       -> core, tasks            (never users)
      //   composition -> core, users, tasks, composition   (the one broad-import file)
      //   app         -> core, composition, app (never features/* directly)
      "boundaries/element-types": [
        "error",
        {
          default: "disallow",
          message: "${file.type} is not allowed to import ${dependency.type}",
          rules: [
            { from: "core", allow: ["core"] },
            { from: "users", allow: ["core", "users"] },
            { from: "tasks", allow: ["core", "tasks"] },
            { from: "composition", allow: ["core", "users", "tasks", "composition"] },
            { from: "app", allow: ["core", "composition", "app"] },
          ],
        },
      ],
      "boundaries/no-unknown": "error",
      "boundaries/no-unknown-files": "error",
    },
  },
];
