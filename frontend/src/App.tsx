import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Landing } from './screens/Landing'
import { Login } from './screens/Login'
import { ForgotPassword } from './screens/ForgotPassword'
import { ResetPassword } from './screens/ResetPassword'
import { Home } from './screens/Home'
import { HealthCheck } from './screens/HealthCheck'
import { NoEncontrado } from './screens/NoEncontrado'
import { RutaConSesion, RutaDeAsesor, RutaDeAsesorias, RutaDeSAE, RutaDeAcademico } from './auth/RutaProtegida'
import { Asesorias } from './features/asesorias/screens/Asesorias'
import { OfertaAsesorias } from './features/asesorias/screens/OfertaAsesorias'
import { AgendarAsesoria } from './features/asesorias/screens/AgendarAsesoria'
import { DetalleAsesoria } from './features/asesorias/screens/DetalleAsesoria'
import { MisMaterias } from './features/asesorias/screens/MisMaterias'
import { MiHorario } from './features/asesorias/screens/MiHorario'
import { SolicitudAsesor } from './features/asesorias/screens/SolicitudAsesor'
import { AdminAsesorias } from './features/asesorias/screens/AdminAsesorias'
import { AdminOfertaMateria } from './features/asesorias/screens/AdminOfertaMateria'
import { AdminAsesores } from './features/asesorias/screens/AdminAsesores'
import { AdminAsesorDetalle } from './features/asesorias/screens/AdminAsesorDetalle'
import { AdminDetalleAsesoria } from './features/asesorias/screens/AdminDetalleAsesoria'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password/:uid/:token" element={<ResetPassword />} />
        <Route
          path="/home"
          element={
            <RutaConSesion>
              <Home />
            </RutaConSesion>
          }
        />
        <Route path="/health" element={<HealthCheck />} />
        <Route
          path="/asesorias"
          element={
            <RutaDeAsesorias>
              <Asesorias />
            </RutaDeAsesorias>
          }
        />
        <Route
          path="/asesorias/nueva"
          element={
            <RutaDeAsesorias>
              <OfertaAsesorias />
            </RutaDeAsesorias>
          }
        />
        <Route
          path="/asesorias/nueva/:materiaId"
          element={
            <RutaDeAsesorias>
              <AgendarAsesoria />
            </RutaDeAsesorias>
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
          path="/asesorias/soy-asesor"
          element={
            <RutaDeAcademico>
              <SolicitudAsesor />
            </RutaDeAcademico>
          }
        />
        <Route
          path="/asesorias/:id"
          element={
            <RutaDeAsesorias>
              <DetalleAsesoria />
            </RutaDeAsesorias>
          }
        />
        <Route
          path="/sae/asesorias"
          element={
            <RutaDeSAE>
              <AdminAsesorias />
            </RutaDeSAE>
          }
        />
        <Route
          path="/sae/asesorias/oferta"
          element={
            <RutaDeSAE>
              <OfertaAsesorias
                titulo="Consulta de oferta"
                rutaVolver="/sae/asesorias"
                etiquetaVolver="← Volver a Asesorías SAE"
                baseRutaMateria="/sae/asesorias/oferta"
              />
            </RutaDeSAE>
          }
        />
        <Route
          path="/sae/asesorias/oferta/:materiaId"
          element={
            <RutaDeSAE>
              <AdminOfertaMateria />
            </RutaDeSAE>
          }
        />
        <Route
          path="/sae/asesorias/:id"
          element={
            <RutaDeSAE>
              <AdminDetalleAsesoria />
            </RutaDeSAE>
          }
        />
        <Route
          path="/sae/asesores"
          element={
            <RutaDeSAE>
              <AdminAsesores />
            </RutaDeSAE>
          }
        />
        <Route
          path="/sae/asesores/:asesorId"
          element={
            <RutaDeSAE>
              <AdminAsesorDetalle />
            </RutaDeSAE>
          }
        />
        <Route path="*" element={<NoEncontrado />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
