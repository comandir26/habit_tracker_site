import test from 'node:test'
import assert from 'node:assert/strict'
import { getProfile } from '../src/api/profile.js'

global.window = { localStorage: { getItem: () => 'test-token' } }
const profile = { id: 1, username: 'alex', total_xp: 200, level: 3, streak: 2, xp_in_level: 0, xp_per_level: 100, xp_to_next_level: 100 }

test('profile requests authenticated personal progress and accepts a new user', async () => {
  for (const payload of [profile, { ...profile, total_xp: 0, level: 1, streak: 0 }]) {
    global.fetch = async (url, options) => {
      assert.equal(url, '/api/auth/profile/')
      assert.equal(options.headers.Authorization, 'Bearer test-token')
      return { ok: true, status: 200, json: async () => payload }
    }
    assert.deepEqual(await getProfile(), payload)
  }
})

test('profile preserves authorization, server and network errors', async () => {
  for (const status of [401, 403, 500]) {
    global.fetch = async () => ({ ok: false, status, json: async () => ({ detail: 'Unavailable' }) })
    await assert.rejects(getProfile(), (error) => error.status === status)
  }
  global.fetch = async () => { throw new TypeError('Network unavailable') }
  await assert.rejects(getProfile(), /Network unavailable/)
})

test('incomplete and invalid profile values are rejected', async () => {
  for (const payload of [null, {}, ...[{ total_xp: -1 }, { level: 0 }, { streak: 1.5 },
    { username: null }, { xp_in_level: 100 }, { xp_per_level: 0 }, { xp_to_next_level: 0 }]
    .map((fields) => ({ ...profile, ...fields }))]) {
    global.fetch = async () => ({ ok: true, status: 200, json: async () => payload })
    await assert.rejects(getProfile(), /неполный профиль/)
  }
})
