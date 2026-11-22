FROM python:3.12-slim
WORKDIR /app
COPY build/gen_log.py /tmp/gen_log.py
# Generate the output at build time and delete the generator, so the answer is only in the output.
RUN mkdir -p /var/lib/app-data && python3 /tmp/gen_log.py > /var/lib/app-data/output.txt && rm /tmp/gen_log.py
COPY build/build.sh /app/build.sh
RUN chmod +x /app/build.sh
CMD ["/bin/bash"]
