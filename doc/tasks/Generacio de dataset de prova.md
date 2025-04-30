Per fer proves més sòlides, en comptes de fer servir només un àudio de 5 minuts del àudio llibre de Harry Potter: La pedra filosofal, farem servir una llista de pel·lícules de l'últim any (2024) per posar a prova la capacitat de transcripció.

# Font de la llista original
La llista original es la meva biblioteca de pel·lícules personal. Faré un llistat ordenat de les pel·lícules mes recents (de l'any 2024) i faré una selecció variada.

```bash
# Llistat ordenat per any de publicació limitat a 50 resultats
# nom dels fitxers en disc: movie_(2000)_[tmdbid-xxxx]_lang.mp4
ls -1 | sed 's/.*(\([0-9]\{4\}\)).*/\1 &/' | sort -n | sed 's/^[0-9]\{4\} //' | tail -n50
```

- Kung Fu Panda 4 (2024)
- Gru 4. Mi villano favorito (2024)
- La vida secreta de los orangutanes (2024)
- No hables con extraños (2024)
- Rebel Moon (Parte dos) La guerrera que deja marcas (2024)
- Sonic 3 La película (2024)
- Furiosa De la saga Mad Max (2024)
- Dune Parte dos (2024)

# Generació dels fitxers d'audio
Per generar els fitxers d'àudio, farem servir un fitxer de text amb la llista de pel·lícules, i executarem una comanda de FFmpeg per generar els 5 minuts d'àudio en format MP3. Agafarem del minut 20 al 25, així ja hauria començat la pel·lícula i podrem tenir diàlegs.
```powershell
%% Llegim el fitxer de pelicules. I per cada linia (pel·lícula) executem la comanda de ffmpeg amb el contingut de la linia (el nom del fitxer) %%
Get-Content "peliculas.txt" | ForEach-Object {ffmpeg -i $_ -ss 00:20:00 -t 00:05:00 -vn -acodec mp3 -ar 44100 -ac 2 ("audio_dataset\" + [System.IO.Path]::GetFileNameWithoutExtension($_) + ".mp3")}
```

# Resultat
```powershell
Get-ChildItem | Select-Object -ExpandProperty Name
Deadpool_y_Lobezno_(2024)_[tmdbid-533535]_Cast.mp3
Dune_Parte_dos_(2024)_[tmdbid-693134]_Cast.mp3
Furiosa_De_la_saga_Mad_Max_(2024)_[tmdbid-786892]_Cast.mp3
Godzilla_y_Kong_El_nuevo_imperio_(2024)_[tmdbid-823464]_Cast.mp3
Gru_4._Mi_villano_favorito_(2024)_[tmdbid-519182]_Cast.mp3
Kung_Fu_Panda_4_(2024)_[tmdbid-1011985]_Cast.mp3
La_vida_secreta_de_los_orangutanes_(2024)_[tmdbid-1239121]_Cast.mp3
Rebel_Moon_(Parte_dos)_La_guerrera_que_deja_marcas_(2024)_[tmdbid-934632]_Cast.mp3
Transformers_One_(2024)_[tmdbid-698687]_Cast.mp3
```
