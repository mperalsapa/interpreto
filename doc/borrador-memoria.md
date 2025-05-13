## Introducció

### Justificació del projecte escollit

La motivació principal d’aquest projecte neix de la necessitat d’oferir una millor accessibilitat al contingut audiovisual per a tothom, especialment per a persones amb discapacitat auditiva. En una societat on el consum de vídeos, pel·lícules i podcasts està en constant creixement, és fonamental que aquesta informació sigui accessible de forma universal. A més, aquest projecte també pot contribuir a superar barreres lingüístiques, afavorint la comprensió de contingut en idiomes estrangers.

### Definició del tema

El projecte consisteix en el desenvolupament d’un sistema automàtic de transcripció d’àudio a text, capaç de generar subtítols per a contingut audiovisual. El sistema estarà basat en tecnologies de reconeixement de veu i intel·ligència artificial, aprofitant els avenços recents en aquest camp per aconseguir una transcripció precisa i funcional en diferents contextos d’ús.

### Abast del treball

L’objectiu del projecte és desenvolupar un sistema funcional capaç de processar àudio i generar la corresponent transcripció escrita. No s’abordarà, però, la integració directa en plataformes comercials ni la traducció automàtica de subtítols. L'enfocament se centrarà en la qualitat i eficiència de la transcripció.

### Pla de treball

El projecte es dividirà en les següents fases:

1. **Investigació i anàlisi prèvia**: recerca sobre tecnologies existents de reconeixement de veu.
2. **Disseny del sistema**: elecció d’eines i definició de l’arquitectura de la solució.
3. **Implementació**: desenvolupament del sistema de transcripció.
4. **Verificació i proves**: avaluació de la precisió de les transcripcions en diferents situacions.
5. **Conclusions i documentació**: recull dels resultats i propostes de millora.

### Eines i entorn de treball

El projecte es desenvoluparà utilitzant eines d’IA com models de reconeixement de veu (per exemple, Whisper d’OpenAI, Google Speech-to-Text, o altres solucions de codi obert), i entorns de programació com Python, juntament amb biblioteques específiques per al tractament d’àudio.

### Objectius generals i específics

**Objectiu general**  
Desenvolupar un sistema automàtic de transcripció d’àudio a text que permeti generar subtítols precisos i útils per a diferents tipus de contingut audiovisual.

**Objectius específics**

- Investigar i analitzar diferents tecnologies de reconeixement de veu.
- Dissenyar i implementar un sistema de transcripció modular i escalable.
- Avaluar la precisió i rendiment del sistema amb àudios de diferents característiques.
- Estudiar possibles aplicacions reals del sistema en entorns d’accessibilitat i traducció.

## Cos del treball

### Anàlisi prèvia i elecció de tecnologia

Un dels primers passos del projecte ha estat la cerca i avaluació de models existents de reconeixement de veu, amb l’objectiu de determinar quina tecnologia oferia un millor equilibri entre precisió, rendiment i flexibilitat. Aquesta fase ha sigut clau per garantir la viabilitat del projecte, ja que les necessitats específiques com la detecció automàtica de l’idioma, la generació de subtítols amb marques de temps i la possibilitat d’adaptar-se a diferents entorns tècnics, han requerit una anàlisi comparativa rigorosa.

#### Models considerats

Es van considerar dos models principals:

- **Whisper (OpenAI - versió v3 turbo)**  
    Un model avançat, multilingüe, que ofereix transcripció precisa i amb marques de temps. A més, és capaç de detectar l’idioma automàticament i, en alguns casos, fer traduccions. Funciona amb GPU i permet generar fitxers `.vtt` que poden ser usats com subtítols.
    
- **Vosk (AlphaCephei)**  
    Un model lleuger i eficient (aproximadament 50 MB per llengua), però que només pot treballar amb un idioma per model. Tot i no disposar de funcionalitats avançades com la traducció, destaca pel seu bon rendiment en sistemes amb menys recursos i per permetre transcripció en streaming. Pot generar fitxers `.srt` amb una configuració addicional.
    

