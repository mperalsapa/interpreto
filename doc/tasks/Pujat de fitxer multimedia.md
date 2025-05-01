Per emmagatzemar el fitxer, tindrem un servidor de fitxers (en aquest cas, será MinIO). Pujarem el fitxer des-del frontend a un servidor web, i aquest es communicarà amb el servidor de fitxers i la base de dades.

La base de dades, en aquest punt, porta la funcionalitat de cua i control de duplicats. Inicialment, qualsevol fitxer que pujem, comprovarem si ja existeix al sistema. En cas d'existir, indicarem a l'usuari que ja tenim el fitxer, i en quin estat de la cua es troba.
