# Step 1: Set the base image
FROM python:3.9-slim

# Step 2: Set the working directory
WORKDIR /app

# Step 3: Install dependencies
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

# Step 4: Copy the entire project to the container
COPY . /app/

# Step 5: Set environment variables
ENV DJANGO_SETTINGS_MODULE=be_lernen.settings

# Step 6: Expose port for Django app
EXPOSE 8000

# Step 7: Run the application
CMD ["gunicorn", "be_lernen.wsgi:application", "--bind", "0.0.0.0:8000"]
