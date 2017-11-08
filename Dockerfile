FROM python:3-alpine
MAINTAINER Ashkan Vahidishams "ashkan.vahidishams@sesam.io"
COPY ./service /service
WORKDIR /service

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

EXPOSE 5001/tcp
ENTRYPOINT ["python3"]
CMD ["cvpartner-rest.py"]