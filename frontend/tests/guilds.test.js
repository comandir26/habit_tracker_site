import test from 'node:test'
import assert from 'node:assert/strict'
import { getGuilds } from '../src/api/guilds.js'

global.window = { localStorage: { getItem: () => 'account-token' } }
const guild = { id: 42, name: 'Моя команда', is_owner: true, members: [{ id: 7, username: 'owner', xp: 20 }] }

test('my guilds loads the authenticated list and preserves navigation IDs and owner permissions', async () => {
  global.fetch = async (url, options) => {
    assert.equal(url, '/api/guilds/')
    assert.equal(options.headers.Authorization, 'Bearer account-token')
    return { ok: true, status: 200, json: async () => [guild, { ...guild, id: 43, is_owner: false }] }
  }
  const guilds = await getGuilds()
  assert.deepEqual(guilds.map(({ id, isOwner }) => ({ id, isOwner })), [{ id: 42, isOwner: true }, { id: 43, isOwner: false }])
  assert.equal(guilds[0].members[0].name, 'owner')
})

test('my guilds accepts empty and wrapped lists and rejects incomplete responses', async () => {
  for (const payload of [[], { results: [] }]) {
    global.fetch = async () => ({ ok: true, status: 200, json: async () => payload })
    assert.deepEqual(await getGuilds(), [])
  }
  for (const payload of [{}, { results: [{}] }, null]) {
    global.fetch = async () => ({ ok: true, status: 200, json: async () => payload })
    await assert.rejects(getGuilds(), /неполный список/)
  }
})

test('my guilds keeps authentication and network errors visible without demo fallback', async () => {
  for (const status of [401, 403, 500]) {
    global.fetch = async () => ({ ok: false, status, json: async () => ({ detail: 'Unavailable' }) })
    await assert.rejects(getGuilds(), (error) => error.status === status)
  }
  global.fetch = async () => { throw new TypeError('Network unavailable') }
  await assert.rejects(getGuilds(), /Network unavailable/)
})
