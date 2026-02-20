FROM python:3.11-slim-bookworm

COPY . /su600
WORKDIR /su600

# 使用 requirements.txt 管理依赖，便于版本维护
RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x RunPython.sh

CMD ["./RunPython.sh"]