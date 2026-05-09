from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.authentication.serializers.personnel_serializer import PersonnelCreateSerializer, PersonnelSerializer
from apps.authentication.services.personnel_service import PersonnelService
from apps.authentication.permissions import IsAdminUser
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from apps.authentication.models import User


class PersonnelCreateView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        users = User.objects.exclude(id=request.user.id).exclude(role='admin').order_by('first_name')
        serializer = PersonnelSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PersonnelCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = PersonnelService.create_personnel(serializer.validated_data)
            return Response(
                {"message": "Personal registrado exitosamente"}, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserDetailView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        """Permite al Admin editar datos del personal"""
        
        user_to_edit = get_object_or_404(User, pk=pk)
        
        # Prepare data
        data = request.data.copy()
        inventories = data.pop('assigned_inventories', None)
        password = data.pop('password', None)
        
        if password:
            raw_password = password[0] if isinstance(password, list) else password
            from django.contrib.auth.password_validation import validate_password
            from django.core.exceptions import ValidationError as DjangoValidationError
            try:
                validate_password(raw_password)
            except DjangoValidationError as e:
                return Response({"password": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PersonnelCreateSerializer(user_to_edit, data=data, partial=True)
        
        if serializer.is_valid():
            user = serializer.save()
            
            if password:
                user.set_password(password[0] if isinstance(password, list) else password)
                user.save()
                
            if inventories is not None:
                # Si llega como string vacio, o lista iteramos
                if inventories == '' or inventories == []:
                    user.assigned_inventories.clear()
                else:
                    if isinstance(inventories, list):
                        user.assigned_inventories.set(inventories)
                    else:
                        user.assigned_inventories.set([inventories])

            return Response(PersonnelSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Permite al Admin eliminar un usuario de la fundación"""
        
        user_to_delete = get_object_or_404(User, pk=pk)
        user_to_delete.delete()
        return Response({"message": "Usuario eliminado correctamente."}, status=status.HTTP_204_NO_CONTENT)
