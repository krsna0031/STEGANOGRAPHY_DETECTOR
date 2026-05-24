from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    home,
    ImageAnalysisViewSet,
    TechniqueViewSet,
    HistoryViewSet
)

router = DefaultRouter()

router.register(r'analysis', ImageAnalysisViewSet, basename='analysis')
router.register(r'techniques', TechniqueViewSet, basename='techniques')
router.register(r'history', HistoryViewSet, basename='history')

urlpatterns = [
    path('', home, name='home'),
    path('api/', include(router.urls)),
]