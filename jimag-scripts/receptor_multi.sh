#!/bin/bash

# 1. Definir rutas robustas
# Usamos la ruta donde instalamos ADFR en el Dockerfile
ADFRBIN="/opt/ADFRsuite/bin"
ADFRLIB="/opt/ADFRsuite/lib"

echo -e "\e[1m\e[36m>>\e[39m preparing receptor...\033[0m"

# 2. Limpieza inicial con obabel del sistema
/usr/bin/obabel "$WD/receptor.pdb" -O "$WD/receptor_clean.pdb"

# 3. Procesar con reduce (aislando el entorno)
# El log mostró que reduce funciona, pero por seguridad aislamos:
(
    unset LD_LIBRARY_PATH
    LD_LIBRARY_PATH="$ADFRLIB" "$ADFRBIN/reduce" "$WD/receptor_clean.pdb" > "$WD/receptorH.pdb"
)

# 4. Generar el PDBQT final
if [ -f "$ADFRBIN/prepare_receptor" ]; then
    echo "DEBUG: Ejecutando prepare_receptor..."
    (
        # ESTA ES LA CLAVE:
        unset LD_LIBRARY_PATH
        export PATH="$ADFRBIN:$PATH"
        # Forzamos que use las librerías de /opt/ y no las de /root/
        LD_LIBRARY_PATH="$ADFRLIB" "$ADFRBIN/prepare_receptor" \
            -r "$WD/receptorH.pdb" \
            -o "$WD/receptor.pdbqt" \
            -A checkhydrogens \
            -e
    )
else
    echo "ERROR: No se encontró prepare_receptor en $ADFRBIN"
    exit 1
fi

# Limpieza de archivos temporales
rm -f "$WD/receptor_clean.pdb" "$WD/receptorH.pdb"