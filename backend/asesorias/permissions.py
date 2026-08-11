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
        user = request.user
        es_alumno_dueno = (
            hasattr(user, "perfil_alumno")
            and obj.alumno_id == user.perfil_alumno.id
        )
        es_asesor_dueno = (
            hasattr(user, "perfil_asesor_academico")
            and obj.disponibilidad.registro.asesor.user_id == user.id
        )
        return es_alumno_dueno or es_asesor_dueno


class EsMiembroSAE(BasePermission):
    message = "Se requiere un perfil de miembro de la SAE."

    def has_permission(self, request, view):
        return hasattr(request.user, "perfil_sae")


class EsAlumnoOMiembroSAE(BasePermission):
    message = "Se requiere un perfil de alumno o de miembro de la SAE."

    def has_permission(self, request, view):
        return hasattr(request.user, "perfil_alumno") or hasattr(request.user, "perfil_sae")