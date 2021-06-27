

FROM postgres:13.3
COPY *.sql /docker-entrypoint-initdb.d/

FROM python:3
# set a directory for the app
WORKDIR /usr/src/app

# copy all the files to the container
COPY . .

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# tell the port number the container should expose
EXPOSE 5000

ENV DEV_DATABASE_URL="postgresql+psycopg2://crisisprofile@localhost/crisisprofile"

# run the command
CMD ["flask", "run", "--host=0.0.0.0"]