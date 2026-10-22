# Usamos una imagen base de Python oficial
# Elegimos 3.10-slim para mantenerla ligera, ajusta si necesitas otra versión específica
FROM python:3.10-slim-bookworm

# Variables de entorno para evitar archivos .pyc y buffers en stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements.txt primero para aprovechar caché de capas
COPY requirements.txt /app/

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del proyecto
COPY . /app/

# Crear directorios necesarios (como logs si se necesitan)
RUN mkdir -p logs

# Comando por defecto
# Nota: Como main.py parece ser un script CLI, el ENTRYPOINT permite pasarle argumentos
# Ejemplo: docker run sentinel-mvp --help
ENTRYPOINT ["python", "main.py"]
