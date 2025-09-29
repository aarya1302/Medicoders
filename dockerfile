# Use lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements_live.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && \
    apt-get install -y --no-install-recommends procps && \
    rm -rf /var/lib/apt/lists/*

# Expose the ports your services use
EXPOSE 8501 8000 8765

# Run your script
# CMD ["python", "start_simulation.py"]
CMD ["streamlit", "run", "live_dashboard.py"]
# FROM python:3.11-slim

# WORKDIR /app

# COPY . /app/

# RUN pip install --no-cache-dir -r requirements.txt
# RUN pip install --no-cache-dir -r requirements_live.txt

# EXPOSE 8501

# CMD ["streamlit", "run", "live_dashboard.py"]
