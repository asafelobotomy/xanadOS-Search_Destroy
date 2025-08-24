import { greet } from '../src/greet.js';

// pseudo-test, for users to enhance
if (greet('World') !== 'Hello, World!') {
  console.error('Test failed');
  process.exit(1);
}

if (greet() !== 'Hello') {
  console.error('Test failed for empty input');
  process.exit(1);
}

console.log('All sample checks passed');
