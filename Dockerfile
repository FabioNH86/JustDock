FROM ubuntu:22.04

RUN sed -i 's|http://ports.ubuntu.com/ubuntu-ports|http://archive.ubuntu.com/ubuntu|g' /etc/apt/sources.list

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Actualizar repositorios con reintentos
# RUN apt-get update --fix-missing || apt-get update

# Instalar dependencias básicas primero
# RUN apt-get install -y --no-install-recommends \
RUN rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && for i in 1 2 3; do apt-get update --fix-missing && break || sleep 5; done \
    && for i in 1 2 3; do apt-get install -y --no-install-recommends \
        npm \
        python3 \
        python3-pip \
        python3-dev \
        pkg-config \
        libmysqlclient-dev \
        build-essential \
        gawk \
        sed \
        wget \
        && break || sleep 5; done \
    && rm -rf /var/lib/apt/lists/*

# Crear enlace simbólico para python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Instalar Vina
RUN wget -q https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.5/vina_1.2.5_linux_x86_64 -O /usr/local/bin/vina \
    && chmod +x /usr/local/bin/vina

# Add NodeSource Node.js 18.x repo and install
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Dependencias de Python
COPY jimag/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Aplicación
COPY jimag/ .
COPY jimag-scripts/ /app/jimag-scripts/

RUN chmod +x /app/jimag-scripts/*.sh \
    && chmod +x /app/jimag-scripts/*.py

RUN npm install && npm run build \
    && npm install typescript --save-dev

RUN mkdir -p /app/media /app/static \
    && python manage.py collectstatic --noinput

EXPOSE 8080

CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
