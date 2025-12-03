#!/bin/bash

# Iniciar API en segundo plano
uvicorn api:app --host 0.0.0.0 --port 8000 &

# Esperar a que la API esté lista
sleep 5

# Iniciar Streamlit en primer plano
streamlit run app_streamlit.py --server.port=${PORT:-8501} --server.address=0.0.0.0
