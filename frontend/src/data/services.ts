import type { ComponentType } from 'react'
import {
  IconOrientacionVocacional,
  IconTutorias,
  IconBecas,
  IconIdiomas,
  IconServicioSocial,
  IconBolsaDeTrabajo,
  IconMovilidad,
  IconVoluntariado,
  IconPracticasProfesionales,
  type IconProps,
} from '../components/icons/ServiceIcons'

export interface Service {
  id: string
  label: string
  Icon: ComponentType<IconProps>
  containerClassName: string
  onContainerClassName: string
}

/**
 * Mock temporal: se muestran todos los servicios a cualquier usuario.
 * Cuando el backend exponga qué servicios ve cada perfil (ADR 0012), esta
 * lista se reemplaza por una llamada a la API, no por un campo de roles
 * agregado aquí.
 */
export const services: Service[] = [
  {
    id: 'orientacion-vocacional',
    label: 'Orientación Vocacional',
    Icon: IconOrientacionVocacional,
    containerClassName: 'bg-primary-container',
    onContainerClassName: 'text-on-primary-container',
  },
  {
    id: 'tutorias',
    label: 'Tutorías · PIT',
    Icon: IconTutorias,
    containerClassName: 'bg-tertiary-container',
    onContainerClassName: 'text-on-tertiary-container',
  },
  {
    id: 'becas',
    label: 'Becas',
    Icon: IconBecas,
    containerClassName: 'bg-secondary-container',
    onContainerClassName: 'text-on-secondary-container',
  },
  {
    id: 'idiomas',
    label: 'Idiomas',
    Icon: IconIdiomas,
    containerClassName: 'bg-primary-container',
    onContainerClassName: 'text-on-primary-container',
  },
  {
    id: 'servicio-social',
    label: 'Servicio Social',
    Icon: IconServicioSocial,
    containerClassName: 'bg-tertiary-container',
    onContainerClassName: 'text-on-tertiary-container',
  },
  {
    id: 'bolsa-de-trabajo',
    label: 'Bolsa de Trabajo',
    Icon: IconBolsaDeTrabajo,
    containerClassName: 'bg-secondary-container',
    onContainerClassName: 'text-on-secondary-container',
  },
  {
    id: 'movilidad',
    label: 'Movilidad',
    Icon: IconMovilidad,
    containerClassName: 'bg-primary-container',
    onContainerClassName: 'text-on-primary-container',
  },
  {
    id: 'voluntariado',
    label: 'Voluntariado',
    Icon: IconVoluntariado,
    containerClassName: 'bg-tertiary-container',
    onContainerClassName: 'text-on-tertiary-container',
  },
  {
    id: 'practicas-profesionales',
    label: 'Prácticas',
    Icon: IconPracticasProfesionales,
    containerClassName: 'bg-secondary-container',
    onContainerClassName: 'text-on-secondary-container',
  },
]
