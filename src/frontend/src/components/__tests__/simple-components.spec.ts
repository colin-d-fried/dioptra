import { describe, it, expect, vi, beforeEach } from 'vitest'

const { axiosMock } = vi.hoisted(() => ({
  axiosMock: {
    get: vi.fn().mockResolvedValue({ data: { data: [] } }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    put: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
    postForm: vi.fn().mockResolvedValue({ data: {} }),
    interceptors: { request: { use: vi.fn() } },
  },
}))

vi.mock('axios', () => ({ default: axiosMock }))
vi.mock('vue-router', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('vue-router')
  return {
    ...actual,
    useRoute: () => ({
      name: 'home',
      path: '/',
      params: {},
      query: {},
      meta: {},
    }),
    useRouter: () => ({
      push: vi.fn(),
      replace: vi.fn(),
      beforeEach: vi.fn(),
    }),
  }
})

import { shallowMount } from '@vue/test-utils'
import { defaultGlobal } from '../../../tests/helpers'

import PageTitle from '../PageTitle.vue'
import KeyValueTable from '../KeyValueTable.vue'
import JobStatus from '../JobStatus.vue'
import BasicTable from '../BasicTable.vue'
import AccessibilityTest from '../AccessibilityTest.vue'

beforeEach(() => {
  axiosMock.get.mockClear()
  axiosMock.get.mockResolvedValue({ data: { data: [] } })
})

describe('PageTitle', () => {
  it('mounts and renders the title', () => {
    const w = shallowMount(PageTitle, {
      global: defaultGlobal(),
      props: { title: 'Hello' },
    })
    expect(w.exists()).toBe(true)
    expect(w.html()).toContain('Hello')
  })

  it('renders the draft badge when draftLabel is provided', () => {
    const w = shallowMount(PageTitle, {
      global: defaultGlobal(),
      props: { title: 'T', draftLabel: 'Draft' },
    })
    expect(w.html().toLowerCase()).toContain('draft')
  })
})

describe('KeyValueTable', () => {
  it('renders one row per entry with label + value', () => {
    const rows = [
      { label: 'Name', value: 'Alice' },
      { label: 'Age', value: 30 },
    ]
    const w = shallowMount(KeyValueTable, {
      props: { rows },
      global: defaultGlobal(),
    })
    const html = w.html()
    expect(html).toContain('Name')
    expect(html).toContain('Alice')
    expect(html).toContain('Age')
    expect(html).toContain('30')
    expect(w.findAll('tr').length).toBe(2)
  })

  it('applies the no-pointer class when disabled=true', () => {
    const w = shallowMount(KeyValueTable, {
      props: { rows: [{ label: 'L', value: 'V' }], disabled: true },
      global: defaultGlobal(),
    })
    expect(w.find('table').classes()).toContain('no-pointer')
  })

  it('applies full-width style on the second column when secondColumnFullWidth=true', () => {
    const w = shallowMount(KeyValueTable, {
      props: {
        rows: [{ label: 'L', value: 'V' }],
        secondColumnFullWidth: true,
      },
      global: defaultGlobal(),
    })
    const secondTd = w.findAll('td')[1]
    expect(secondTd.attributes('style')).toContain('width: 100%')
  })
})

describe('JobStatus', () => {
  it.each(['finished', 'queued', 'started', 'failed'] as const)(
    'mounts with the "%s" status value without throwing',
    (status) => {
      const w = shallowMount(JobStatus, {
        props: { status },
        global: defaultGlobal(),
      })
      expect(w.exists()).toBe(true)
    },
  )

  it('does not render a chip for an unknown status', () => {
    const w = shallowMount(JobStatus, {
      props: { status: 'unknown' },
      global: defaultGlobal(),
    })
    // v-if is false, so the root should be a comment placeholder
    expect(w.find('q-chip-stub').exists()).toBe(false)
  })
})

describe('BasicTable', () => {
  it('mounts without error given empty rows/columns', () => {
    const w = shallowMount(BasicTable, {
      props: {
        rows: [],
        columns: [],
        title: '',
      },
      global: defaultGlobal(),
    })
    expect(w.exists()).toBe(true)
  })
})

describe('AccessibilityTest', () => {
  it('mounts without error', () => {
    const w = shallowMount(AccessibilityTest, { global: defaultGlobal() })
    expect(w.exists()).toBe(true)
  })
})
