# 💡 ELK-BLEDOM Plus

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://hacs.xyz/) [![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Ready-41BDF5?style=for-the-badge&logo=home-assistant)](https://www.home-assistant.io/)
  
[🇷🇺 Русский](#-на-русском) | [🇬🇧 English](#-in-english)

---

## 🇷🇺 На русском

> 🧠 Улучшенная версия интеграции **ELK-BLEDOM** для Home Assistant  
> ⚡ Работает быстрее, стабильнее и с полной поддержкой эффектов, плавной яркостью и цветовой температурой.

---

### 🚀 Основные возможности

✅ Постоянное BLE-соединение — без засыпания  
✅ Мгновенный отклик и высокая стабильность  
✅ Плавная регулировка яркости без мёртвых зон  
✅ Полностью рабочие эффекты и управление скоростью  
✅ Эмуляция цветовой температуры (тёплый ↔ холодный RGB)  
✅ Оптимизация BLE-команд для лент **5050 RGB**  
✅ Улучшенная логика повторных подключений и автообновления состояния  

---

### 🛠️ Установка через HACS

1. Открой **HACS → Интеграции → Три точки → Пользовательские репозитории**  
2. Добавь ссылку на репозиторий: https://github.com/Satimaro/elkbledom-plus
Тип: **Integration**
3. Найди **ELK-BLEDOM Plus** в списке и установи  
4. Перезапусти Home Assistant  
5. Добавь устройство через **Настройки → Интеграции → ELK-BLEDOM Plus**

---

### ⚙️ Совместимость

| Контроллер | Поддержка |
|-------------|------------|
| ELK-BLEDOM  | ✅ Полная |
| LEDBLE       | ✅ Полная |
| MELK         | ✅ Полная |
| ELK-BULB / BULB2 | ✅ Полная |
| RGB 5050 LED Strip | ✅ Полная |

---

### 🧩 Улучшения по сравнению с оригиналом

- 🔄 Переписана логика BLE-соединения (скорость + устойчивость)  
- 🚀 Мгновенное восстановление связи при обрыве  
- 💡 Плавная и точная регулировка яркости  
- 🌈 Реализованы эффекты и регулировка их скорости  
- 🔥 Добавлена эмуляция цветовой температуры  
- 🧱 Устойчивость к ошибкам BLE и тайм-аутам  
- 🧰 Полная интеграция с интерфейсом Home Assistant  

---

### 📦 Информация

- **Домен:** `elkbledom`  
- **Платформы:** `light`, `number`  
- **Зависимости:** `bleak >= 0.22.2`, `bleak-retry-connector >= 3.5.0`  

---

### 👨‍💻 Авторство

Разработано и улучшено — **Satimaro (Ukraine)** 🇺🇦  
Оригинальная база: [dave-code-ruiz/elkbledom](https://github.com/dave-code-ruiz/elkbledom)

---

### ⭐ Поддержи проект

Если интеграция тебе понравилась — поставь ⭐ на GitHub!  
Это поможет другим пользователям найти стабильную и быструю версию ELK-BLEDOM ❤️  

---

---

## 🇬🇧 In English

> 🧠 Improved version of **ELK-BLEDOM** integration for Home Assistant  
> ⚡ Faster, more stable, with full effect support, smooth brightness control, and RGB-based color temperature emulation.

---

### 🚀 Key Features

✅ Persistent BLE connection (no sleep or lag)  
✅ Instant response and stable control  
✅ Smooth brightness curve with precise levels  
✅ Fully functional effects with adjustable speed  
✅ RGB-based color temperature emulation (warm ↔ cool)  
✅ Optimized BLE command timing for **5050 RGB** LED strips  
✅ Advanced reconnect and auto-update logic  

---

### 🛠️ Installation via HACS

1. Open **HACS → Integrations → Three dots → Custom repositories**  
2. Add this repository: https://github.com/Satimaro/elkbledom-plus
Type: **Integration**
3. Find **ELK-BLEDOM Plus** and install it  
4. Restart Home Assistant  
5. Add the light via **Settings → Integrations → ELK-BLEDOM Plus**

---

### ⚙️ Compatibility

| Controller | Status |
|-------------|---------|
| ELK-BLEDOM  | ✅ Full |
| LEDBLE      | ✅ Full |
| MELK        | ✅ Full |
| ELK-BULB / BULB2 | ✅ Full |
| RGB 5050 LED Strip | ✅ Full |

---

### 🧩 Improvements over the Original

- 🔄 Rewritten BLE connection logic (speed + stability)  
- 🚀 Instant reconnect after disconnection  
- 💡 Fixed and smoothed brightness scaling  
- 🌈 Full effect system with adjustable speed  
- 🔥 Added RGB color temperature emulation  
- 🧱 More resilient to BLE timeouts and errors  
- 🧰 Full Home Assistant UI integration  

---

### 📦 Integration Info

- **Domain:** `elkbledom`  
- **Platforms:** `light`, `number`  
- **Requirements:** `bleak >= 0.22.2`, `bleak-retry-connector >= 3.5.0`  

---

### 👨‍💻 Author

Developed and enhanced by **Satimaro (Ukraine)** 🇺🇦  
Original base: [dave-code-ruiz/elkbledom](https://github.com/dave-code-ruiz/elkbledom)

---

### ⭐ Support the Project

If you like this integration — give it a ⭐ on GitHub!  
Help others discover a faster, more stable ELK-BLEDOM experience ❤️
