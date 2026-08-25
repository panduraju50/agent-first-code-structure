// Minimal ambient declaration for the one Node global this starter touches
// (console), so `npm run build` type-checks with zero installed
// dependencies — no @types/node required. See tsconfig.base.json's
// "types": [], which keeps this the single source of truth for globals
// rather than risking a conflicting definition if @types/node is ever
// added as a devDependency.
export {};

declare global {
  const console: {
    log(...args: unknown[]): void;
    error(...args: unknown[]): void;
  };
}
