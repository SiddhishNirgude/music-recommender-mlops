# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY ./requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire project directory into the container
COPY . /app

# Expose the port FastAPI will run on
EXPOSE 8000

# Run the Uvicorn server
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
