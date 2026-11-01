import test from 'node:test';
import assert from 'node:assert/strict';
import { durationLabel, moveItem, validateShow, scheduledTime } from '../src/lib/show.mjs';

test('reordering preserves duplicate spots and does not mutate the original', () => {
  const original = ['ad', 'trailer', 'ad', 'film'];
  assert.deepEqual(moveItem(original, 2, 0), ['ad', 'ad', 'trailer', 'film']);
  assert.deepEqual(original, ['ad', 'trailer', 'ad', 'film']);
  assert.deepEqual(moveItem(original, 0, -1), original);
});
test('preflight refuses demo, missing media, empty queue, and invalid durations', () => {
  const video = { url: 'blob:video', duration: 90 };
  assert.equal(validateShow([video], 'display'), null);
  for (const items of [
    [],
    [{ ...video, demo: true }],
    [{ duration: 90 }],
    [{ ...video, duration: Infinity }],
  ])
    assert.ok(validateShow(items, 'display'));
  assert.ok(validateShow([video], ''));
});
test('schedules require a strictly future valid timestamp', () => {
  assert.throws(() => scheduledTime('invalid', 1000));
  assert.throws(() => scheduledTime('1970-01-01T00:00:01Z', 1000));
  assert.equal(scheduledTime('1970-01-01T00:00:02Z', 1000), 2000);
});
test('full film runtimes preserve hours', () => assert.equal(durationLabel(7542), '02:05:42'));
