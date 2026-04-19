import { vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

export function mockRoute(overrides: Record<string, unknown> = {}) {
  return {
    name: 'home',
    path: '/',
    params: {},
    query: {},
    meta: {},
    ...overrides,
  }
}

export function mockRouter() {
  return {
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    go: vi.fn(),
    beforeEach: vi.fn(),
    currentRoute: { value: mockRoute() },
  }
}

export function freshPinia() {
  const pinia = createPinia()
  setActivePinia(pinia)
  return pinia
}

export const defaultGlobal = () => ({
  plugins: [freshPinia()],
  provide: {
    darkMode: false,
  },
  stubs: {
    'router-link': true,
    'router-view': true,
    transition: false,
  },
  mocks: {
    $route: mockRoute(),
    $router: mockRouter(),
    $q: {
      notify: vi.fn(),
      dark: { isActive: false, set: vi.fn() },
      dialog: vi.fn(),
      loading: { show: vi.fn(), hide: vi.fn() },
    },
  },
})
