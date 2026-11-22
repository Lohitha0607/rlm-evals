FROM python:3.12-slim
WORKDIR /app
COPY build/gen_tests.py /tmp/gen_tests.py
# Generate the output at build time and delete the generator, so the answer is only in the output.
RUN mkdir -p /var/lib/app-data && python3 /tmp/gen_tests.py > /var/lib/app-data/output.txt && rm /tmp/gen_tests.py
COPY build/run_tests.sh /app/run_tests.sh
RUN chmod +x /app/run_tests.sh
CMD ["/bin/bash"]
