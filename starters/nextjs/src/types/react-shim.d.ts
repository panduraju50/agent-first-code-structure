// Minimal ambient shim standing in for `@types/react` + `@types/react-dom`.
//
// This starter is npm-install-free by design (see README.md: no network
// installs were run to build it), so the real React type packages are not
// present. A production checkout replaces this file entirely by running
// `npm install react react-dom next` (and their @types packages) — at that
// point delete this file and let the real types win.
//
// Only the handful of APIs the demo App Router components actually use are
// declared, kept deliberately loose (`any`) since this is a compile-time
// stand-in, not a real type-safety guarantee.

declare module "react" {
  export type ReactNode = any;

  export function useState<T>(initial: T): [T, (value: T) => void];

  const React: {
    createElement(...args: any[]): any;
    Fragment: any;
  };
  export default React;
}

declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any;
  }
  interface Element {
    [key: string]: any;
  }
}
