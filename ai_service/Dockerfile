FROM continuumio/miniconda3
WORKDIR /app

COPY environment.yaml .

RUN conda env create -f environment.yaml

COPY . .

CMD ["conda", "run", "--no-capture-output", "-n", "traffic-ai", "python", "mock_yolo.py"]