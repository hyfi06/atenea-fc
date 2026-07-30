import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Landing } from './screens/Landing'
import { Login } from './screens/Login'
import { Home } from './screens/Home'
import { HealthCheck } from './screens/HealthCheck'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/home" element={<Home />} />
        <Route path="/health" element={<HealthCheck />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
