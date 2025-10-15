FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV MONGO_URI="mongodb+srv://ak_db_user:akdbuser1234@cluster0.pdhavjz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
CMD ["python", "app.py"]