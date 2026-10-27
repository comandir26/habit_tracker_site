import test from 'node:test'
import assert from 'node:assert/strict'
import { getLeaderboard } from '../src/api/leaderboard.js'

global.window = { localStorage: { getItem: () => 'test-token' } }
const member = { member_id: 1, user_id: 3, username: 'Focus', rank: 1, xp: 50, streak: 2, is_current_user: true }
const payload = { guild_id: 42, guild_name: 'Team', sort: 'xp', members: [member] }

test('leaderboard sends bearer token and chosen sort, preserving server ranks', async () => {
  for (const sort of ['xp', 'streak']) {
    global.fetch = async (url, options) => {
      assert.equal(url, `/api/guilds/42/leaderboard/?sort=${sort}`)
      assert.equal(options.headers.Authorization, 'Bearer test-token')
      return { ok: true, status: 200, json: async () => ({ ...payload, sort }) }
    }
    assert.deepEqual((await getLeaderboard(42, sort)).members, [member])
  }
})

test('leaderboard defaults to XP and accepts an empty list', async () => {
  global.fetch = async (url) => {
    assert.equal(url, '/api/guilds/42/leaderboard/?sort=xp')
    return { ok: true, status: 200, json: async () => ({ ...payload, members: [] }) }
  }
  assert.deepEqual((await getLeaderboard(42)).members, [])
})

test('invalid sort is rejected before requesting data', async () => {
  global.fetch = async () => { throw new Error('must not fetch') }
  await assert.rejects(getLeaderboard(42, 'name'), /Неизвестный порядок/)
})

test('access and server errors stay visible without demo fallback', async () => {
  for (const status of [401, 403, 404, 500]) {
    global.fetch = async () => ({ ok: false, status, json: async () => ({ detail: 'Unavailable' }) })
    await assert.rejects(getLeaderboard(42), (error) => error.status === status)
  }
  global.fetch = async () => { throw new TypeError('Network unavailable') }
  await assert.rejects(getLeaderboard(42), /Network unavailable/)
})

test('incomplete or invalid metrics fail instead of displaying invented progress', async () => {
  const invalid = [null, {}, { ...payload, sort: 'streak' }, { ...payload, members: [null] }]
  for (const fields of [{ xp: -1 }, { streak: 1.5 }, { rank: 0 }, { username: null }, { is_current_user: undefined }]) {
    invalid.push({ ...payload, members: [{ ...member, ...fields }] })
  }
  for (const result of invalid) {
    global.fetch = async () => ({ ok: true, status: 200, json: async () => result })
    await assert.rejects(getLeaderboard(42), /неполный рейтинг/)
  }
})
