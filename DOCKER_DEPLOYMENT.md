# Docker Deployment Guide - Система автомобильного детейлинга

## Содержание
1. [Предварительные требования](#предварительные-требования)
2. [Структура Docker Compose](#структура-docker-compose)
3. [Порядок запуска](#порядок-запуска)
4. [Проверка работоспособности](#проверка-работоспособности)
5. [Управление сервисами](#управление-сервисами)
6. [Мониторинг и логи](#мониторинг-и-логи)
7. [Проблемы и решения](#проблемы-и-решения)
8. [Production deployment](#production-deployment)

---

## Предварительные требования

### Необходимое ПО
- **Docker**: версия 20.10 или новее
- **Docker Compose**: версия 2.0 или новее

### Проверка версий
```bash
docker --version
# Docker version 20.10.x или новее

docker-compose --version
# Docker Compose version 2.x.x или новее
```

### Системные требования
- **RAM**: минимум 4GB, рекомендуется 8GB
- **Disk**: минимум 5GB свободного места
- **CPU**: 2 cores минимум, рекомендуется 4 cores

---

## Структура Docker Compose

### Файл docker-compose.yml

Расположение: `/Users/fr4lzen/Documents/мирэа/микросы/пр7/project/docker-compose.yml`

### Сервисы инфраструктуры

#### postgres-db
```yaml
postgres-db:
  image: postgres:14-alpine
  ports:
    - "5432:5432"
  environment:
    POSTGRES_USER: detailing_user
    POSTGRES_PASSWORD: detailing_pass
    POSTGRES_DB: detailing_db
  volumes:
    - postgres_data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U detailing_user"]
    interval: 10s
    timeout: 5s
    retries: 5
  restart: unless-stopped
```

**Особенности**:
- Alpine образ (минимальный размер)
- Persistent volume для сохранения данных
- Healthcheck для корректного порядка запуска
- Автоматический перезапуск

#### rabbitmq
```yaml
rabbitmq:
  image: rabbitmq:3-management
  ports:
    - "5672:5672"    # AMQP
    - "15672:15672"  # Management UI
  environment:
    RABBITMQ_DEFAULT_USER: guest
    RABBITMQ_DEFAULT_PASS: guest
  healthcheck:
    test: ["CMD", "rabbitmq-diagnostics", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
  restart: unless-stopped
```

**Особенности**:
- Management UI на порту 15672
- Healthcheck для готовности очередей
- Автоматический перезапуск

### Микросервисы

#### user-service (с PostgreSQL)
```yaml
user-service:
  build:
    context: ./user-service
    dockerfile: Dockerfile
  ports:
    - "8001:8001"
  environment:
    - POSTGRES_URL=postgresql+asyncpg://detailing_user:detailing_pass@postgres-db:5432/detailing_db
  depends_on:
    postgres-db:
      condition: service_healthy
  restart: on-failure
```

**ВАЖНО**: Миграции Alembic применяются автоматически при старте через CMD в Dockerfile

#### order-service (HTTP client)
```yaml
order-service:
  build:
    context: ./order-service
    dockerfile: Dockerfile
  ports:
    - "8003:8003"
  environment:
    - CAR_SERVICE_URL=http://car-service:8002
  depends_on:
    - car-service
  restart: on-failure
```

**ВАЖНО**: Должен стартовать после car-service

#### payment-service (RabbitMQ Publisher)
```yaml
payment-service:
  build:
    context: ./payment-service
    dockerfile: Dockerfile
  ports:
    - "8005:8005"
  environment:
    - AMQP_URL=amqp://guest:guest@rabbitmq:5672/
  depends_on:
    rabbitmq:
      condition: service_healthy
  restart: on-failure
```

#### bonus-service (RabbitMQ Consumer)
```yaml
bonus-service:
  build:
    context: ./bonus-service
    dockerfile: Dockerfile
  ports:
    - "8006:8006"
  environment:
    - AMQP_URL=amqp://guest:guest@rabbitmq:5672/
  depends_on:
    rabbitmq:
      condition: service_healthy
  restart: on-failure
```

### Сеть
```yaml
networks:
  default:
    name: detailing-network
    driver: bridge
```

**Особенности**:
- Все сервисы в одной сети
- DNS резолвинг по имени сервиса
- Изоляция от других Docker сетей

### Volumes
```yaml
volumes:
  postgres_data:
    driver: local
```

**Особенности**:
- Данные PostgreSQL сохраняются между перезапусками
- Удаляются только с флагом `-v`

---

## Порядок запуска

### 1. Полная сборка и запуск
```bash
cd /Users/fr4lzen/Documents/мирэа/микросы/пр7/project
docker-compose up --build -d
```

**Флаги**:
- `--build`: Пересобрать образы (при изменении кода)
- `-d`: Detached mode (фоновый режим)

**Порядок запуска автоматический**:
1. postgres-db (с healthcheck)
2. rabbitmq (с healthcheck)
3. Сервисы без зависимостей (car, cart, fines, support)
4. user-service (после postgres-db healthy)
5. order-service (после car-service)
6. payment-service (после rabbitmq healthy)
7. bonus-service (после rabbitmq healthy)

**Время запуска**: 30-60 секунд

### 2. Запуск без пересборки
```bash
docker-compose up -d
```

Используется, если код не изменялся.

### 3. Запуск отдельного сервиса
```bash
docker-compose up -d user-service
```

Автоматически запустит зависимости (postgres-db).

### 4. Запуск с логами в консоли
```bash
docker-compose up --build
```

Без флага `-d` - логи выводятся в терминал (Ctrl+C для остановки).

---

## Проверка работоспособности

### 1. Статус всех сервисов
```bash
docker-compose ps
```

**Ожидаемый вывод**:
```
NAME                STATUS              PORTS
postgres-db         Up (healthy)        0.0.0.0:5432->5432/tcp
rabbitmq            Up (healthy)        0.0.0.0:5672->5672/tcp, 0.0.0.0:15672->15672/tcp
user-service        Up                  0.0.0.0:8001->8001/tcp
car-service         Up                  0.0.0.0:8002->8002/tcp
order-service       Up                  0.0.0.0:8003->8003/tcp
cart-service        Up                  0.0.0.0:8004->8004/tcp
payment-service     Up                  0.0.0.0:8005->8005/tcp
bonus-service       Up                  0.0.0.0:8006->8006/tcp
fines-service       Up                  0.0.0.0:8007->8007/tcp
support-service     Up                  0.0.0.0:8008->8008/tcp
```

**ВАЖНО**: postgres-db и rabbitmq должны быть `(healthy)`

### 2. Health checks
```bash
# Проверка всех health endpoints
for i in {1..8}; do
  echo "Service 800$i:"
  curl -s http://localhost:800$i/health | jq
done
```

### 3. Swagger UI
Открыть в браузере:
- http://localhost:8001/docs (user-service)
- http://localhost:8002/docs (car-service)
- http://localhost:8003/docs (order-service)
- ... и так далее

### 4. RabbitMQ Management UI
```
URL: http://localhost:15672
Login: guest
Password: guest
```

Проверить:
- Connections: должно быть 2 (payment-service, bonus-service)
- Queues: должна быть `payment_succeeded_queue`

### 5. PostgreSQL подключение
```bash
docker-compose exec postgres-db psql -U detailing_user -d detailing_db -c "\dt"
```

Должна быть таблица `users` и `alembic_version`.

---

## Управление сервисами

### Остановка всех сервисов
```bash
docker-compose stop
```

Контейнеры останавливаются, но не удаляются.

### Остановка отдельного сервиса
```bash
docker-compose stop user-service
```

### Запуск остановленных сервисов
```bash
docker-compose start
```

### Перезапуск сервиса
```bash
docker-compose restart user-service
```

### Полное удаление контейнеров
```bash
docker-compose down
```

**ВАЖНО**: Volumes (PostgreSQL данные) сохраняются.

### Удаление с volumes
```bash
docker-compose down -v
```

**ВНИМАНИЕ**: Удалит все данные PostgreSQL!

### Пересборка одного сервиса
```bash
docker-compose build user-service
docker-compose up -d user-service
```

### Масштабирование (если нужно)
```bash
docker-compose up -d --scale cart-service=3
```

---

## Мониторинг и логи

### Логи всех сервисов
```bash
docker-compose logs -f
```

Флаг `-f` для follow (real-time).

### Логи конкретного сервиса
```bash
docker-compose logs -f user-service
```

### Последние N строк логов
```bash
docker-compose logs --tail=100 user-service
```

### Логи с временными метками
```bash
docker-compose logs -f -t user-service
```

### Поиск в логах
```bash
docker-compose logs user-service | grep "ERROR"
docker-compose logs payment-service | grep "payment_succeeded"
```

### Статистика ресурсов
```bash
docker stats
```

Показывает CPU, Memory, Network для каждого контейнера.

### Inspect контейнера
```bash
docker-compose exec user-service env
```

Показывает переменные окружения.

---

## Проблемы и решения

### Проблема: user-service не стартует

**Симптомы**:
```
user-service    | sqlalchemy.exc.OperationalError: connection refused
```

**Решение**:
1. Проверить статус postgres-db:
```bash
docker-compose ps postgres-db
# Должен быть "Up (healthy)"
```

2. Если не healthy, проверить логи:
```bash
docker-compose logs postgres-db
```

3. Перезапустить postgres-db:
```bash
docker-compose restart postgres-db
```

4. Подождать 10-15 секунд до статуса healthy

### Проблема: order-service возвращает 404 при создании заказа

**Причина**: car-service не запущен или car_id не существует

**Решение**:
1. Проверить статус car-service:
```bash
docker-compose ps car-service
```

2. Проверить что car-service доступен:
```bash
docker-compose exec order-service curl http://car-service:8002/health
```

3. Добавить автомобиль:
```bash
curl -X POST http://localhost:8002/api/cars -H "Content-Type: application/json" \
  -d '{"owner_id":"550e8400-e29b-41d4-a716-446655440000","license_plate":"А123БВ799","vin":"XTA210930V0123456","make":"Lada","model":"Vesta","year":2021}'
```

### Проблема: bonus-service не получает события от payment-service

**Симптомы**: Логи bonus-service не показывают "Accrued bonuses"

**Решение**:
1. Проверить RabbitMQ Management UI (localhost:15672)
   - Queues → должна быть `payment_succeeded_queue`
   - Connections → должно быть 2 подключения

2. Проверить логи payment-service:
```bash
docker-compose logs payment-service | grep "published"
```

3. Проверить логи bonus-service:
```bash
docker-compose logs bonus-service | grep "RabbitMQ"
```

4. Перезапустить оба сервиса:
```bash
docker-compose restart payment-service bonus-service
```

### Проблема: Port already in use

**Симптомы**:
```
ERROR: for user-service  Cannot start service user-service:
Bind for 0.0.0.0:8001 failed: port is already allocated
```

**Решение**:
1. Найти процесс на порту:
```bash
lsof -i :8001
```

2. Убить процесс:
```bash
kill -9 <PID>
```

3. Или изменить порт в docker-compose.yml:
```yaml
ports:
  - "8101:8001"  # Внешний порт 8101, внутренний 8001
```

### Проблема: Out of memory

**Симптомы**: Контейнеры случайно останавливаются

**Решение**:
1. Увеличить лимиты в Docker Desktop (Preferences → Resources)

2. Или добавить memory limits в docker-compose.yml:
```yaml
services:
  user-service:
    mem_limit: 512m
```

### Проблема: Slow build

**Решение**:
1. Использовать build cache:
```bash
docker-compose build --parallel
```

2. Оптимизировать Dockerfile (уже оптимизированы с layer caching)

---

## Production Deployment

### Рекомендации для production

#### 1. Переменные окружения
Не хардкодить credentials в docker-compose.yml!

Использовать `.env` файл:
```bash
# .env
POSTGRES_USER=prod_user
POSTGRES_PASSWORD=strong_password_here
JWT_SECRET_KEY=random_secret_key_256_bits
```

docker-compose.yml:
```yaml
environment:
  - POSTGRES_USER=${POSTGRES_USER}
  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
```

#### 2. Volumes для логов
```yaml
volumes:
  - ./logs:/app/logs
```

#### 3. Resource limits
```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 256M
```

#### 4. Healthchecks для микросервисов
```yaml
user-service:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

#### 5. Restart policies
```yaml
restart: unless-stopped  # Для инфраструктуры
restart: on-failure      # Для микросервисов
```

#### 6. Логирование
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

#### 7. Сеть
```yaml
networks:
  backend:
    driver: bridge
  frontend:
    driver: bridge

services:
  user-service:
    networks:
      - backend
```

#### 8. Secrets (Docker Swarm)
```yaml
secrets:
  postgres_password:
    external: true

services:
  user-service:
    secrets:
      - postgres_password
```

#### 9. Reverse Proxy (Nginx)
```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
  depends_on:
    - user-service
    - car-service
    # ... все сервисы
```

#### 10. Мониторинг (Prometheus + Grafana)
```yaml
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
```

---

## Быстрые команды (Cheat Sheet)

```bash
# Запуск
docker-compose up -d

# Пересборка и запуск
docker-compose up --build -d

# Статус
docker-compose ps

# Логи
docker-compose logs -f <service>

# Остановка
docker-compose stop

# Перезапуск
docker-compose restart <service>

# Удаление
docker-compose down

# Удаление с volumes
docker-compose down -v

# Exec в контейнер
docker-compose exec <service> bash

# Статистика ресурсов
docker stats

# Очистка неиспользуемых образов
docker image prune -a
```

---

## Дополнительные ресурсы

- **Docker Compose документация**: https://docs.docker.com/compose/
- **FastAPI Best Practices**: https://fastapi.tiangolo.com/
- **PostgreSQL Docker**: https://hub.docker.com/_/postgres
- **RabbitMQ Docker**: https://hub.docker.com/_/rabbitmq

---

**Документ создан для Практической Работы №6**
**Дата: 2024**
**Автор: Система автомобильного детейлинга**
