# Usamos una imagen ligera de Python (Actualizado a 3.11 por compatibilidad con networkx)
FROM python:3.11-slim

# Evitamos archivos .pyc y buffers en logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# 1. Copiamos solo los requerimientos primero (para aprovechar caché de Docker)
COPY requirements.txt .

# 2. Instalamos dependencias del sistema necesarias para compilar paquetes nativos
# wordcloud requiere gcc para compilar extensiones C
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove \
    gcc \
    g++ \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. Copiamos todo el código del proyecto
COPY . .

# Exponemos el puerto de Streamlit
EXPOSE 8501

# Comando de ejecución
CMD ["streamlit", "run", "src/05_analytics_viz/14_webapp_pro.py", "--server.address=0.0.0.0"]
