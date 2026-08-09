import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Landing } from './screens/Landing'
import { Login } from './screens/Login'
import { Home } from './screens/Home'
import { HealthCheck } from './screens/HealthCheck'
import { RutaDeAsesor } from './auth/RutaProtegida'
import { Asesorias } from './features/asesorias/screens/Asesorias'
import { DetalleAsesoria } from './features/asesorias/screens/DetalleAsesoria'
import { MisMaterias } from './features/asesorias/screens/MisMaterias'
import { MiHorario } from './features/asesorias/screens/MiHorario'

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
              <Asesorias />
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
          path="/asesorias/horario"
          element={
            <RutaDeAsesor>
              <MiHorario />
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
