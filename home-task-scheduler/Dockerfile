ARG BUILD_FROM
FROM $BUILD_FROM

# Install requirements for add-on
RUN \
  apk add --no-cache \
    python3 \
    py3-pip

WORKDIR /data

# Copy data for add-on
COPY /data/run.sh /
COPY data/ /data/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r /data/server/requirements.txt

RUN chmod a+x /run.sh

CMD [ "./run.sh" ]
