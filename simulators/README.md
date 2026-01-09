# Simulators / Emulators  Halo Test Lab

Questo repository QA incorpora un layer di simulazione per rendere i test E2E ripetibili (deterministici) e audit-ready.

## Simulatori implementati
- Gateway Stub Simulator: avvio/arresto/status con PID + log (porta 8080, /health).

## Roadmap (non in questo step)
- Android Emulator Harness (adb + emulator)
- Watch/BLE proxy harness per Xiaomi Watch S1 Pro
- Glasses simulator (event stream) e replay deterministico