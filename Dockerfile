FROM python:3.8.8
WORKDIR /app
EXPOSE 8501
ADD . /app
ENTRYPOINT ["bash","./entrypoint.sh"]