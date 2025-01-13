# Base image s Pythonem
FROM python:3.12

# Vytvoření pracovního adresáře
WORKDIR /app

# Kopírování aplikace
COPY . /app

# Vytvoření virtuálního prostředí pro Python
RUN python3 -m venv /venv

# Aktivace virtuálního prostředí
ENV PATH="/venv/bin:$PATH"

RUN ls -la ./requirements.txt

COPY ./requirements.txt /app/requirements.txt

RUN ls /app/requirements.txt

# Instalace Python knihoven ve virtuálním prostředí
RUN pip install --no-cache-dir -r /app/requirements.txt

ENV PYTHONPATH=/app

# Expozice portu 8000
EXPOSE 8000

# Spuštění aplikace
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]


# Vytvoření virtuálního prostředí pro Python
RUN python3 -m venv /venv
