import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { App } from '@/app/app'
import '@/styles/theme.css'

const container = document.getElementById('root')
if (!container) {
  throw new Error('O elemento #root não existe em index.html')
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
