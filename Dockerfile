FROM deepset/haystack:base-main

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install packages specified in requirements.txt
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Run app.py when the container launches
ENTRYPOINT ["python", "auto_pr_writer.py"]
