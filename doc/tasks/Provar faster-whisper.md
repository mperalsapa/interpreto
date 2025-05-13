[faster-whisper](https://github.com/SYSTRAN/faster-whisper) es una reimplementació de whisper pero molt mes ràpida i eficient.

Per provar faster-whisper, hem de tenir instal·lades les llibreries `cuBLAS` i `cuDNN`.

# Comparativa

Les següents proves s'han realitzat sobre 5 minuts d'audio.



## faster-whisper

| Temps | Inferenciat per    | Sistema          |
| ----- | ------------------ | ---------------- |
| 4m54s | CPU - i7 11700K    | PC               |
| 4m36s | CPU - i7 6700HQ    | Portatil         |
| 2m16s | GPU - NV T1000 8GB | Workstation SAPA |
| 2m14s | CPU - i7 12700     | Workstation SAPA |
| 1m41s | GPU - GTX 1060 6GB | PC               |


## Whisper v3 Turbo

| Temps | Inferenciat per    |
| ----- | ------------------ |
| 8m36s | CPU - i7 6700HQ    |
| 4m18s | GPU - GTX 970m 3GB |

