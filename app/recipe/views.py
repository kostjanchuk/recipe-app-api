"""
Views for the recipe API
"""

from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe, Tag, Ingredient
from .serializers import (RecipeSerializer, RecipeDetailSerializer,
                          TagSerializer, IngredientSerializer)


class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage recipe APIs"""
    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve recipes for authenticated user """
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request"""
        if self.action == 'list':
            return RecipeSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe"""
        serializer.save(user=self.request.user)


class RecipeAttrBaseViewSet(mixins.CreateModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset yo authenticated user"""
        return self.queryset.filter(user=self.request.user).order_by('-name')


class TagViewSet(RecipeAttrBaseViewSet):
    """Manage tags in the database"""

    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(RecipeAttrBaseViewSet):
    """Manage ingredients in database"""

    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
