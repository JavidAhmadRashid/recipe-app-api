"""
Views for the recipe app.
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from core.models import Recipe
from recipe import serializers

class RecipeViewSet(viewsets.ModelViewSet):
    """Views for managing Recipe API."""
    queryset = Recipe.objects.all()
    serializer_class = serializers.RecipeDetailSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Retrieve the recipes for the authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-id')
    
    def get_serializer_class(self):
        """Return the appropriate serializer class based on the action."""
        if self.action == 'list':
            return serializers.RecipeSerializer
        
        return self.serializer_class
    
    def perform_create(self, serializer):
        """Create a new recipe."""
        serializer.save(user=self.request.user)