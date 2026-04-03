import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { HomePage } from '@/pages/home'
import { ResearchPage } from '@/pages/research'

const queryClient = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/research/:runId" element={<ResearchPage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
