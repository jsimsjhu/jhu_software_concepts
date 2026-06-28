FROM python:3.11-slim

# Install Chrome and dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Add the Google Chrome repository using the modern method
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-archive-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-archive-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list

# Install Chrome
RUN apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create selenium cache directory with proper permissions for non-root user
# This must be done BEFORE switching to USER 1000
RUN mkdir -p /home/worker/.cache/selenium && chown -R 1000:1000 /home/worker/.cache
ENV HOME=/home/worker
ENV PATH="/home/worker/.local/bin:$PATH"

# Switch to non-root user AFTER all files and directories are set up
USER 1000

CMD ["python", "-u", "consumer.py"]