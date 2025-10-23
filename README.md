<p align="center">
  <img src="brands/elkbledom_fastlink/icon.png" width="120" height="120" alt="ELK-BLEDOM FastLink Icon">
</p>

<h1 align="center">💡 ELK-BLEDOM FastLink</h1>

<p align="center">
  <em>Fast & Stable BLE integration for ELK-BLEDOM lights in Home Assistant</em><br>
  <em>Быстрая и стабильная BLE-интеграция для лент ELK-BLEDOM в Home Assistant</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Bluetooth-0082FC?style=for-the-badge&logo=bluetooth&logoColor=white" alt="Bluetooth">
  <img src="https://img.shields.io/badge/Home%20Assistant-41BDF5?style=for-the-badge&logo=home-assistant&logoColor=white" alt="Home Assistant">
</p>

<p align="center">
  <a href="https://hacs.xyz/">
    <img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge" alt="HACS Custom">
  </a>
  <a href="https://www.home-assistant.io/">
    <img src="https://img.shields.io/badge/Home%20Assistant-Ready-41BDF5?style=for-the-badge&logo=home-assistant" alt="Home Assistant Ready">
  </a>
</p>

<p align="center">
  <a href="#-in-english">🇬🇧 English</a> |
  <a href="#-на-русском">🇷🇺 Русский</a>
</p>

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
2. Add this repository:  
   `https://github.com/Satimaro/elkbledom-fastlink`  
   Type: **Integration**  
3. Find **ELK-BLEDOM FastLink** and install it  
4. Restart Home Assistant  
5. Add the light via **Settings → Integrations → ELK-BLEDOM FastLink**

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

- **Domain:** `elkbledom_fastlink`  
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
2. Добавь ссылку на репозиторий:  
   `https://github.com/Satimaro/elkbledom-fastlink`  
   Тип: **Integration**  
3. Найди **ELK-BLEDOM FastLink** в списке и установи  
4. Перезапусти Home Assistant  
5. Добавь устройство через **Настройки → Интеграции → ELK-BLEDOM FastLink**

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

- **Домен:** `elkbledom_fastlink`  
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
