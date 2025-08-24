export function greet(name) {
  if (!name) return 'Hello';
  // naive formatting and edge cases
  return `Hello, ${String(name)}!`;
}
