import test from 'node:test'
import assert from 'node:assert/strict'
import { completeHabit, createHabit, getHabits, getHabitDifficulties } from '../src/api/habits.js'
import { habitSchedule, validateHabit } from '../src/api/habitOptions.js'

const storage = new Map()
global.window = {
  sessionStorage: { getItem: (key) => storage.get(key), setItem: (key, value) => storage.set(key, value) },
  localStorage: { getItem: () => 'test-token' },
}

const habit = { name: 'Читать', schedule: 'weekdays', weekdays: [1, 5], difficulty: 'hard', xp_weight: 4 }

test('weekday schedule uses ISO weekday order and validates empty days and fractional weights', () => {
  assert.equal(habitSchedule(habit), 'Пн, Пт')
  assert.equal(habitSchedule({ schedule: 'daily' }), 'Каждый день')
  assert.deepEqual(validateHabit(habit), {})
  assert.deepEqual(Object.keys(validateHabit({ ...habit, weekdays: [], xp_weight: 1.5 })), ['weekdays', 'xp_weight'])
  assert.ok(validateHabit({ ...habit, name: '  ' }).name)
  assert.ok(validateHabit({ ...habit, name: 'x'.repeat(121) }).name)
  assert.deepEqual(validateHabit({ ...habit, name: 'x'.repeat(120) }), {})
})

test('explicit demo stores habits locally and computes XP from difficulty and weight', async () => {
  storage.clear()
  const created = await createHabit('demo', habit)
  assert.equal(created.xp_reward, 120)
  assert.equal(created.guild, 'demo')
  assert.deepEqual(await getHabits('demo'), [created])
  assert.equal((await getHabitDifficulties('demo')).length, 3)
})

test('real guild errors remain visible and cannot produce local demo success', async () => {
  const before = storage.get('inhabit.demoHabits')
  global.fetch = async () => ({ ok: false, status: 403, json: async () => ({ detail: 'Access denied' }) })
  await assert.rejects(createHabit('42', habit), (error) => error.status === 403)
  await assert.rejects(getHabits('42'), (error) => error.status === 403)
  global.fetch = async () => { throw new TypeError('Network unavailable') }
  await assert.rejects(createHabit('42', habit), /Network unavailable/)
  assert.equal(storage.get('inhabit.demoHabits'), before)
})

test('real creation sends token, guild path and habit fields; list accepts pagination', async () => {
  global.fetch = async (url, options) => {
    assert.equal(url, '/api/guilds/42/habits/')
    assert.equal(options.headers.Authorization, 'Token test-token')
    if (options.method === 'POST') {
      assert.deepEqual(JSON.parse(options.body), habit)
      return { ok: true, status: 201, json: async () => ({ ...habit, id: 7, xp_reward: 120 }) }
    }
    return { ok: true, status: 200, json: async () => ({ results: [{ id: 7 }] }) }
  }
  assert.equal((await createHabit('42', habit)).id, 7)
  assert.deepEqual(await getHabits('42'), [{ id: 7 }])
})

test('completion uses its dedicated API endpoint and demo completion is idempotent', async () => {
  global.fetch = async (url, options) => {
    assert.equal(url, '/api/habits/7/complete/')
    assert.equal(options.method, 'POST')
    assert.deepEqual(JSON.parse(options.body), {})
    return { ok: true, status: 200, json: async () => ({ created: true, awarded_xp: 120, member_id: 3, member_xp: 120 }) }
  }
  assert.equal((await completeHabit('42', { id: 7 })).awarded_xp, 120)

  storage.clear()
  const demoHabit = { id: 'demo-habit', xp_reward: 20 }
  const first = await completeHabit('demo', demoHabit)
  const retry = await completeHabit('demo', demoHabit)
  assert.equal(first.created, true)
  assert.equal(first.awarded_xp, 20)
  assert.equal(first.member_id, '1')
  assert.equal(retry.created, false)
  assert.equal(retry.awarded_xp, 0)
})
