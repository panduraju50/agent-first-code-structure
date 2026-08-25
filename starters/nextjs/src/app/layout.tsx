// Server component (no "use client" directive). App-router files may import
// `composition` and `core`, but never reach into `features/*` directly — see
// README.md and scripts/check-boundaries.mjs.
import React from "react";
import type { ReactNode } from "react";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
