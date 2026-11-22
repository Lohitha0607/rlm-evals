FROM python:3.12-slim
WORKDIR /app
COPY build/gen_access_log.py /tmp/gen_access_log.py
# Generate the output at build time and delete the generator, so the answer is only in the output.
RUN mkdir -p /var/lib/app-data && python3 /tmp/gen_access_log.py > /var/lib/app-data/output.txt && rm /tmp/gen_access_log.py
COPY build/access_log.sh /app/access_log.sh
RUN chmod +x /app/access_log.sh
CMD ["/bin/bash"]
