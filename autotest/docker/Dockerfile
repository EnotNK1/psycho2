FROM python:3.12

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-m", "pytest", "autotest/docker/smoke", "-c", "autotest/pytest.ini", "-q"]
