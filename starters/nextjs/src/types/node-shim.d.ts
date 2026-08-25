// Minimal ambient shim standing in for `@types/node`, scoped to exactly the
// `node:` built-ins the domain tests use (Node itself provides these modules
// at runtime regardless of type declarations — this file only satisfies the
// compiler, offline, without an `npm install`).

declare module "node:test" {
  export interface TestContext {
    [key: string]: unknown;
  }
  export default function test(
    name: string,
    fn: (t?: TestContext) => void | Promise<void>
  ): void;
}

declare module "node:assert/strict" {
  interface Assert {
    equal(actual: unknown, expected: unknown, message?: string): void;
    deepEqual(actual: unknown, expected: unknown, message?: string): void;
    match(actual: string, regex: RegExp, message?: string): void;
    ok(value: unknown, message?: string): void;
    throws(
      fn: () => unknown,
      matcher?: RegExp | ((err: unknown) => boolean),
      message?: string
    ): void;
  }
  const assert: Assert;
  export default assert;
}
