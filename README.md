# Shadowrocket & V2RayTun — Proxy Routing Config

Конфигурация маршрутизации VPN для обхода блокировок. Правила автоматически подтягиваются клиентами через raw GitHub URLs.

## Клиенты

| Платформа | Клиент | Конфиг |
|-----------|--------|--------|
| iOS | [Shadowrocket](https://apps.apple.com/app/shadowrocket/id932747118) | `default.conf` / `KaminskiyVPN.conf` |
| Android | [V2RayTun](https://play.google.com/store/apps/details?id=free.v2ray.proxy.VPN) | `KaminskiyVPN.v2raytun.routing.json` |

## Файлы

- **`proxy.list`** — основной список доменов, IP и портов для проксирования. Источник правды для всех конфигов.
- **`default.conf`** — минимальная конфигурация Shadowrocket.
- **`KaminskiyVPN.conf`** — расширенная конфигурация Shadowrocket с исключениями для Kaspersky, Yandex Cloud и других российских сервисов.
- **`KaminskiyVPN.v2raytun.routing.json`** — конфигурация маршрутизации V2RayTun, генерируется из `proxy.list`.

## Логика маршрутизации

1. Домены/IP из `proxy.list` → **PROXY**
2. Российские IP (GeoIP RU) → **DIRECT**
3. Всё остальное → **DIRECT**

## Какие сервисы проксируются

- **AI**: Google Gemini, Claude (Anthropic), ChatGPT (OpenAI)
- **Соцсети**: Instagram, Facebook, Twitter/X, LinkedIn, Telegram, WhatsApp
- **Видео**: YouTube, Netflix, Disney+, Vimeo, TikTok
- **Медиа**: BBC, Medium, Quora, SoundCloud
- **Прочее**: Proton Mail, Canva, GoDaddy и др.

## Установка

### Shadowrocket (iOS)

Добавьте URL конфига в настройках:

```
https://raw.githubusercontent.com/mkaminskiy/shadowrocket/main/KaminskiyVPN.conf
```

или минимальный вариант:

```
https://raw.githubusercontent.com/mkaminskiy/shadowrocket/main/default.conf
```

Конфиг обновляется автоматически (интервал 60 сек).

### V2RayTun (Android)

Маршрутизация доставляется автоматически через HTTP-заголовок `routing` в подписке 3x-ui. При обновлении подписки V2RayTun применяет правила маршрутизации без ручного импорта.

Для ручного импорта: загрузите `KaminskiyVPN.v2raytun.routing.json` в настройках маршрутизации приложения.

## Как обновляются правила

1. Изменения вносятся в `proxy.list` → генерируется `KaminskiyVPN.v2raytun.routing.json` → push в GitHub
2. **Shadowrocket**: читает `proxy.list` напрямую из GitHub (автообновление каждые 60 сек)
3. **V2RayTun**: сервер каждые 5 минут подтягивает JSON из GitHub и отдаёт его в заголовке подписки; клиент обновляет подписку каждый час
