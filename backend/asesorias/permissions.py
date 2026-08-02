from rest_framework.permissions import BasePermission


class EsAlumno(BasePermission):
    message = "Se requiere un perfil de alumno."

    def has_permission(self, request, view):
        return hasattr(request.user, "perfil_alumno")


class EsAsesorAcademico(BasePermission):
    message = "Se requiere un perfil de asesor académico."

    def has_permission(self, request, view):
        return hasattr(request.user, "perfil_asesor_academico")


class EsAlumnoOAsesorAcademico(BasePermission):
    message = "Se requiere un perfil de alumno o de asesor académico."

    def has_permission(self, request, view):
        return hasattr(request.user, "perfil_alumno") or hasattr(request.user, "perfil_asesor_academico")


class EsDuenoDelRegistro(BasePermission):
    message = "No puedes operar sobre el registro de otro asesor."

    def has_object_permission(self, request, view, obj):
        registro = obj if hasattr(obj, "asesor") else obj.registro
        return registro.asesor.user_id == request.user.id


class EsDuenoDeLaAsesoria(BasePermission):
    message = "No puedes operar sobre una sesión ajena."

    def has_object_permission(self, request, view, obj):
        if hasattr(request.user, "perfil_alumno"):
            return obj.alumno_id == request.user.perfil_alumno.id
        if hasattr(request.user, "perfil_asesor_academico"):
            return obj.disponibilidad.registro.asesor.user_id == request.user.id
        return False