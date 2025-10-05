# app/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Max
from .models import Location, DailyForecast
from .serializers import DailyForecastSerializer
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

    
# ----------------------------------------------------------------------
# 3. Vista de Búsqueda por Coordenadas (Endpoint Principal)
# ----------------------------------------------------------------------

class CurrentWeatherView(APIView):
    """
    Endpoint para obtener el pronóstico climático actual (más reciente)
    dada la latitud y longitud.
    
    Ruta: /api/v1/current-weather/?lat=<latitud>&lon=<longitud>
    """
    def get(self, request, *args, **kwargs):
        # 1. Obtener parámetros de la URL
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lon')

        # 2. Validar parámetros
        if not latitude or not longitude:
            return Response(
                {"error": "Se requieren los parámetros 'lat' (latitud) y 'lon' (longitud)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lat = float(latitude)
            lon = float(longitude)
        except ValueError:
            return Response(
                {"error": "Los parámetros lat y lon deben ser valores numéricos."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 3. Buscar la ubicación
        # Usaremos una tolerancia (ej: 0.01) ya que las coordenadas pueden variar ligeramente
        # En un sistema real, usarías un campo de búsqueda geoespacial (PostGIS)
        tolerance = 0.01
        
        try:
            location = Location.objects.get(
                latitude__gte=lat - tolerance,
                latitude__lte=lat + tolerance,
                longitude__gte=lon - tolerance,
                longitude__lte=lon + tolerance
            )
        except Location.DoesNotExist:
            return Response(
                {"error": "Ubicación no encontrada en la base de datos para esas coordenadas."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Location.MultipleObjectsReturned:
            # Manejar el caso si varias ubicaciones están muy cerca, solo tomamos la primera
            location = Location.objects.filter(
                latitude__gte=lat - tolerance,
                latitude__lte=lat + tolerance,
                longitude__gte=lon - tolerance,
                longitude__lte=lon + tolerance
            ).first()

        # 4. Obtener el pronóstico más reciente (o de hoy) para esa ubicación
        try:
            # Buscamos el pronóstico del día de hoy o el más reciente si no hay uno de hoy
            forecast = DailyForecast.objects.filter(location=location).order_by('-date').first()
            
            if not forecast:
                 return Response(
                    {"error": f"No se encontró pronóstico para {location.city}."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 5. Serializar y devolver la respuesta
            serializer = DailyForecastSerializer(forecast)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Error interno del servidor: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )