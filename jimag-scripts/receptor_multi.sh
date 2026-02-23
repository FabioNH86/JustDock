#!/bin/bash

# 1. Definir rutas sin hardcoding
[ -z "$HOMEDIR" ] && HOMEDIR="$HOME"
ADFRBIN="$HOMEDIR/.local/src/adfr/ADFRsuite-1.0/bin"

# 2. Configurar el entorno para que encuentre sus librerías internas
export PATH="$ADFRBIN:$PATH"
export LD_LIBRARY_PATH="$HOMEDIR/.local/src/adfr/ADFRsuite-1.0/lib:$LD_LIBRARY_PATH"

echo -e "\e[1m\e[36m>>\e[39m preparing receptor...\033[0m"

# 3. LIMPIEZA CRUCIAL: Usamos obabel para eliminar duplicados y errores geométricos
# Esto evita el ZeroDivisionError al normalizar la estructura.
obabel "$WD/receptor.pdb" -O "$WD/receptor_clean.pdb"

# 4. Procesar con reduce (usando el archivo limpio)
# Nota: Usamos '>' para sobrescribir y evitar que se acumulen H si reintenta
"$ADFRBIN/reduce" "$WD/receptor_clean.pdb" > "$WD/receptorH.pdb"

# 5. Generar el PDBQT final
if [ -f "$ADFRBIN/prepare_receptor" ]; then
    "$ADFRBIN/prepare_receptor" -r "$WD/receptorH.pdb" -o "$WD/receptor.pdbqt"
else
    echo "ERROR: No se encontró prepare_receptor en $ADFRBIN"
    exit 1
fi

# Respuesta al TODO:
# No es estrictamente necesario borrar el .pyc, pero no hace daño. 
# Lo que sí es útil es limpiar los archivos temporales de limpieza.
rm -f "$WD/receptor_clean.pdb"