FROM python:3.12-alpine
WORKDIR /app
COPY ./.venv/emi_calc.py .
COPY ./requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
ENV GRADIO_SERVER_NAME="0.0.0.0"
EXPOSE 7860
CMD ["python", "emi_calc.py"]