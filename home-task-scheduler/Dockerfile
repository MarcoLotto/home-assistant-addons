ARG BUILD_FROM
FROM $BUILD_FROM

# Install requirements for add-on
RUN \
  apk add --no-cache \
    python3 \
    py3-pip

# Copy root filesystem
COPY rootfs /

# Install pip dependencies
RUN pip3 install --no-cache-dir -r /usr/bin/server/requirements.txt
RUN chmod +x /etc/services.d/home-task-scheduler/run
RUN chmod +x /etc/services.d/home-task-scheduler/finish
RUN chmod +x /usr/bin/run.sh

EXPOSE 8000