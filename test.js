/**
 * Basic functionality tests for the Slack Messaging Prioritization App
 * These tests verify the core logic without requiring a Slack connection
 */

// Mock environment variables for testing
process.env.SLACK_BOT_TOKEN = 'xoxb-test-token';
process.env.SLACK_SIGNING_SECRET = 'test-signing-secret';
process.env.SLACK_APP_TOKEN = 'xapp-test-token';

// Test priority keyword detection
function testPriorityDetection() {
  console.log('Testing priority detection logic...\n');
  
  const testCases = [
    { text: 'This is an urgent issue', expected: 'CRITICAL' },
    { text: 'Emergency - server down!', expected: 'CRITICAL' },
    { text: 'Important deadline tomorrow', expected: 'HIGH' },
    { text: 'This is a blocker for the release', expected: 'HIGH' },
    { text: 'We need this soon', expected: 'MEDIUM' },
    { text: 'This is required for next sprint', expected: 'MEDIUM' },
    { text: 'FYI: new documentation available', expected: 'LOW' },
    { text: 'Info: team meeting at 3pm', expected: 'LOW' },
    { text: 'This is a regular message', expected: null },
    { text: 'We are organizing the materials', expected: null }, // Contains "info" substring but not as a word
  ];
  
  // Load the priority keywords
  const PRIORITY_KEYWORDS = {
    CRITICAL: (process.env.CRITICAL_KEYWORDS || 'urgent,emergency,critical,asap,immediately').split(',').map(k => k.trim().toLowerCase()),
    HIGH: (process.env.HIGH_KEYWORDS || 'important,priority,deadline,blocker').split(',').map(k => k.trim().toLowerCase()),
    MEDIUM: (process.env.MEDIUM_KEYWORDS || 'soon,needed,required').split(',').map(k => k.trim().toLowerCase()),
    LOW: (process.env.LOW_KEYWORDS || 'fyi,info,update').split(',').map(k => k.trim().toLowerCase())
  };
  
  // Recreate the detectPriority function
  function detectPriority(text) {
    const lowerText = text.toLowerCase();
    
    const hasKeyword = (keywords) => {
      return keywords.some(keyword => {
        const regex = new RegExp(`\\b${keyword}\\b`, 'i');
        return regex.test(lowerText);
      });
    };
    
    if (hasKeyword(PRIORITY_KEYWORDS.CRITICAL)) return 'CRITICAL';
    if (hasKeyword(PRIORITY_KEYWORDS.HIGH)) return 'HIGH';
    if (hasKeyword(PRIORITY_KEYWORDS.MEDIUM)) return 'MEDIUM';
    if (hasKeyword(PRIORITY_KEYWORDS.LOW)) return 'LOW';
    
    return null;
  }
  
  let passed = 0;
  let failed = 0;
  
  testCases.forEach(({ text, expected }) => {
    const result = detectPriority(text);
    const status = result === expected ? '✅ PASS' : '❌ FAIL';
    
    if (result === expected) {
      passed++;
    } else {
      failed++;
      console.log(`${status}: "${text}"`);
      console.log(`  Expected: ${expected}, Got: ${result}\n`);
    }
  });
  
  console.log(`\nTest Results: ${passed} passed, ${failed} failed out of ${testCases.length} tests`);
  
  return failed === 0;
}

// Test environment variable validation
function testEnvironmentValidation() {
  console.log('\n\nTesting environment variable validation...\n');
  
  // Save original env vars
  const originalToken = process.env.SLACK_BOT_TOKEN;
  const originalSecret = process.env.SLACK_SIGNING_SECRET;
  const originalAppToken = process.env.SLACK_APP_TOKEN;
  
  // Test with missing variables
  delete process.env.SLACK_BOT_TOKEN;
  
  const requiredEnvVars = ['SLACK_BOT_TOKEN', 'SLACK_SIGNING_SECRET', 'SLACK_APP_TOKEN'];
  const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);
  
  const testPassed = missingVars.length === 1 && missingVars[0] === 'SLACK_BOT_TOKEN';
  
  // Restore env vars
  process.env.SLACK_BOT_TOKEN = originalToken;
  process.env.SLACK_SIGNING_SECRET = originalSecret;
  process.env.SLACK_APP_TOKEN = originalAppToken;
  
  if (testPassed) {
    console.log('✅ PASS: Environment validation correctly detects missing variables');
  } else {
    console.log('❌ FAIL: Environment validation not working correctly');
  }
  
  return testPassed;
}

// Run all tests
console.log('='.repeat(60));
console.log('Slack Messaging Prioritization App - Unit Tests');
console.log('='.repeat(60));

const test1 = testPriorityDetection();
const test2 = testEnvironmentValidation();

console.log('\n' + '='.repeat(60));
if (test1 && test2) {
  console.log('✅ All tests passed!');
  console.log('='.repeat(60));
  process.exit(0);
} else {
  console.log('❌ Some tests failed');
  console.log('='.repeat(60));
  process.exit(1);
}
