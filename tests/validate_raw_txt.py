import os

def cargar_texto(fichero):
    """Función para cargar el contenido de un archivo y procesarlo."""
    with open(fichero, 'r', encoding='utf-8') as file:
        texto = file.read().strip().lower()  # Elimina saltos de línea y pone a minúsculas

    # Eliminamos comas y puntos
    texto = texto.translate(str.maketrans('', '', ',.\'\`\''))
    
    return texto

def calcular_precision(texto_referencia, texto_comparar):
    """Función para calcular la precisión entre el texto de referencia y otro texto."""
    # Convertimos ambos textos en listas de palabras
    palabras_referencia = set(texto_referencia.split())
    palabras_comparar = set(texto_comparar.split())
    
    # Calculamos las palabras coincidentes
    palabras_comunes = palabras_referencia.intersection(palabras_comparar)
    
    # Calculamos la precisión (número de coincidencias / total de palabras en el texto de referencia)
    if len(palabras_referencia) == 0:
        return 0.0  # Evitar división por cero si el texto de referencia está vacío
    precision = len(palabras_comunes) / len(palabras_referencia)
    
    # Palabras en la referencia que no están en el texto de prueba
    palabras_no_encontradas = palabras_referencia - palabras_comparar
    
    return precision, len(palabras_referencia), len(palabras_comparar), len(palabras_comunes), palabras_no_encontradas

def procesar_ficheros(lista_ficheros, fichero_referencia):
    """Función para procesar una lista de ficheros y calcular la precisión de cada uno."""
    # Cargamos el texto de referencia desde el archivo
    texto_referencia = cargar_texto(fichero_referencia)
    
    # Información sobre el texto de referencia
    palabras_referencia = texto_referencia.split()
    num_palabras_referencia = len(palabras_referencia)
    
    resultados = []
    
    print(f"Texto de referencia cargado: {fichero_referencia}")
    print(f"Total de palabras en el archivo de referencia: {num_palabras_referencia}")
    print("-" * 50)

    for fichero in lista_ficheros:
        if os.path.exists(fichero):
            texto_comparar = cargar_texto(fichero)
            precision, num_palabras_referencia, num_palabras_comparar, num_palabras_comunes, palabras_no_encontradas = calcular_precision(texto_referencia, texto_comparar)
            
            resultados.append((fichero, precision, num_palabras_comparar, num_palabras_comunes, palabras_no_encontradas))
            
            print(f"\nProcesando el archivo: {fichero}")
            print(f"  Total de palabras en el archivo de prueba: {num_palabras_comparar}")
            print(f"  Palabras coincidentes con el texto de referencia: {num_palabras_comunes}")
            print(f"  Precisión: {precision * 100:.2f}%")
            print(f"  Palabras en la referencia que no están en el archivo de prueba: {', '.join(palabras_no_encontradas)}")
            print("-" * 50)
        else:
            print(f"El archivo {fichero} no existe.")
    
    return resultados

# Lista de ficheros a procesar
ficheros = ['../vosk/output/harry_potter_first_5_min.txt', 
            '../whisper-v3-turbo/output/harry_potter_first_5_min.txt']

# Archivo de referencia
fichero_referencia = '../references/harry_potter_first_pages.txt'

# Procesamos los ficheros
resultados = procesar_ficheros(ficheros, fichero_referencia)

# Imprimimos los resultados finales
print("\nResultados finales:")
for fichero, precision, num_palabras_comparar, num_palabras_comunes, palabras_no_encontradas in resultados:
    print(f"Precisión del archivo {fichero}: {precision * 100:.2f}%")
    print(f"  Palabras en el archivo de prueba: {num_palabras_comparar}")
    print(f"  Palabras coincidentes: {num_palabras_comunes}")
    print(f"  Palabras en la referencia que no están en el archivo de prueba: {', '.join(palabras_no_encontradas)}")
    print("-" * 50)
