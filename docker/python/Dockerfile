# Base image s Pythonem
FROM python:3.12

# Nastavení pracovního adresáře
WORKDIR /app/data_analysis

# Kopírování requirements.txt a instalace závislostí
COPY ./requirements.txt ./
RUN python3 -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

ENV PATH="/venv/bin:$PATH"

# Kopírování zbytku aplikace
COPY . .

# Nastavení PYTHONPATH pouze pro `data_analysis`
ENV PYTHONPATH=/app/data_analysis

CMD ["python3", "main.py"]