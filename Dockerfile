# Usamos Ubuntu 22.04
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Instalamos las dependencias actualizadas
RUN apt-get update && apt-get install -y \
    tzdata \
    python3 \
    python3-pip \
    python3-dev \
    libpython2.7 \
    python2.7 \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    openbabel \
    libgl1-mesa-glx \
    libglu1-mesa \
    libxrender1 \
    libxcursor1 \
    libftgl2 \
    libfontconfig1 \
    libdbus-1-3 \
    libxft2 \
    libxext6 \
    libsm6 \
    libice6 \
    libxss1 \
    openjdk-8-jre-headless \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /.local /root/.local && \
    ln -s /app /.local/src && \
    ln -s /app /root/.local/src

# --- PARCHE PARA ADFRSUITE ---
# 1. Copiamos el comprimido al contenedor
COPY ADFRsuite_x86_64Linux_1.0.tar.gz /tmp/
RUN cd /tmp && tar -xzf ADFRsuite_x86_64Linux_1.0.tar.gz && \
    cd ADFRsuite_x86_64Linux_1.0 && \
    ./install.sh -d /opt/ADFRsuite -l && \
    rm -rf /tmp/ADFRsuite*

RUN rm -f /opt/ADFRsuite/bin/obabel /opt/ADFRsuite/bin/obabelbin/obabel    
# Borramos la ZLIB vieja de ADFRsuite para que use la del sistema automáticamente

# --- ELIMINAR EL CONFLICTO DE RAÍZ ---
# Borramos la librería vieja de ADFR que rompe los comandos de Ubuntu
RUN rm -rf /opt/ADFRsuite/lib/libz.so*

# Si instalaste ADFR en otra ruta (como sugiere el log /root/.local/...), bórrala también ahí:
RUN rm -rf /root/.local/src/adfr/ADFRsuite-1.0/lib/libz.so*

# Enlazamos la librería moderna del sistema donde ADFR espera encontrar la suya
RUN ln -sf /lib/x86_64-linux-gnu/libz.so.1 /opt/ADFRsuite/lib/libz.so.1

RUN ln -sf /opt/ADFRsuite/bin/python2.7 /usr/bin/python2.7

# Crear un acceso directo para Vina
# 1. Copiar la carpeta de Vina desde tu host a la imagen
COPY vina_1.2.5 /app/vina_1.2.5

# 2. Dar permisos al binario REAL (no al link)
RUN chmod +x /app/vina_1.2.5/vina_1.2.5_linux_x86_64

# 3. Crear el link simbólico
RUN ln -s /app/vina_1.2.5/vina_1.2.5_linux_x86_64 /usr/bin/vina

# --- REPARACIONES DE COMPATIBILIDAD ---
# 1. Eliminar librería conflictiva de Chimera
RUN rm -f /app/chimera/lib/libfreetype.so*

# 2. Asegurar que las librerías de sistema tengan prioridad
ENV LD_PRELOAD="/usr/lib/x86_64-linux-gnu/libfreetype.so.6"

RUN mkdir -p /app/jimag/media && chmod -R 777 /app/jimag/media

WORKDIR /app

# --- PYTHON & DEPENDENCIES ---
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel
COPY jimag/requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt
COPY jimag-scripts/ /app/jimag-scripts/
RUN chmod +x /app/jimag-scripts/*.sh
COPY . .

# --- ENVIRONMENT ---
ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
ENV PATH="/app/chimera/bin:/app/p2rank_2.4:/app/jimag-scripts:${PATH}:/opt/ADFRsuite/bin"
#ENV LD_LIBRARY_PATH="/opt/ADFRsuite/lib:${LD_LIBRARY_PATH}"
ENV SCRIPTDIR=/app/jimag-scripts
ENV PYTHONPATH="/app:/app/jimag:${PYTHONPATH}"

