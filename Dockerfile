FROM python:3.10-slim
RUN useradd -m -u 1000 user
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=user . .
USER user
ENV HOME=/home/user
RUN python -m data.seed_orders && python -m app.rag.ingest
EXPOSE 7860
CMD ["streamlit", "run", "ui/app.py", "--server.port=7860", "--server.address=0.0.0.0", "--server.enableXsrfProtection=false", "--server.enableCORS=false"]