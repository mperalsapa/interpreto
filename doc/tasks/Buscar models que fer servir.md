Possibles models que es poden fer servir:

# [Whisper 3 Turbo](https://huggingface.co/openai/whisper-large-v3-turbo)
Es multi llenguatge, i genera transcripcions amb temps, per al que pot retornar un vtt*

# [Vosk](https://alphacephei.com/vosk/)
Genera transcripcions, però és específic de cada llenguatge. És molt lleuger (50 MB per llenguatge). Pot ser, té la possibilitat de generar [fitxers srt](https://github.com/alphacep/vosk-api/issues/1347)

# Detecció d’idioma
En cas de fer servir un model com Vosk, s’ha de fer servir un model d'identificació d’idioma extra.

[language_detector](https://huggingface.co/fitlemon/language_detector) - Basat en Whisper, detecta l’idioma
