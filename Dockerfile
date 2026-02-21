FROM python:3.9-slim-bullseye
COPY . ./su600
WORKDIR /su600
RUN pip install paho-mqtt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
RUN rm -f Dockerfile
RUN chmod +x RunPython.sh 
CMD ./RunPython.sh