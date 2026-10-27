import test from 'node:test'
import assert from 'node:assert/strict'
import {
  buildInviteLink, createInvite, formatInviteExpiry, getInvite, getInvites, isInviteActive, joinGuild, normalizeInviteCode,
} from '../src/api/invites.js'

const storage = new Map()
global.window = {
  location: { origin: 'https://inhabit.example' },
  sessionStorage: { getItem: (key) => storage.get(key), setItem: (key, value) => storage.set(key, value) },
  localStorage: { getItem: () => 'test-token' },
}

const hour = 3_600_000
const now = new Date('2026-10-25T12:00:00Z')

test('joining posts normalized code with authentication and returns first/repeated results', async () => {
  for (const created of [true, false]) {
    global.fetch = async (url, options) => {
      assert.equal(url, '/api/invites/AB3K9Q2M/join/')
      assert.equal(options.method, 'POST')
      assert.equal(options.headers.Authorization, 'Bearer test-token')
      return { ok: true, status: created ? 201 : 200, json: async () => ({ guild_id: 42, created }) }
    }
    assert.deepEqual(await joinGuild(' ab3k9q2m '), { guild_id: 42, created })
  }
})

test('invalid join codes fail before making a request', async () => {
  global.fetch = async () => { throw new Error('invalid code must not call API') }
  for (const code of ['', 'ABC', 'AB3K9Q2O', 'AB3K/Q2M', 'AB3K9Q2MEXTRA']) {
    await assert.rejects(joinGuild(code), (error) => error.status === 400 && /8 символов/.test(error.message))
  }
})

test('join errors explain expired and missing invites and preserve server failures', async () => {
  for (const [status, message] of [[404, /не найдено/], [410, /истёк/], [401, /Authentication/], [500, /Server error/]]) {
    global.fetch = async () => ({ ok: false, status, json: async () => ({ detail: status === 401 ? 'Authentication required' : 'Server error' }) })
    await assert.rejects(joinGuild('AB3K9Q2M'), (error) => error.status === status && message.test(error.message))
  }
  global.fetch = async () => { throw new Error('Network unavailable') }
  await assert.rejects(joinGuild('AB3K9Q2M'), /Network unavailable/)
})

test('invite codes are normalized and turned into shareable links', () => {
  assert.equal(normalizeInviteCode('  ab3k9q2m '), 'AB3K9Q2M')
  assert.equal(buildInviteLink('AB3K9Q2M'), 'https://inhabit.example/invite/AB3K9Q2M')
  assert.equal(buildInviteLink('AB 3/K', 'http://localhost:5173'), 'http://localhost:5173/invite/AB%203%2FK')
})

test('expiry is shown in hours on the last day and in days before that', () => {
  assert.equal(formatInviteExpiry(new Date(now.getTime() + 7 * 24 * hour).toISOString(), now), 'Действует ещё 7 дн.')
  assert.equal(formatInviteExpiry(new Date(now.getTime() + 25 * hour).toISOString(), now), 'Действует ещё 2 дн.')
  assert.equal(formatInviteExpiry(new Date(now.getTime() + 90 * 60_000).toISOString(), now), 'Действует ещё 2 ч')
  assert.equal(formatInviteExpiry(now.toISOString(), now), 'Срок действия истёк')
  assert.equal(isInviteActive({ expires_at: new Date(now.getTime() + 1).toISOString() }, now), true)
  assert.equal(isInviteActive({ expires_at: now.toISOString() }, now), false)
})

test('real creation sends the owner token and chosen lifetime to the guild endpoint', async () => {
  global.fetch = async (url, options) => {
    assert.equal(url, '/api/guilds/42/invites/')
    assert.equal(options.method, 'POST')
    assert.equal(options.headers.Authorization, 'Bearer test-token')
    assert.deepEqual(JSON.parse(options.body), { expires_in_days: 30 })
    return { ok: true, status: 201, json: async () => ({ id: 5, code: 'AB3K9Q2M' }) }
  }
  assert.equal((await createInvite('42', 30)).code, 'AB3K9Q2M')

  global.fetch = async (url, options) => {
    assert.deepEqual(JSON.parse(options.body), { expires_in_days: 7 })
    return { ok: true, status: 201, json: async () => ({ id: 6 }) }
  }
  assert.equal((await createInvite('42')).id, 6)
})

test('list accepts plain and paginated payloads and rejects incomplete ones', async () => {
  global.fetch = async (url) => {
    assert.equal(url, '/api/guilds/42/invites/')
    return { ok: true, status: 200, json: async () => [{ id: 1 }] }
  }
  assert.deepEqual(await getInvites('42'), [{ id: 1 }])

  global.fetch = async () => ({ ok: true, status: 200, json: async () => ({ results: [{ id: 2 }] }) })
  assert.deepEqual(await getInvites('42'), [{ id: 2 }])

  global.fetch = async () => ({ ok: true, status: 200, json: async () => ({}) })
  await assert.rejects(getInvites('42'), /неполный список приглашений/)
})

test('member errors stay visible and never fall back to demo invites', async () => {
  storage.clear()
  global.fetch = async () => ({ ok: false, status: 403, json: async () => ({ detail: 'Only the guild owner can manage invites.' }) })
  await assert.rejects(createInvite('42'), (error) => error.status === 403)
  await assert.rejects(getInvites('42'), (error) => error.status === 403)
  assert.equal(storage.get('inhabit.demoInvites'), undefined)
})

test('demo invites are stored locally with a valid code and requested lifetime', async () => {
  storage.clear()
  global.fetch = async () => { throw new Error('demo must not call the API') }
  const before = Date.now()
  const invite = await createInvite('demo', 1)

  assert.match(invite.code, /^[ABCDEFGHJKMNPQRSTUVWXYZ2-9]{8}$/)
  assert.ok(Math.abs(new Date(invite.expires_at) - before - 24 * hour) < 5_000)
  assert.deepEqual(await getInvites('demo'), [invite])

  const expired = { ...invite, id: 'old', expires_at: new Date(before - 1).toISOString() }
  storage.set('inhabit.demoInvites', JSON.stringify([invite, expired]))
  assert.deepEqual((await getInvites('demo')).map((item) => item.id), [invite.id])
})

test('preview normalizes the code and explains missing and expired invites', async () => {
  global.fetch = async (url) => {
    assert.equal(url, '/api/invites/AB3K9Q2M/')
    return { ok: true, status: 200, json: async () => ({ code: 'AB3K9Q2M', guild: { name: 'Focus' }, is_member: false }) }
  }
  assert.equal((await getInvite(' ab3k9q2m ')).guild.name, 'Focus')

  global.fetch = async () => ({ ok: false, status: 404, json: async () => ({ detail: 'Not found.' }) })
  await assert.rejects(getInvite('NOPE2345'), (error) => error.status === 404 && /не найдено/.test(error.message))

  global.fetch = async () => ({ ok: false, status: 410, json: async () => ({ detail: 'This invite has expired.' }) })
  await assert.rejects(getInvite('OLD23456'), (error) => error.status === 410 && /истёк/.test(error.message))

  global.fetch = async () => ({ ok: false, status: 500, json: async () => ({ detail: 'Server error' }) })
  await assert.rejects(getInvite('AB3K9Q2M'), (error) => error.status === 500 && error.message === 'Server error')
})
