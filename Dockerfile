FROM python:3.11-bullseye
RUN apt-get update && apt-get install vim ffmpeg build-essential libssl-dev ca-certificates libasound2 wget -y
COPY . /code
WORKDIR /code/dayatani_chatbot
RUN pip install -r requirements.txt
ENTRYPOINT [ "/bin/bash", "/code/entrypoint.sh"]
CMD [ "python", "manage.py", "runserver", "0.0.0.0:8000"]