Per cobrir les funcionalitats que Vosk no ofereix per defecte, es va estudiar també l’ús d’un detector d’idioma extern com el model [language_detector](https://huggingface.co/fitlemon/language_detector), basat també en Whisper.

#### Comparativa tècnica

|Característica|Whisper|Vosk|
|---|---|---|
|Traducció|Sí|No|
|Transcripció|Sí|Sí|
|Detecció de llengua|Sí|Amb suport|
|Ús de GPU|Sí|Possible|
|Suport per streaming|No|Sí|

A més d’aquesta comparativa teòrica, es van dur a terme proves pràctiques amb un fragment d’àudio conegut: els primers 5 minuts de l’audiollibre _Harry Potter and the Philosopher’s Stone_. Es va comparar el resultat de la transcripció amb l’equivalent del text escrit original.

|Mesura|Whisper|Vosk|
|---|---|---|
|Durada|1m 51s (GPU)|20s|
|Precisió|Superior al 90%|80 - 90%|

Tot i que Vosk és molt més ràpid, especialment en sistemes sense GPU, la precisió del model Whisper va ser notablement superior. En concret, es van detectar errors importants en noms propis amb Vosk (ex: _Dursley_ → _Dazzly_), mentre que Whisper oferia una transcripció molt més fidel al text original.

### Arquitectura del sistema

L’arquitectura general del sistema es pot representar amb el següent diagrama de components:

![[Diagrama de components.svg]]
**Descripció dels components:**

- **Frontend**: Interfície gràfica on l’usuari pot pujar un vídeo i visualitzar-lo amb els subtítols generats.
- **Backend**: Gestor de processos que rep el fitxer de vídeo, l’envia al sistema de transcripció i retorna els resultats al frontend.
- **Mòduls de processament**:
    - _Detecció de l’idioma_: Identifica l’idioma del contingut per escollir el model adequat o activar la traducció.
    - _Generació dels subtítols_: Transcriu l’àudio a text amb marques de temps.
    - _Traducció (opcional)_: Si l’idioma detectat és diferent del preferit per l’usuari, tradueix els subtítols generats.


### Formats de fitxers de subtítols

Un cop generats els textos transcrits, cal convertir-los a un format estàndard que pugui ser integrat fàcilment en reproductors de vídeo o aplicacions web. Durant la fase d’investigació es van identificar els dos formats de subtítols més utilitzats:

- **SRT (SubRip Subtitle)**  
    És un dels formats més coneguts i àmpliament acceptats. Cada bloc conté el número de seqüència, el temps d’inici i de finalització, i el text corresponent. És molt senzill i compatible amb la gran majoria de reproductors i editors.
    
- **VTT (WebVTT - Web Video Text Tracks)**  
    Basat en SRT però amb millores per a aplicacions web. Permet formatar el text (negreta, cursiva), definir estils, i fins i tot afegir metadades. És especialment útil per integració en reproductors HTML5 i aplicacions modernes.
    

Tenint en compte l’objectiu de fer una eina adaptable a diferents contextos (reproductors offline i plataformes web), es va optar per implementar la generació dels dos formats, segons l’escenari on es necessiti.

### Generació d’un dataset de prova

Per poder fer una avaluació objectiva del rendiment dels models en múltiples situacions, es va decidir construir un petit dataset de proves amb àudios reals i recents. El fragment inicial de l’audiollibre de _Harry Potter_ va ser útil per a una primera comparativa, però insuficient per a una valoració completa de casos d’ús diversos. Així doncs, es va optar per generar un conjunt d’àudios a partir de pel·lícules comercials estrenades durant el 2024.

#### Selecció de pel·lícules

La selecció es va fer a partir d’una biblioteca personal de pel·lícules, filtrant les més recents (2024) i escollint-ne una mostra representativa. Aquesta llista inclou pel·lícules amb una gran varietat de gèneres i estils de diàleg, la qual cosa ajuda a avaluar el sistema en entorns diferents (acció, animació, documental, etc.).

Exemples de pel·lícules seleccionades:

- _Kung Fu Panda 4_
    
- _Gru 4. Mi villano favorito_
    
- _Furiosa. De la saga Mad Max_
    
- _Dune. Parte dos_
    
- _Rebel Moon (Parte dos)_
    
- _La vida secreta de los orangutanes_
    

#### Extracció d’àudio

Per extreure els fragments d’àudio, es va fer servir l’eina **FFmpeg**, que permet tallar i convertir vídeos de manera eficient. Es van extreure 5 minuts d’àudio començant al minut 20, amb l’objectiu de capturar escenes amb diàlegs ja establerts i evitar introduccions silencioses o crèdits.

L’script utilitzat (en PowerShell) automatitza aquest procés:

```powershell
Get-Content "peliculas.txt" | ForEach-Object {
  ffmpeg -i $_ -ss 00:20:00 -t 00:05:00 -vn -acodec mp3 -ar 44100 -ac 2 ("audio_dataset\" + [System.IO.Path]::GetFileNameWithoutExtension($_) + ".mp3")
}
```

El resultat final va ser un conjunt de fitxers `.mp3` que formen el dataset de prova, tots amb noms normalitzats i provinents de pel·lícules diverses. Aquests àudios es van utilitzar per posar a prova la robustesa del sistema de transcripció i verificar com es comportaven els models davant diferents veus, accents, sorolls de fons i velocitats de parla.

Llistat parcial de fitxers generats:

```
Dune_Parte_dos_(2024)_Cast.mp3  
Furiosa_De_la_saga_Mad_Max_(2024)_Cast.mp3  
Kung_Fu_Panda_4_(2024)_Cast.mp3  
Rebel_Moon_(Parte_dos)_Cast.mp3  
...
```






### Implementació tècnica del pipeline de transcripció

Per tal de generar automàticament els fitxers de subtítols a partir dels fragments d’àudio preparats, es va implementar un pipeline de transcripció basat en el model _Faster-Whisper_, una versió optimitzada del model Whisper original desenvolupat per OpenAI.

Aquest pipeline permet transcriure arxius d’àudio de forma ràpida i precisa, exportant el resultat en format `.srt`. Inicialment, es va desenvolupar un script senzill que carregava l’arxiu d’àudio, aplicava la transcripció per segments i generava el fitxer de subtítols final.

#### Versió bàsica del sistema

En la versió inicial del script es realitzava la següent seqüència de passos:

1. **Carrega del model** Whisper (_turbo_) en GPU amb precisió `float32`.
2. **Processament seqüencial** de l’àudio complet amb el mètode `model.transcribe()`.
3. **Conversió de temps** a format `HH:MM:SS,mmm` per a generar el fitxer `.srt`.
4. **Exportació** de la transcripció a un fitxer SRT en la carpeta `output/`.

Aquesta aproximació funcionava bé amb àudios curts (com els fragments de 5 minuts del dataset de prova), però es van detectar dues limitacions importants:

- **Degradació de la precisió** en àudios llargs, on el model semblava perdre context o fer errors acumulats.
- **Temps de processament elevat** per àudios de més durada, especialment si contenien períodes llargs sense veu.

#### Millora amb detecció de veu (VAD)

Per solucionar aquestes limitacions, es va implementar una segona versió del pipeline combinant Whisper amb un sistema de detecció de veu (Voice Activity Detection, VAD) mitjançant el model _Silero VAD_.

Aquest nou enfocament introdueix una etapa prèvia on es detecten únicament els segments amb parla, descartant silencis i reduint la càrrega computacional. El procés complet inclou:

1. **Conversió de l’àudio** original a WAV mono i 16 kHz (format requerit per Silero).
2. **Aplicació del model Silero VAD** per detectar intervals amb veu. Es descarten segments massa curts i es poden ajustar paràmetres com `min_silence_duration_ms` o `speech_pad_ms` per adaptar-se a diferents tipus d’àudio.
3. **Extracció i guardat temporal dels segments de veu** com a fitxers WAV individuals.
4. **Transcripció independent** de cada segment detectat mitjançant _Faster-Whisper_.
5. **Construcció del fitxer SRT**, unificant les transcripcions en un únic fitxer amb timestamps acurats.

Aquest mètode va aportar diversos avantatges:
- Millor gestió de recursos en àudios llargs.
- Augment de la precisió en la transcripció, especialment en àudios amb intervals de silenci o amb escenes de soroll no vocal.
- Possibilitat de paralel·litzar futurs processaments per segment.


Tot i la millora, es van identificar nous reptes: la detecció de veu pot truncar frases si els paràmetres no estan ben calibrats, i pot aparèixer una lleu desconnexió semàntica entre segments molt curts. Malgrat això, el guany en eficiència i qualitat fa que aquest mètode sigui més robust i recomanable per escenaris reals.

### Disseny i desenvolupament del prototip funcional

Un cop resolts els problemes de precisió amb l’ús de VAD per a la detecció de veu, es va avançar cap al desenvolupament d’un **prototip funcional complet**, pensat per permetre la càrrega, transcripció i visualització de subtítols a partir de fitxers d’àudio o vídeo de manera interactiva. Aquest sistema es va construir seguint una arquitectura de **sis components principals**, distribuïts entre el frontend i el backend.

#### Frontend

1. **Interfície d’usuari (React)**  
    Es va implementar una interfície web utilitzant React que permet als usuaris:
    - Carregar fitxers d’àudio o vídeo.
    - Visualitzar els subtítols generats en temps real en un reproductor integrat.
    - Rebre els fragments transcrits de manera asincrònica i construir dinàmicament els subtítols en format **WebVTT**, adequat per a la visualització en entorns web.
2. **Servidor web (API + Controlador)**  
    Aquest component actua com a intermediari entre la UI i el backend. S’encarrega de:
    - Rebre i pujar els fitxers dels usuaris a **MinIO**, un servei d’emmagatzematge compatible amb S3.
    - Registrar els metadades del fitxer a **MongoDB** (hash, nom, format...).
    - Afegir una nova entrada a la cua de processament.
    - Escoltar els missatges enviats pels **workers** via Redis i retransmetre'ls a la UI per a la seva visualització immediata.
#### Backend

3. **MongoDB**  
    Base de dades principal on es registren:
    - Els metadades dels fitxers (hash, nom, mida...).
    - Els resultats de les transcripcions, per facilitar consultes i descàrregues posteriors.
    - La **cua de processament**, implementada com una col·lecció específica, que indica quins fitxers estan pendents de transcripció.
4. **Redis (Pub/Sub)**  
    Redis s'utilitza com a sistema de missatgeria lleugera mitjançant el mecanisme de **Publicació/Subscripció**, permetent:
    - Enviar en temps real cada fragment transcrit pels workers.
    - Notificar el servidor web perquè actualitzi la UI sense necessitat de refrescar la pàgina ni esperar la transcripció completa.
5. **Worker de transcripció**  
    Procés independent que actua de la següent manera:
    - Consulta la cua de MongoDB per obtenir els fitxers pendents.
    - Accedeix als fitxers d'àudio o vídeo emmagatzemats a MinIO.
    - Aplica el pipeline de transcripció basat en VAD i _Faster-Whisper_.
    - Envia cada fragment de text a Redis a mesura que es transcriu, mantenint el sistema reactiu i escalable.
    - Desa els resultats finals a MongoDB un cop completada la transcripció.
6. **MinIO (Emmagatzematge)**  
    S’utilitza com a sistema d’emmagatzematge d’arxius multimèdia:
       - Permet accedir fàcilment als fitxers des dels workers gràcies a la seva compatibilitat amb l’API S3.
       - Redueix la dependència de sistemes de fitxers locals i afavoreix l’escalabilitat del sistema.
#### Flux general del sistema
1. L’usuari puja un vídeo o àudio des de la UI.
2. El fitxer es desa a MinIO i es registra a MongoDB.
3. Es crea una entrada a la cua de processament.
4. El worker detecta el nou treball i comença la transcripció.
5. A cada fragment processat, el worker envia un missatge a Redis.
6. El servidor web rep el missatge i l’envia a la UI.
7. La UI mostra els subtítols en temps real, sincronitzats amb el reproductor.
8. En finalitzar, els subtítols complets queden disponibles per a descàrrega o reutilització.

Aquest enfocament modular i asincrònic facilita tant l’**escalabilitat** com la **resposta en temps real**, essencials en sistemes moderns d’anàlisi i transcripció multimèdia.

