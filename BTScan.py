#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 BTScan.py — Утилита для поиска BLE-устройств (Elkbledom, LEDBLE, MELK и т.п.)
Автор: Satimaro
Версия: 1.0.0

Использует BluePy для сканирования Bluetooth Low Energy устройств.
Выводит MAC, RSSI, имя и поддерживаемые сервисы.
"""

from bluepy.btle import Scanner, DefaultDelegate, BTLEException
import logging
import sys
import time

# -----------------------------------------------
# Настройки логирования
# -----------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S"
)
_LOGGER = logging.getLogger("BTScan")

# -----------------------------------------------
# Ключевые слова для фильтрации устройств
# -----------------------------------------------
TARGET_NAMES = [
    "ELK-BLE", "ELK-BLEDDM", "LEDBLE", "MELK", "ELK-BULB", "ELK-LAMPL"
]

# -----------------------------------------------
# Обработчик событий сканирования
# -----------------------------------------------
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            _LOGGER.debug("🔹 Найдено новое устройство: %s", dev.addr)
        elif isNewData:
            _LOGGER.debug("🔄 Обновлены данные устройства: %s", dev.addr)


# -----------------------------------------------
# Основной класс сканирования
# -----------------------------------------------
class BluetoothScanner:
    def __init__(self, duration: int = 10):
        self.duration = duration
        self.scanner = Scanner().withDelegate(ScanDelegate())

    def scan(self):
        """Выполняет сканирование BLE-устройств."""
        _LOGGER.info("🚀 Начало сканирования BLE (%s секунд)...", self.duration)
        try:
            devices = self.scanner.scan(self.duration)
        except BTLEException as e:
            _LOGGER.error("Ошибка Bluetooth: %s", e)
            sys.exit(1)

        if not devices:
            _LOGGER.warning("❌ Устройства не найдены. Убедись, что Bluetooth включён.")
            return

        _LOGGER.info("📡 Найдено %d устройств:", len(devices))
        print("=" * 70)
        print(f"{'MAC-адрес':<20} {'RSSI (дБ)':<10} {'Имя устройства':<25} {'Тип'}")
        print("=" * 70)

        for dev in devices:
            name = None
            for (_, desc, value) in dev.getScanData():
                if desc.lower() == "complete local name":
                    name = value
                    break

            target_flag = ""
            if name and any(key.lower() in name.lower() for key in TARGET_NAMES):
                target_flag = "⭐"
            elif name is None:
                name = "(Без имени)"

            print(f"{dev.addr:<20} {dev.rssi:<10} {name:<25} {target_flag}")

        print("=" * 70)
        _LOGGER.info("✅ Сканирование завершено.")


# -----------------------------------------------
# Запуск из консоли
# -----------------------------------------------
if __name__ == "__main__":
    try:
        duration = 10
        if len(sys.argv) > 1:
            duration = int(sys.argv[1])

        scanner = BluetoothScanner(duration)
        scanner.scan()

        # Совет пользователю
        print("\n💡 Совет: чтобы повторить сканирование, запусти снова:")
        print("   python3 BTScan.py 15   # где 15 — длительность в секундах")

    except KeyboardInterrupt:
        print("\n⛔ Остановлено пользователем.")
        sys.exit(0)
    except Exception as e:
        _LOGGER.error("Непредвиденная ошибка: %s", e)
        time.sleep(1)
        sys.exit(1)
