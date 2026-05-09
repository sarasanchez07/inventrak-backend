# Imagen base
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear carpeta de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copiar el proyecto
COPY . .

# Exponer puerto
EXPOSE 8000

# Crear usuario sin privilegios y asignarle permisos de la app
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN chown -R appuser:appgroup /app

# Cambiar a usuario no root
USER appuser

# Comando para correr el servidor
CMD ["sh", "-c", "gunicorn inventrack.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]