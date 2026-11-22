FROM python:3.12-slim
WORKDIR /app
COPY build/gen_deploy.py /tmp/gen_deploy.py
# Generate the output at build time and delete the generator, so the answer is only in the output.
RUN mkdir -p /var/lib/app-data && python3 /tmp/gen_deploy.py > /var/lib/app-data/output.txt && rm /tmp/gen_deploy.py
COPY build/deploy.sh /app/deploy.sh
RUN chmod +x /app/deploy.sh
CMD ["/bin/bash"]
