FROM continuumio/miniconda3
WORKDIR /app
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY environment.yaml .

RUN conda env create -f environment.yaml

COPY . .

CMD ["conda", "run", "--no-capture-output", "-n", "traffic-backend", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]