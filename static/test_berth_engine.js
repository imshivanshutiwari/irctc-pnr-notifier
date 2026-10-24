/**
 * Unit Tests for RailPulse Berth Engine (static/berth_resolver.js)
 * Run with Node.js
 */
const assert = require('assert');
const BerthEngine = require('./berth_resolver.js');

console.log('=== Running RailPulse Berth Engine Unit Tests ===');

// 1. Class Normalization Tests
assert.strictEqual(BerthEngine.normalizeCoachClass('3A'), '3A');
assert.strictEqual(BerthEngine.normalizeCoachClass('THIRD AC'), '3A');
assert.strictEqual(BerthEngine.normalizeCoachClass('3 TIER'), '3A');
assert.strictEqual(BerthEngine.normalizeCoachClass('3E'), '3E');
assert.strictEqual(BerthEngine.normalizeCoachClass('ECONOMY 3 TIER'), '3E');
assert.strictEqual(BerthEngine.normalizeCoachClass('2A'), '2A');
assert.strictEqual(BerthEngine.normalizeCoachClass('1A'), '1A');
assert.strictEqual(BerthEngine.normalizeCoachClass('SL'), 'SL');
assert.strictEqual(BerthEngine.normalizeCoachClass('CC'), 'CC');
assert.strictEqual(BerthEngine.normalizeCoachClass('XYZ_UNKNOWN'), null);
console.log('✓ Class normalization passed');

// 2. Status Extraction Tests
const ex1 = BerthEngine.extractCoachBerth('CNF / B2 / 41 / MB');
assert.strictEqual(ex1.coach, 'B2');
assert.strictEqual(ex1.seat, 41);

const ex2 = BerthEngine.extractCoachBerth('CNF (S4/23)');
assert.strictEqual(ex2.coach, 'S4');
assert.strictEqual(ex2.seat, 23);

const ex3 = BerthEngine.extractCoachBerth('RLWL 7');
assert.strictEqual(ex3.coach, null);
assert.strictEqual(ex3.seat, null);

const ex4 = BerthEngine.extractCoachBerth('CNF');
assert.strictEqual(ex4.coach, null);
assert.strictEqual(ex4.seat, null);

const ex5 = BerthEngine.extractCoachBerth('CNF B5 34');
assert.strictEqual(ex5.coach, 'B5');
assert.strictEqual(ex5.seat, 34);
console.log('✓ Status extraction passed');

// 3. Sleeper (SL) / 3A (Modulo 8) Exhaustive Bay 1 Test
const slExpected = [
  { seat: 1, code: 'LB', name: 'Lower Berth' },
  { seat: 2, code: 'MB', name: 'Middle Berth' },
  { seat: 3, code: 'UB', name: 'Upper Berth' },
  { seat: 4, code: 'LB', name: 'Lower Berth' },
  { seat: 5, code: 'MB', name: 'Middle Berth' },
  { seat: 6, code: 'UB', name: 'Upper Berth' },
  { seat: 7, code: 'SL', name: 'Side Lower' },
  { seat: 8, code: 'SU', name: 'Side Upper' }
];

slExpected.forEach(item => {
  const res = BerthEngine.resolveBerthDetails('3A', item.seat, 'B1');
  assert.strictEqual(res.isSupported, true);
  assert.strictEqual(res.berthCode, item.code);
  assert.strictEqual(res.berthName, item.name);
  assert.strictEqual(res.bayNumber, 1);
});
console.log('✓ 3A / SL Bay 1 exhaustive mapping passed');

// Test higher seat in 3A (Seat 41)
// 41 = (5 * 8) + 1 -> Bay 6, Offset 1 -> Lower Berth
const seat41 = BerthEngine.resolveBerthDetails('3A', 41, 'B2');
assert.strictEqual(seat41.bayNumber, 6);
assert.strictEqual(seat41.berthCode, 'LB');
assert.strictEqual(seat41.bayBerths.length, 8);
console.log('✓ 3A Seat 41 mapping passed');

// 4. AC 3 Tier Economy (3E) Test with Side Middle (SM)
// 3E has 9 berths per bay!
const e7 = BerthEngine.resolveBerthDetails('3E', 7, 'M1');
assert.strictEqual(e7.berthCode, 'SL');
const e8 = BerthEngine.resolveBerthDetails('3E', 8, 'M1');
assert.strictEqual(e8.berthCode, 'SM'); // Side Middle!
assert.strictEqual(e8.berthName, 'Side Middle');
const e9 = BerthEngine.resolveBerthDetails('3E', 9, 'M1');
assert.strictEqual(e9.berthCode, 'SU'); // Side Upper!
console.log('✓ 3E Side Middle & 9-berth layout passed');

