FROM python:3.7-alpine
WORKDIR /apimon
COPY . /apimon
RUN pip install -r requirements.txt
EXPOSE 80
CMD ["python", "app.py"]