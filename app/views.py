# app/views.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import (
    Location, 
    DailyForecast, 
    HourlyForecast, 
    WeatherAlert, 
    FavoriteLocation
)
from .serializers import (
    LocationSerializer, 
    DailyForecastSerializer, 
    HourlyForecastSerializer, 
    WeatherAlertSerializer, 
    FavoriteLocationSerializer
)

# ----------------------------------------------------------------------
# 1. ViewSets de Datos Climáticos (Solo Lectura/Administración)
# ----------------------------------------------------------------------

class LocationViewSet(viewsets.ModelViewSet):
    """Permite listar y crear ubicaciones (ciudades)."""
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    # Permitimos acceso sin autenticación para listar/buscar ubicaciones
    permission_classes = [AllowAny] 
    

class DailyForecastViewSet(viewsets.ModelViewSet):
    """Permite listar y obtener pronósticos diarios (Home Screen)."""
    # Ordenamos por fecha descendente para obtener el pronóstico más reciente
    queryset = DailyForecast.objects.all().order_by('-date', '-id')
    serializer_class = DailyForecastSerializer
    permission_classes = [AllowAny]
    
    
class HourlyForecastViewSet(viewsets.ModelViewSet):
    """Permite listar pronósticos por hora."""
    queryset = HourlyForecast.objects.all().order_by('time')
    serializer_class = HourlyForecastSerializer
    permission_classes = [AllowAny]
    
    
class WeatherAlertViewSet(viewsets.ModelViewSet):
    """Permite listar alertas climáticas."""
    queryset = WeatherAlert.objects.all().order_by('-date')
    serializer_class = WeatherAlertSerializer
    permission_classes = [AllowAny]


# ----------------------------------------------------------------------
# 2. ViewSet de Favoritos (Requiere Autenticación y Asignación de Usuario)
# ----------------------------------------------------------------------

class FavoriteLocationViewSet(viewsets.ModelViewSet):
    """Permite a los usuarios gestionar sus ubicaciones favoritas."""
    queryset = FavoriteLocation.objects.all() 
    serializer_class = FavoriteLocationSerializer
    
    # NOTA: Debes descomentar esta línea e instalar/configurar JWT 
    # cuando implementes la autenticación
    # permission_classes = [IsAuthenticated] 
    permission_classes = [AllowAny] # Temporalmente, permitimos acceso


    def get_queryset(self):
        """Filtra el queryset para mostrar solo los favoritos del usuario actual."""
        # Si usas autenticación, el usuario estará disponible en self.request.user
        # Para pruebas sin autenticación, devolveremos todos
        if self.request.user.is_authenticated:
            return FavoriteLocation.objects.filter(user=self.request.user)
        return FavoriteLocation.objects.all() # Solo para pruebas

    def perform_create(self, serializer):
        """Asigna el usuario que realiza la petición al crear el favorito."""
        # Esta línea es crucial para que el favorito se asigne al usuario logueado.
        # Si usas IsAuthenticated, self.request.user será el usuario.
        if self.request.user.is_authenticated:
             serializer.save(user=self.request.user)
        else:
             # Necesitas manejar este caso si permites AllowAny para la creación
             # o implementar un usuario de prueba si es necesario.
             serializer.save()