import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useLoginStore } from './LoginStore'

describe('LoginStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('exposes default state', () => {
    const store = useLoginStore()
    expect(store.loggedInUser).toEqual({})
    expect(store.groups).toEqual([])
    expect(store.showRightDrawer).toBe(false)
    expect(store.triggerPopup).toBe(false)
    expect(store.initialPage).toBe(false)
    expect(store.savedForms).toEqual({ jobs: {}, files: {} })
    expect(store.users.length).toBe(20)
  })

  it('loggedInGroup returns the sole group when exactly one is present', () => {
    const store = useLoginStore()
    store.groups = [{ id: 42, name: 'only' }] as never
    expect(store.loggedInGroup).toEqual({ id: 42, name: 'only' })
  })

  it('loggedInGroup returns empty string when multiple groups are present', () => {
    const store = useLoginStore()
    store.groups = [{ id: 1 }, { id: 2 }] as never
    expect(store.loggedInGroup).toBe('')
  })

  it('loggedInGroup returns empty string when no groups are present', () => {
    const store = useLoginStore()
    expect(store.loggedInGroup).toBe('')
  })

  it('state is reactive and mutable', () => {
    const store = useLoginStore()
    store.loggedInUser = { username: 'alice' }
    store.showRightDrawer = true
    store.selectedSnapshot = { id: 1 }
    store.triggerPopup = true
    store.initialPage = true
    store.savedForms = { jobs: { a: 1 }, files: { b: 2 } } as never
    expect(store.loggedInUser).toEqual({ username: 'alice' })
    expect(store.showRightDrawer).toBe(true)
    expect(store.selectedSnapshot).toEqual({ id: 1 })
    expect(store.triggerPopup).toBe(true)
    expect(store.initialPage).toBe(true)
  })

  it('users seed list has the expected permission flags', () => {
    const store = useLoginStore()
    const owners = store.users.filter((u) => u.owner === true)
    expect(owners.map((u) => u.name).sort()).toEqual(['Larry', 'Sam', 'Tatum'])
  })
})
