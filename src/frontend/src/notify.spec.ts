import { describe, it, expect, vi, beforeEach } from 'vitest'

const { createMock } = vi.hoisted(() => ({ createMock: vi.fn((opts: unknown) => opts) }))

vi.mock('quasar', () => ({
  Notify: { create: createMock },
  Quasar: { install: () => undefined },
}))

import { success, error, info, wait } from './notify'

describe('notify', () => {
  beforeEach(() => {
    createMock.mockClear()
  })

  it('success() uses green icon+color and forwards the message', () => {
    success('hi')
    expect(createMock).toHaveBeenCalledOnce()
    expect(createMock.mock.calls[0][0]).toMatchObject({
      color: 'green-7',
      textColor: 'white',
      icon: 'done',
      message: 'hi',
    })
  })

  it('error() uses red color and warning icon', () => {
    error('bad')
    expect(createMock.mock.calls[0][0]).toMatchObject({
      color: 'red-5',
      icon: 'warning',
      message: 'bad',
    })
  })

  it('info() uses blue color and info icon', () => {
    info('fyi')
    expect(createMock.mock.calls[0][0]).toMatchObject({
      color: 'blue-5',
      icon: 'info',
      message: 'fyi',
    })
  })

  it('wait() returns a spinner notification with no auto-timeout', () => {
    wait('loading…')
    const opts = createMock.mock.calls[0][0] as Record<string, unknown>
    expect(opts.spinner).toBe(true)
    expect(opts.timeout).toBe(0)
    expect(opts.message).toBe('loading…')
    expect(opts.color).toBe('blue-5')
  })
})
