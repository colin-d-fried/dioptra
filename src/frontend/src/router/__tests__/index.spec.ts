/**
 * Router unit tests: import the router module, verify the expected route
 * shape (names, paths, param slots, meta), and exercise the navigation
 * guard with stubbed LoginStore/dataApi.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/services/dataApi', () => ({
  getLoginStatus: vi.fn(),
}))

import router from '../index'
import { useLoginStore } from '@/stores/LoginStore'
import { getLoginStatus } from '@/services/dataApi'

const getLoginStatusMock = vi.mocked(getLoginStatus)

describe('router', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    getLoginStatusMock.mockReset()
  })

  it('registers the home route at "/"', () => {
    const home = router.resolve('/')
    expect(home.matched.length).toBeGreaterThan(0)
    expect(home.name).toBe('home')
  })

  it('registers the jobs route with experiment+job params', () => {
    const r = router.resolve({
      name: 'createExperimentJob',
      params: { id: '1', jobId: '2' },
    })
    expect(r.matched.length).toBeGreaterThan(0)
    expect(r.params).toMatchObject({ id: '1', jobId: '2' })
  })

  it('exposes the common named routes', () => {
    const names = router
      .getRoutes()
      .map((r) => r.name)
      .filter(Boolean) as string[]
    expect(names).toEqual(
      expect.arrayContaining([
        'home',
        'experiments',
        'entrypoints',
        'plugins',
        'queues',
        'models',
        'tags',
      ]),
    )
  })

  it('tags experiment routes with meta.type="experiments"', () => {
    const r = router.resolve('/experiments')
    const meta = r.matched.map((m) => m.meta).find((m) => m.type === 'experiments')
    expect(meta).toBeDefined()
  })

  it('resolves route query params via /?snapshot=5', () => {
    const r = router.resolve('/?snapshot=5')
    expect(r.query.snapshot).toBe('5')
  })

  it('global beforeEach: populates loggedInUser + groups when getLoginStatus resolves', async () => {
    getLoginStatusMock.mockResolvedValue({
      data: { username: 'admin', groups: [{ id: 1, name: 'admins' }] },
    } as never)
    const store = useLoginStore()
    await router.push('/')
    await router.isReady()
    expect(getLoginStatusMock).toHaveBeenCalled()
    expect((store.loggedInUser as { username: string }).username).toBe('admin')
    expect(store.groups).toEqual([{ id: 1, name: 'admins' }])
  })

  it('global beforeEach closes the snapshot drawer and toggles initialPage', async () => {
    getLoginStatusMock.mockResolvedValue({ data: { username: 'u', groups: [] } } as never)
    const store = useLoginStore()
    store.showRightDrawer = true
    store.selectedSnapshot = 42
    await router.push('/plugins')
    await router.isReady()
    expect(store.showRightDrawer).toBe(false)
    expect(store.selectedSnapshot).toBeNull()
    // second nav is not START_LOCATION, so initialPage should flip to false
    await router.push('/queues')
    expect(store.initialPage).toBe(false)
  })
})
