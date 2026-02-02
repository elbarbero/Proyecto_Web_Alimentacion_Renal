# Usar una imagen base ligera de Python
FROM python:3.11-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar requirements y instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar los archivos del proyecto al contenedor
COPY . /app

# Exponer el puerto 8000 que usa la aplicación
EXPOSE 8000

# Comando para iniciar la aplicación
CMD ["python", "server.py"]
