// Barrel export for the core package. Domains should import from the
// specific module (./id.ts, ./validate.ts) or from this barrel — both
// resolve to the same single implementation.
export { encodeBase62, decodeBase62, nextId } from "./id.ts";
export { validateTitle, validateEmail, ValidationError } from "./validate.ts";
