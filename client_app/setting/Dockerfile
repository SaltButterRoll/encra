FROM python:3.9

WORKDIR /app

RUN apt-get update && \
    apt-get install -y build-essential libgmp-dev libssl-dev libmpfr-dev python3-dev \
    git wget m4 flex bison libgl1-mesa-glx

RUN wget https://crypto.stanford.edu/pbc/files/pbc-0.5.14.tar.gz && \
    tar -xvzf pbc-0.5.14.tar.gz && \
    cd pbc-0.5.14 && ./configure && make && make install && cd .. && \
    ldconfig

RUN git clone https://github.com/JHUISI/charm.git && \
    cd charm && ./configure.sh && make && python3 setup.py install && \
    cd .. && rm -rf charm

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
