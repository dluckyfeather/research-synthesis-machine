# Use the official Python image
FROM python:3.11

# Set the working directory
WORKDIR /app

# Copy your files into the container
COPY . .

# Install the tools we listed in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Streamlit uses
EXPOSE 7860

# Start the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
