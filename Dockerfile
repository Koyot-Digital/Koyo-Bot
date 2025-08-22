# syntax=docker/dockerfile:1

FROM archlinux:latest

# Install Python, pip, git, unzip
RUN pacman -Sy --noconfirm python python-pip git unzip && \
    pacman -Scc --noconfirm

# Download and extract the repo archive
WORKDIR /app
ADD https://github.com/Koyot-Digital/Koyo-Bot/archive/refs/heads/main.zip /app/main.zip
RUN unzip main.zip && mv Koyo-Bot-main/* . && rm -rf Koyo-Bot-main main.zip

# Install Python dependencies if there's a requirements.txt
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Default command
CMD ["python", "bot.py"]
