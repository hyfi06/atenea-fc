import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Landing } from './screens/Landing'
import { Login } from './screens/Login'
import { Home } from './screens/Home'
import { HealthCheck } from './screens/HealthCheck'
import { RutaDeAsesor } from './auth/RutaProtegida'
import { SesionesAsesor } from './features/asesorias/screens/SesionesAsesor'
import { DetalleAsesoria } from './features/asesorias/screens/DetalleAsesoria'
import { DisponibilidadAsesor } from './features/asesorias/screens/DisponibilidadAsesor'
import { MisMaterias } from './features/asesorias/screens/MisMaterias'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/home" element={<Home />} />
        <Route path="/health" element={<HealthCheck />} />
        <Route
          path="/asesorias"
          element={
            <RutaDeAsesor>
              <SesionesAsesor />
            </RutaDeAsesor>
          }
        />
        <Route
          path="/asesorias/disponibilidad"
          element={
            <RutaDeAsesor>
              <DisponibilidadAsesor />
            </RutaDeAsesor>
          }
        />
        <Route
          path="/asesorias/materias"
          element={
            <RutaDeAsesor>
              <MisMaterias />
            </RutaDeAsesor>
          }
        />
        <Route
          path="/asesorias/:id"
          element={
            <RutaDeAsesor>
              <DetalleAsesoria />
            </RutaDeAsesor>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
