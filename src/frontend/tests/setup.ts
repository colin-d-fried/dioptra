import { config } from '@vue/test-utils'
import { Quasar } from 'quasar'

config.global.plugins = [[Quasar, {}]]

if (typeof window !== 'undefined') {
  // happy-dom does not implement URL.createObjectURL; several Vue files use it.
  if (!window.URL.createObjectURL) {
    window.URL.createObjectURL = () => 'blob:mock'
  }
  if (!window.URL.revokeObjectURL) {
    window.URL.revokeObjectURL = () => undefined
  }
}
