from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """
    Manager para el modelo User.
    Define cómo se crean usuarios y superusuarios.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El usuario debe tener un correo electrónico")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("El superusuario debe tener is_staff=True")

        if not extra_fields.get("is_superuser"):
            raise ValueError("El superusuario debe tener is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuario personalizado.
    Se usa el email como identificador principal.
    """

    email = models.EmailField(
        unique=True,
        verbose_name="Correo electrónico"
    )
    first_name = models.CharField(
        max_length=100,
        blank=True
    )
    last_name = models.CharField(
        max_length=100,
        blank=True
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_system = models.BooleanField(
        default=False, 
        help_text="Designa si este es un usuario interno del sistema, usado para procesos automáticos."
    )

    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        MAESTRO = 'maestro', 'Maestro'
        JEFE = 'jefe', 'Jefe'
        ESTUDIANTE = 'estudiante', 'Estudiante'

    role = models.CharField(
        max_length=15, 
        choices=Role.choices, 
        default=Role.ESTUDIANTE
    )
    
    # Relación ManyToMany con la app de inventory
    # (Asegúrate de que la app 'inventory' y el modelo 'Inventory' existan)
    assigned_inventories = models.ManyToManyField('inventory.Inventory', blank=True, related_name='staff')

    class Meta:
        app_label = 'authentication'
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["email"]

    def __str__(self):
        return self.email
