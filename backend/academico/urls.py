from django.urls import path

from .views import PeriodoVigenteView

urlpatterns = [
    path("periodo-vigente/", PeriodoVigenteView.as_view(), name="periodo-vigente"),
]