// 5. AC 2 Tier (2A) Test (No Middle Berths, 6 berths per bay)
const a2Expected = [
  { seat: 1, code: 'LB' },
  { seat: 2, code: 'UB' },
  { seat: 3, code: 'LB' },
  { seat: 4, code: 'UB' },
  { seat: 5, code: 'SL' },
  { seat: 6, code: 'SU' }
];
a2Expected.forEach(item => {
  const res = BerthEngine.resolveBerthDetails('2A', item.seat, 'A1');
  assert.strictEqual(res.isSupported, true);
  assert.strictEqual(res.berthCode, item.code);
  assert.strictEqual(res.bayNumber, 1);
});
console.log('✓ 2A 6-berth layout passed (no middle berths)');

// 6. First AC (1A) Safe Refusal Test (No guessing)
const firstAC = BerthEngine.resolveBerthDetails('1A', 4, 'H1');
assert.strictEqual(firstAC.isSupported, false);
assert.ok(firstAC.reason.includes('First AC'));
console.log('✓ 1A safe refusal without fake layout passed');

// 7. Invalid & Out-of-bounds Seat Tests
assert.strictEqual(BerthEngine.resolveBerthDetails('3A', 0, 'B1').isSupported, false);
assert.strictEqual(BerthEngine.resolveBerthDetails('3A', -5, 'B1').isSupported, false);
assert.strictEqual(BerthEngine.resolveBerthDetails('3A', 250, 'B1').isSupported, false);
console.log('✓ Out-of-bounds validation passed');

// 8. Multi-Passenger Proximity Tests
const togetherGroup = [
  { passenger_number: 1, current_status: 'CNF / B2 / 41' }, // Bay 6
  { passenger_number: 2, current_status: 'CNF / B2 / 42' }, // Bay 6
  { passenger_number: 3, current_status: 'CNF / B2 / 44' }  // Bay 6
];
const proxTogether = BerthEngine.evaluatePassengerProximity(togetherGroup, '3A');
assert.strictEqual(proxTogether.status, 'together');
assert.strictEqual(proxTogether.bayNumber, 6);

const splitBayGroup = [
  { passenger_number: 1, current_status: 'CNF / B2 / 41' }, // Bay 6
  { passenger_number: 2, current_status: 'CNF / B2 / 55' }  // Bay 7
];
const proxSplitBay = BerthEngine.evaluatePassengerProximity(splitBayGroup, '3A');
assert.strictEqual(proxSplitBay.status, 'split-bay');

const splitCoachGroup = [
  { passenger_number: 1, current_status: 'CNF / B1 / 41' },
  { passenger_number: 2, current_status: 'CNF / B2 / 41' }
];
const proxSplitCoach = BerthEngine.evaluatePassengerProximity(splitCoachGroup, '3A');
assert.strictEqual(proxSplitCoach.status, 'split-coach');

const pendingGroup = [
  { passenger_number: 1, current_status: 'CNF' }, // No berth yet!
  { passenger_number: 2, current_status: 'WL 5' }
];
const proxPending = BerthEngine.evaluatePassengerProximity(pendingGroup, '3A');
assert.strictEqual(proxPending.status, 'pending');

console.log('✓ Multi-passenger proximity evaluations passed');
// 9. Chair Car (CC) & Vande Bharat / Shatabdi Seat Layout Tests
const ccSeat19 = BerthEngine.resolveBerthDetails('CC', 19, 'C3');
assert.strictEqual(ccSeat19.isSupported, true);
assert.strictEqual(ccSeat19.berthCode, 'WS');
assert.strictEqual(ccSeat19.berthName, 'Window Seat');

// Test authoritative berth_code override (e.g. from IRCTC PRS)
const ccOverride = BerthEngine.resolveBerthDetails('CC', 19, 'C3', 'WS');
assert.strictEqual(ccOverride.berthCode, 'WS');
assert.strictEqual(ccOverride.berthName, 'Window Seat');

console.log('✓ CC Chair Car Seat 19 Window Seat & authoritative override passed');
console.log('=== ALL 9 TEST SUITES IN BERTH ENGINE PASSED! ===');
