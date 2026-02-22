# Используем готовый образ с Chrome от сообщества
FROM joyzoursky/python-chromedriver:3.12

# Устанавливаем только Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бота
COPY bot.py .

# Запускаем
CMD ["python", "bot.py"]
