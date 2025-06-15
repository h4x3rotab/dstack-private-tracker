# Use a lightweight official Python image as the base.
# Using python:3.9-slim-buster provides a smaller image size compared to full Python images.
FROM python:3.9-slim-buster

# Set the working directory inside the container
WORKDIR /app

# Copy the Python script into the container at /app
# The script is now named 'server.py'.
RUN pip install web3
COPY server.py .

# Expose port 80. This tells Docker that the container listens on this port.
# Note: When running the container, if you map this to a privileged port (like 80 on the host),
# you might need to run Docker with elevated privileges (e.g., `sudo docker run ...`).
# Alternatively, you can map it to a higher port on the host (e.g., `docker run -p 8080:80 ...`).
EXPOSE 8091

# Command to run the Python HTTP server.
# `CMD` defines the default command to execute when a container starts.
# `python` is the command, and `server.py` is the argument.
CMD ["python", "server.py"]

