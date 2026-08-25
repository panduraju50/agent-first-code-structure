// Public barrel for the `core` domain. Everything a feature is allowed to
// depend on flows through this one file (or its subpaths) — core itself
// depends on nothing else in this repo.

// @capability core.barrel
export { toBase62, nextId } from "./id/base62";
export { validateTitle, validateEmail } from "./validation/validators";
