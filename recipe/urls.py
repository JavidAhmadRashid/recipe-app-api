"""
Url patterns for the recipe app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from recipe import views

# Create a router and register the RecipeViewSet with it
router = DefaultRouter()
router.register('recipes', views.RecipeViewSet)
router.register('tags', views.TagViewset)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
    # Additional paths can be added here if needed
]
        # Ensure that only recipes belonging to the authenticated user are returned
        # and order them by the most recent first.  