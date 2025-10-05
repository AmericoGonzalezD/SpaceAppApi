# app/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
# Importaciones necesarias para la búsqueda por distancia
from django.db.models import F, FloatField, ExpressionWrapper
from django.db.models.functions import Cast
from decimal import Decimal

# Importa todos los modelos y serializers necesarios
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
# 1. ViewSets de Datos Climáticos (CRUD para Administración/Carga)
# ----------------------------------------------------------------------

class LocationViewSet(viewsets.ModelViewSet):
    """Permite listar y crear ubicaciones (ciudades)."""
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [AllowAny] 
    

class DailyForecastViewSet(viewsets.ModelViewSet):
    """Permite listar y obtener pronósticos diarios (Home Screen)."""
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
# 2. ViewSet de Favoritos
# ----------------------------------------------------------------------

class FavoriteLocationViewSet(viewsets.ModelViewSet):
    """Permite a los usuarios gestionar sus ubicaciones favoritas."""
    queryset = FavoriteLocation.objects.all() 
    serializer_class = FavoriteLocationSerializer
    permission_classes = [AllowAny] 

    def get_queryset(self):
        """Filtra el queryset para mostrar solo los favoritos del usuario actual."""
        if self.request.user.is_authenticated:
            return FavoriteLocation.objects.filter(user=self.request.user)
        return FavoriteLocation.objects.all() 

    def perform_create(self, serializer):
        """Asigna el usuario que realiza la petición al crear el favorito."""
        if self.request.user.is_authenticated:
             serializer.save(user=self.request.user)
        else:
             serializer.save()

    
# ----------------------------------------------------------------------
# 3. Vista de Búsqueda por Coordenadas (Endpoint: /clima-actual/)
# ----------------------------------------------------------------------

class CurrentWeatherView(APIView):
    """
    Endpoint para obtener el pronóstico más reciente, encontrando la 
    Location más cercana por distancia euclidiana.
    """
    def get(self, request, *args, **kwargs):
        latitude_str = request.query_params.get('lat')
        longitude_str = request.query_params.get('lon')

        # 1. Validar y convertir parámetros
        if not latitude_str or not longitude_str:
            return Response(
                {"error": "Se requieren los parámetros 'lat' y 'lon'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Convertimos a float para usar en el cálculo SQL
            lat_f = float(latitude_str) 
            lon_f = float(longitude_str)
        except Exception:
            return Response(
                {"error": "Los parámetros lat y lon deben ser valores numéricos válidos."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 2. BÚSQUEDA POR DISTANCIA (FIXED)
        distance_expression = ExpressionWrapper(
            (Cast(F('latitude'), FloatField()) - lat_f) ** 2 + 
            (Cast(F('longitude'), FloatField()) - lon_f) ** 2,
            output_field=FloatField() 
        )
        
        locations_with_distance = Location.objects.annotate(
            distance=distance_expression
        )
        
        closest_location = locations_with_distance.order_by('distance').first()

        if not closest_location:
            return Response(
                {"error": "No hay ubicaciones registradas en la base de datos para realizar la búsqueda."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. Obtener el pronóstico más reciente
        try:
            forecast = DailyForecast.objects.filter(location=closest_location).order_by('-date').first()
            
            if not forecast:
                 return Response(
                    {"error": f"Ubicación más cercana encontrada: {closest_location.city}, pero no hay pronóstico registrado."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 4. Serializar y devolver
            serializer = DailyForecastSerializer(forecast)
            response_data = serializer.data
            response_data['metadata'] = {
                'found_city': closest_location.city,
                'found_latitude': closest_location.latitude,
                'found_longitude': closest_location.longitude
            }
            
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error interno al obtener pronóstico: {e}") 
            return Response(
                {"error": "Error interno al procesar el pronóstico. Verifique el log del servidor."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ----------------------------------------------------------------------
# 4. Vista de Búsqueda por Ciudad (Endpoint: /clima-por-ciudad/)
# ----------------------------------------------------------------------

class CityWeatherView(APIView):
    """
    Endpoint para obtener el pronóstico climático actual dado el nombre de la ciudad.
    """
    def get(self, request, *args, **kwargs):
        city_name = request.query_params.get('city')

        # 1. Validar parámetro
        if not city_name:
            return Response(
                {"error": "Se requiere el parámetro 'city' (nombre de la ciudad)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Buscar la ubicación por nombre (búsqueda insensible a mayúsculas y minúsculas)
        try:
            # Usamos icontains (case-insensitive contains) para búsquedas flexibles
            location = Location.objects.filter(city__icontains=city_name).first()
            
            if not location:
                return Response(
                    {"error": f"Ciudad no encontrada: No se encontró '{city_name}' en la base de datos."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        except Exception as e:
             return Response(
                {"error": f"Error interno en la búsqueda de ubicación: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


        # 3. Obtener el pronóstico más reciente
        try:
            forecast = DailyForecast.objects.filter(location=location).order_by('-date').first()
            
            if not forecast:
                 return Response(
                    {"error": f"Ubicación encontrada: {location.city}, pero no hay pronóstico registrado."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 4. Serializar y devolver la respuesta
            serializer = DailyForecastSerializer(forecast)
            
            response_data = serializer.data
            response_data['metadata'] = {
                'found_city': location.city,
                'found_latitude': location.latitude,
                'found_longitude': location.longitude
            }
            
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Error interno al procesar el pronóstico. Verifique el log del servidor."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )