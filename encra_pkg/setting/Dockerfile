FROM python:3.9-slim

# 시스템 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libgmp-dev \
    libssl-dev \
    libmpfr-dev \
    python3-dev \
    git \
    wget \
    m4 \
    flex \
    bison \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# PBC 라이브러리 설치
RUN wget https://crypto.stanford.edu/pbc/files/pbc-0.5.14.tar.gz && \
    tar -xzf pbc-0.5.14.tar.gz && \
    cd pbc-0.5.14 && ./configure && make && make install && \
    cd .. && rm -rf pbc-0.5.14* && ldconfig

# Charm-Crypto 설치
RUN git clone https://github.com/JHUISI/charm.git && \
    cd charm && ./configure.sh && make && python3 setup.py install && \
    cd .. && rm -rf charm

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY . .

EXPOSE 6543

CMD ["python", "app.py"]
