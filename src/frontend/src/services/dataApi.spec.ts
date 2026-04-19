import { describe, it, expect, vi, beforeEach } from 'vitest'

const { axiosMock } = vi.hoisted(() => ({
  axiosMock: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    postForm: vi.fn(),
    interceptors: { request: { use: vi.fn() } },
  },
}))

vi.mock('axios', () => ({
  default: axiosMock,
}))

import * as api from './dataApi'

const ok = (data: unknown = {}) => ({ data })

describe('dataApi', () => {
  beforeEach(() => {
    axiosMock.get.mockReset()
    axiosMock.post.mockReset()
    axiosMock.put.mockReset()
    axiosMock.delete.mockReset()
    axiosMock.postForm.mockReset()
  })

  describe('getData', () => {
    it('hits /api/<type>/ with paginated params when showDrafts=false', async () => {
      axiosMock.get.mockResolvedValueOnce(ok({ data: [] }))
      await api.getData('plugins', {
        rowsPerPage: 10,
        index: 2,
        sortBy: 'name',
        descending: true,
        search: 'foo',
      })
      expect(axiosMock.get).toHaveBeenCalledWith('/api/plugins/', {
        params: {
          index: 2,
          pageLength: 10,
          search: 'foo',
          draftType: '',
          sortBy: 'name',
          descending: true,
        },
      })
    })

    it('uses pageLength=100 when rowsPerPage=0 (GET ALL)', async () => {
      axiosMock.get.mockResolvedValueOnce(ok({ data: [1, 2], next: null }))
      await api.getData('plugins', {
        rowsPerPage: 0,
        index: 0,
        sortBy: '',
        descending: false,
        search: '',
      })
      expect(axiosMock.get.mock.calls[0][1].params.pageLength).toBe(100)
    })

    it('follows .next links when paginating "all"', async () => {
      axiosMock.get
        .mockResolvedValueOnce(ok({ data: [1, 2], next: '/v1/api/plugins/?page=2' }))
        .mockResolvedValueOnce(ok({ data: [3], next: null }))
      const res = await api.getData('plugins', {
        rowsPerPage: 0,
        index: 0,
        sortBy: '',
        descending: false,
        search: '',
      })
      expect(axiosMock.get).toHaveBeenCalledTimes(2)
      expect(res.data.data).toEqual([1, 2, 3])
    })

    it('merges draft payload onto each row when showDrafts=true', async () => {
      axiosMock.get.mockResolvedValueOnce(
        ok({ data: [{ id: 1, payload: { name: 'a' } }] }),
      )
      const res = await api.getData(
        'plugins',
        {
          rowsPerPage: 10,
          index: 0,
          sortBy: '',
          descending: false,
          search: '',
        },
        true,
      )
      expect(axiosMock.get.mock.calls[0][0]).toBe('/api/plugins/drafts/')
      expect(axiosMock.get.mock.calls[0][1].params.draftType).toBe('new')
      expect(res.data.data[0].name).toBe('a')
    })
  })

  describe('getSnapshots + getSnapshot', () => {
    it('hits /api/<type>/<id>/snapshots and follows .next', async () => {
      axiosMock.get
        .mockResolvedValueOnce(ok({ data: [1], next: '/v1/api/plugins/5/snapshots?page=2' }))
        .mockResolvedValueOnce(ok({ data: [2], next: null }))
      const res = await api.getSnapshots('plugins', 5)
      expect(axiosMock.get.mock.calls[0][0]).toBe('/api/plugins/5/snapshots')
      expect(res.data.data).toEqual([1, 2])
    })

    it('getSnapshot targets a single snapshot id', async () => {
      axiosMock.get.mockResolvedValueOnce(ok({ id: 9 }))
      await api.getSnapshot('plugins', 5, 9)
      expect(axiosMock.get).toHaveBeenCalledWith('/api/plugins/5/snapshots/9')
    })
  })

  describe('job metrics', () => {
    it('addJobMetric posts to /api/jobs/<id>/metrics', async () => {
      axiosMock.post.mockResolvedValueOnce(ok())
      await api.addJobMetric('7', 'loss', 0.5, 3)
      expect(axiosMock.post).toHaveBeenCalledWith('/api/jobs/7/metrics', {
        name: 'loss',
        value: 0.5,
        step: 3,
      })
    })

    it('getJobMetricHistory pages through all metrics', async () => {
      axiosMock.get
        .mockResolvedValueOnce(ok({ data: [1], next: '/v1/api/jobs/7/metrics/loss/snapshots?page=2' }))
        .mockResolvedValueOnce(ok({ data: [2], next: null }))
      const res = await api.getJobMetricHistory('7', 'loss')
      expect(res.data.data).toEqual([1, 2])
    })

    it('getJobMetrics issues a single GET for the given job id', async () => {
      axiosMock.get.mockResolvedValueOnce(ok({ metrics: [] }))
      await api.getJobMetrics(3)
      expect(axiosMock.get).toHaveBeenCalledWith('/api/jobs/3/metrics')
    })
  })

  describe('jobs for an experiment', () => {
    it('getJobs hits /api/experiments/<id>/jobs with paginated params', async () => {
      axiosMock.get.mockResolvedValueOnce(ok({ data: [] }))
      await api.getJobs(3, {
        rowsPerPage: 25,
        index: 1,
        sortBy: 'createdAt',
        descending: true,
        search: '',
      })
      expect(axiosMock.get.mock.calls[0][0]).toBe('/api/experiments/3/jobs')
      expect(axiosMock.get.mock.calls[0][1].params.pageLength).toBe(25)
    })

    it('getJobs follows .next when rowsPerPage=0', async () => {
      axiosMock.get
        .mockResolvedValueOnce(ok({ data: [1], next: '/v1/api/experiments/3/jobs?p=2' }))
        .mockResolvedValueOnce(ok({ data: [2], next: null }))
      const res = await api.getJobs(3, {
        rowsPerPage: 0,
        index: 0,
        sortBy: '',
        descending: false,
        search: '',
      })
      expect(res.data.data).toEqual([1, 2])
    })

    it('addJob posts to /api/experiments/<id>/jobs', async () => {
      axiosMock.post.mockResolvedValueOnce(ok())
      await api.addJob(3, {
        description: 'd',
        queue: 1,
        entrypoint: 2,
        values: { k: 'v' },
        timeout: '1h',
      })
      expect(axiosMock.post).toHaveBeenCalledWith(
        '/api/experiments/3/jobs',
        expect.objectContaining({ description: 'd', queue: 1, entrypoint: 2, timeout: '1h' }),
      )
    })

    it('deleteJob deletes /api/experiments/<id>/jobs/<jobId>', async () => {
      axiosMock.delete.mockResolvedValueOnce(ok())
      await api.deleteJob(3, 7)
      expect(axiosMock.delete).toHaveBeenCalledWith('/api/experiments/3/jobs/7')
    })
  })

  describe('getJobLogs', () => {
    it('passes severity array and paramsSerializer config', async () => {
      axiosMock.get.mockResolvedValueOnce(ok({ data: [] }))
      await api.getJobLogs(
        1,
        { rowsPerPage: 10, index: 0, sortBy: '', descending: false, search: '' },
        ['INFO', 'WARNING'],
      )
      const args = axiosMock.get.mock.calls[0][1]
      expect(args.params.severity).toEqual(['INFO', 'WARNING'])
      expect(args.paramsSerializer.indexes).toBeNull()
    })

    it('defaults severity to null when not provided', async () => {
      axiosMock.get.mockResolvedValueOnce(ok({ data: [] }))
      await api.getJobLogs(1, {
        rowsPerPage: 10,
        index: 0,
        sortBy: '',
        descending: false,
        search: '',
      })
      expect(axiosMock.get.mock.calls[0][1].params.severity).toBeNull()
    })
  })

  describe('items', () => {
    it('getItem hits the resource endpoint and merges draft payload when isDraft=true', async () => {
      axiosMock.get.mockResolvedValueOnce(ok({ id: 5, payload: { name: 'draft' } }))
      const res = await api.getItem('plugins', 5, true)
      expect(axiosMock.get).toHaveBeenCalledWith('/api/plugins/drafts/5')
      expect(res.data.name).toBe('draft')
    })

    it('getItem uses the regular endpoint when isDraft=false (default)', async () => {
      axiosMock.get.mockResolvedValueOnce(ok({ id: 5 }))
      await api.getItem('plugins', 5)
      expect(axiosMock.get).toHaveBeenCalledWith('/api/plugins/5')
    })

    it('getResourceDraft merges payload fields into res.data', async () => {
      axiosMock.get.mockResolvedValueOnce(ok({ payload: { name: 'n' } }))
      const res = await api.getResourceDraft('plugins', 5)
      expect(res.data.name).toBe('n')
    })

    it('addItem / updateItem / deleteItem hit the expected verbs + paths', async () => {
      axiosMock.post.mockResolvedValueOnce(ok())
      axiosMock.put.mockResolvedValueOnce(ok())
      axiosMock.delete.mockResolvedValueOnce(ok())
      await api.addItem('plugins', { name: 'p', description: '', group: 1 })
      await api.updateItem('plugins', 5, { name: 'p', description: '' })
      await api.deleteItem('plugins', 5)
      expect(axiosMock.post.mock.calls[0][0]).toBe('/api/plugins/')
      expect(axiosMock.put.mock.calls[0][0]).toBe('/api/plugins/5')
      expect(axiosMock.delete.mock.calls[0][0]).toBe('/api/plugins/5')
    })
  })

  describe('drafts', () => {
    it('addDraft posts to /<type>/<id>/draft when id is truthy', async () => {
      axiosMock.post.mockResolvedValueOnce(ok())
      await api.addDraft('plugins', { name: 'p', description: '', group: 1 }, 5)
      expect(axiosMock.post).toHaveBeenCalledWith('/api/plugins/5/draft', expect.anything())
    })

    it('addDraft posts to /<type>/drafts/ when id is 0/falsy', async () => {
      axiosMock.post.mockResolvedValueOnce(ok())
      await api.addDraft('plugins', { name: 'p', description: '', group: 1 }, 0)
      expect(axiosMock.post).toHaveBeenCalledWith('/api/plugins/drafts/', expect.anything())
    })

    it('updateDraft puts to /<type>/drafts/<draftId>', async () => {
      axiosMock.put.mockResolvedValueOnce(ok())
      await api.updateDraft('plugins', 'abc', { name: 'p', description: '' })
      expect(axiosMock.put).toHaveBeenCalledWith('/api/plugins/drafts/abc', expect.anything())
    })

    it('updateDraftLinkedtoQueue wraps the payload under resourceData', async () => {
      axiosMock.put.mockResolvedValueOnce(ok())
      await api.updateDraftLinkedtoQueue(1, 'q', 'd', 99)
      expect(axiosMock.put).toHaveBeenCalledWith('/api/queues/1/draft', {
        resourceSnapshot: 99,
        resourceData: { name: 'q', description: 'd' },
      })
    })

    it('deleteDraft + deleteResourceDraft hit the right endpoints', async () => {
      axiosMock.delete.mockResolvedValueOnce(ok()).mockResolvedValueOnce(ok())
      await api.deleteDraft('plugins', 5)
      await api.deleteResourceDraft('plugins', 5)
      expect(axiosMock.delete.mock.calls[0][0]).toBe('/api/plugins/drafts/5')
      expect(axiosMock.delete.mock.calls[1][0]).toBe('/api/plugins/5/draft')
    })

    it('convertToResource posts to workflows/draftCommit', async () => {
      axiosMock.post.mockResolvedValueOnce(ok())
      await api.convertToResource(7)
      expect(axiosMock.post).toHaveBeenCalledWith('/api/workflows/draftCommit/7')
    })
  })

  describe('plugin files', () => {
    it('getFiles paginates and follows .next on rowsPerPage=0', async () => {
      axiosMock.get
        .mockResolvedValueOnce(ok({ data: [1], next: '/v1/api/plugins/1/files?p=2' }))
        .mockResolvedValueOnce(ok({ data: [2], next: null }))
      const res = await api.getFiles(1, {
        rowsPerPage: 0,
        index: 0,
        sortBy: '',
        descending: false,
        search: '',
      })
      expect(res.data.data).toEqual([1, 2])
    })

    it('getFile + getFileSnapshot hit the expected paths', async () => {
      axiosMock.get.mockResolvedValueOnce(ok()).mockResolvedValueOnce(ok())
      await api.getFile('p1', 'f1')
      await api.getFileSnapshot('p1', 'f1', 5)
      expect(axiosMock.get.mock.calls[0][0]).toBe('/api/plugins/p1/files/f1')
      expect(axiosMock.get.mock.calls[1][0]).toBe('/api/plugins/p1/files/f1/snapshots/5')
    })

    it('addFile / updateFile / deleteFile hit the expected verbs + paths', async () => {
      axiosMock.post.mockResolvedValueOnce(ok())
      axiosMock.put.mockResolvedValueOnce(ok())
      axiosMock.delete.mockResolvedValueOnce(ok())
      await api.addFile(1, { filename: 'a', contents: '', description: '', tasks: [] })
      await api.updateFile(1, 'f1', { filename: 'a', contents: '', description: '', tasks: [] })
      await api.deleteFile('p1', 'f1')
      expect(axiosMock.post.mock.calls[0][0]).toBe('/api/plugins/1/files')
      expect(axiosMock.put.mock.calls[0][0]).toBe('/api/plugins/1/files/f1')
      expect(axiosMock.delete.mock.calls[0][0]).toBe('/api/plugins/p1/files/f1')
    })
  })

  describe('tags', () => {
    it('updateTags routes plugin-files tags through /plugins/<id>/files/<fileId>/tags/', async () => {
      axiosMock.put.mockResolvedValueOnce(ok())
      await api.updateTags('files', 1, [2, 3], 9)
      expect(axiosMock.put).toHaveBeenCalledWith('/api/plugins/1/files/9/tags/', { ids: [2, 3] })
    })

    it('updateTags routes other types through /<type>/<id>/tags', async () => {
      axiosMock.put.mockResolvedValueOnce(ok())
      await api.updateTags('plugins', 1, [2, 3])
      expect(axiosMock.put).toHaveBeenCalledWith('/api/plugins/1/tags', { ids: [2, 3] })
    })
  })

  describe('artifacts + files', () => {
    it('addArtifact posts to the nested artifacts endpoint', async () => {
      axiosMock.post.mockResolvedValueOnce(ok())
      await api.addArtifact('1', '2', { description: 'd', uri: 'u' })
      expect(axiosMock.post).toHaveBeenCalledWith('/api/experiments/1/jobs/2/artifacts', {
        description: 'd',
        uri: 'u',
      })
    })

    it('getArtifactFiles hits /api/artifacts/<id>/files', async () => {
      axiosMock.get.mockResolvedValueOnce(ok())
      await api.getArtifactFiles('99')
      expect(axiosMock.get).toHaveBeenCalledWith('/api/artifacts/99/files')
    })

    it('downloadFile triggers an anchor click with the object URL and revokes it', async () => {
      const blob = { type: 'text/plain' } as Blob
      axiosMock.get.mockResolvedValueOnce({ data: blob })
      const createObjectURL = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:abc')
      const revokeObjectURL = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined)
      const anchor = document.createElement('a')
      const clickSpy = vi.spyOn(anchor, 'click').mockImplementation(() => undefined)
      const createElementSpy = vi.spyOn(document, 'createElement').mockReturnValue(anchor)
      await api.downloadFile('/x.bin', 'out.bin')
      expect(anchor.href).toContain('blob:abc')
      expect(anchor.download).toBe('out.bin')
      expect(clickSpy).toHaveBeenCalled()
      expect(revokeObjectURL).toHaveBeenCalledWith('blob:abc')
      createObjectURL.mockRestore()
      revokeObjectURL.mockRestore()
      clickSpy.mockRestore()
      createElementSpy.mockRestore()
    })
  })

  describe('entrypoint plugins + resource linking', () => {
    it('addPluginsToEntrypoint posts the plugin id list under the pluginType key', async () => {
      axiosMock.post.mockResolvedValueOnce(ok())
      await api.addPluginsToEntrypoint('7', [1, 2], 'plugins')
      expect(axiosMock.post).toHaveBeenCalledWith('/api/entrypoints/7/plugins', { plugins: [1, 2] })
    })

    it('removePluginFromEntrypoint deletes the nested resource', async () => {
      axiosMock.delete.mockResolvedValueOnce(ok())
      await api.removePluginFromEntrypoint('7', 2, 'plugins')
      expect(axiosMock.delete).toHaveBeenCalledWith('/api/entrypoints/7/plugins/2')
    })

    it('appendResource + removeResourceFromResource hit nested endpoints', async () => {
      axiosMock.post.mockResolvedValueOnce(ok())
      axiosMock.delete.mockResolvedValueOnce(ok())
      await api.appendResource('experiments', 1, 'entrypoints', [5, 6])
      await api.removeResourceFromResource('experiments', 1, 'entrypoints', 5)
      expect(axiosMock.post).toHaveBeenCalledWith('/api/experiments/1/entrypoints', { ids: [5, 6] })
      expect(axiosMock.delete).toHaveBeenCalledWith('/api/experiments/1/entrypoints/5')
    })
  })

  describe('models + workflows', () => {
    it('getVersions hits /api/models/<id>/versions', async () => {
      axiosMock.get.mockResolvedValueOnce(ok())
      await api.getVersions('9')
      expect(axiosMock.get).toHaveBeenCalledWith('/api/models/9/versions')
    })

    it('validateEntrypoint + suggestPluginTasks post to workflow endpoints', async () => {
      axiosMock.post.mockResolvedValueOnce(ok()).mockResolvedValueOnce(ok())
      await api.validateEntrypoint({ name: 'e' })
      await api.suggestPluginTasks('def f(): pass')
      expect(axiosMock.post.mock.calls[0][0]).toBe('/api/workflows/validateEntrypoint')
      expect(axiosMock.post.mock.calls[1][0]).toBe('/api/workflows/pluginTaskSignatureAnalysis')
      expect(axiosMock.post.mock.calls[1][1]).toEqual({ pythonCode: 'def f(): pass' })
    })

    it('importResources uses axios.postForm with paramsSerializer.indexes=null', async () => {
      axiosMock.postForm.mockResolvedValueOnce(ok())
      await api.importResources({
        group: 1,
        sourceType: 'upload',
        gitUrl: '',
        files: 'x',
        archiveFile: '',
        configPath: '',
        resolveNameConflictsStrategy: 'error',
      })
      expect(axiosMock.postForm).toHaveBeenCalled()
      expect(axiosMock.postForm.mock.calls[0][0]).toBe('/api/workflows/resourceImport')
      expect(axiosMock.postForm.mock.calls[0][2]).toEqual({ formSerializer: { indexes: null } })
    })

    it('getDioptraVersion returns res.data.version or "unknown"', async () => {
      axiosMock.get.mockResolvedValueOnce(ok({ version: '1.2.3' }))
      expect(await api.getDioptraVersion()).toBe('1.2.3')
      axiosMock.get.mockResolvedValueOnce(ok({}))
      expect(await api.getDioptraVersion()).toBe('unknown')
    })
  })

  describe('auth', () => {
    it('getLoginStatus + login + logout + registerUser use the users/auth endpoints', async () => {
      axiosMock.get.mockResolvedValueOnce(ok())
      axiosMock.post
        .mockResolvedValueOnce(ok())
        .mockResolvedValueOnce(ok())
        .mockResolvedValueOnce(ok())
      await api.getLoginStatus()
      await api.login('u', 'p')
      await api.logout(true)
      await api.registerUser('u', 'e', 'p', 'p')
      expect(axiosMock.get.mock.calls[0][0]).toBe('/api/users/current')
      expect(axiosMock.post.mock.calls[0]).toEqual([
        '/api/auth/login',
        { username: 'u', password: 'p' },
      ])
      expect(axiosMock.post.mock.calls[1][0]).toBe('/api/auth/logout?everywhere=true')
      expect(axiosMock.post.mock.calls[2][0]).toBe('/api/users')
    })

    it('logout defaults to everywhere=false', async () => {
      axiosMock.post.mockResolvedValueOnce(ok())
      await api.logout()
      expect(axiosMock.post.mock.calls[0][0]).toBe('/api/auth/logout?everywhere=false')
    })

    it('changePassword + deleteUser hit /api/users/current*', async () => {
      axiosMock.post.mockResolvedValueOnce(ok())
      axiosMock.delete.mockResolvedValueOnce(ok())
      await api.changePassword('old', 'new', 'new')
      await api.deleteUser('secret')
      expect(axiosMock.post.mock.calls[0][0]).toBe('/api/users/current/password')
      expect(axiosMock.delete.mock.calls[0]).toEqual([
        '/api/users/current',
        { data: { password: 'secret' } },
      ])
    })
  })
})
