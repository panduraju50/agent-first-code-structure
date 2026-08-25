// A tiny CLI entry point so the wired scenario is directly runnable/verifiable
// offline: `node dist/composition/run.js` after `npm run build:offline`.
import { runScenario } from "./root";

const result = runScenario();
console.log(JSON.stringify(result, null, 2));
