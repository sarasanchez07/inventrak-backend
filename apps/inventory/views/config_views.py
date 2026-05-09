from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import BaseUnit, Presentation
from rest_framework import serializers

class BaseUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseUnit
        fields = '__all__'

class PresentationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Presentation
        fields = '__all__'

class BaseUnitListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        units = BaseUnit.objects.all()
        serializer = BaseUnitSerializer(units, many=True)
        return Response(serializer.data)

class PresentationListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        prefs = Presentation.objects.all()
        serializer = PresentationSerializer(prefs, many=True)
        return Response(serializer.data)
