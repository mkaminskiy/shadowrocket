# Автоматизация обновления конфигурации

## Обзор

При изменении `proxy.list` и push в GitHub, V2RayTun routing JSON автоматически регенерируется через GitHub Actions.

## Как это работает

1. **Триггер**: При push коммита, изменяющего `proxy.list`, в ветку `main`
2. **Генерация**: GitHub Actions запускает `generate_routing.py`
3. **Коммит**: Если JSON изменился, создаётся автоматический коммит с обновлённым файлом
4. **Доставка**: VPN сервер скачивает обновлённый JSON через cron (каждые 5 минут)

## Файлы

- **`generate_routing.py`** — Python скрипт для конвертации proxy.list → V2RayTun JSON
- **`.github/workflows/update-routing.yml`** — GitHub Actions workflow
- **`proxy.list`** — Source of truth для всех правил маршрутизации
- **`KaminskiyVPN.v2raytun.routing.json`** — Автоматически генерируемый файл (не редактировать вручную!)

## Workflow

```
proxy.list изменён → git commit → git push
                                      ↓
                            GitHub Actions триггер
                                      ↓
                          python3 generate_routing.py
                                      ↓
                    JSON обновлён → auto commit → push
                                      ↓
                          GitHub raw URL обновлён
                                      ↓
                VPN сервер скачивает (каждые 5 мин)
                                      ↓
                      V2RayTun клиенты получают обновление
```

## Локальный запуск

Для ручной генерации JSON:

```bash
python3 generate_routing.py
```

Скрипт:
- Парсит `proxy.list`
- Группирует правила по комментариям (#Group Name)
- Конвертирует в V2Ray JSON формат
- Сохраняет в `KaminskiyVPN.v2raytun.routing.json`

## Правила конвертации

| proxy.list              | V2Ray JSON                |
|-------------------------|---------------------------|
| `DOMAIN-SUFFIX,x.com`   | `"domain:x.com"`          |
| `DOMAIN,api.x.com`      | `"full:api.x.com"`        |
| `DOMAIN-KEYWORD,foo`    | `"keyword:foo"`           |
| `IP-CIDR,x.x.x.x/y`     | добавляется в `ip` массив |
| `DST-PORT,3478`         | `"port": "3478,..."`      |

## Структура JSON

1. **Фиксированные правила** (не из proxy.list):
   - "Прямые домены" (direct) — Kaspersky, local, geoip:private
   - "Прямые RU" (direct) — geoip:ru

2. **Правила из proxy.list** (proxy):
   - Одно правило на каждую группу (#Group Name)
   - WhatsApp/Telegram включают домены + IP CIDR

3. **DST-PORT правила** (proxy):
   - "Голосовые и видеозвонки" — все порты в одной строке

4. **Default** (direct):
   - Catch-all правило, network: ["tcp"]

## Ручной workflow (без GitHub Actions)

Если нужно обновить JSON локально без push:

```bash
# 1. Отредактировать proxy.list
nano proxy.list

# 2. Сгенерировать JSON
python3 generate_routing.py

# 3. Проверить изменения
git diff KaminskiyVPN.v2raytun.routing.json

# 4. Закоммитить оба файла
git add proxy.list KaminskiyVPN.v2raytun.routing.json
git commit -m "update routing rules"
git push
```

## Отладка

Проверить количество правил:

```bash
python3 -c "
import json
data = json.load(open('KaminskiyVPN.v2raytun.routing.json'))
print(f'Total rules: {len(data[\"rules\"])}')
for i, r in enumerate(data['rules']):
    print(f'{i+1}. {r[\"__name__\"]}')
"
```

Ожидаемый результат: 16 правил (2 фиксированных + 12 из proxy.list + 1 DST-PORT + 1 default)

## Примечания

- Названия групп в proxy.list должны точно совпадать с желаемыми названиями в JSON
- Комментарии с URL (https://...) и после DST-PORT игнорируются
- UUID генерируются случайно при каждом запуске (это нормально)
