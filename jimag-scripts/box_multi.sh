#!/bin/bash

# Evitar que errores silenciosos rompan el script
set -e

echo -e "\e[1m\e[36m>>\e[39m calculando gridbox para pocket $CURRENT_POCKET...\033[0m"

# 1. Definir la ruta del archivo de predicciones de P2Rank
# P2Rank suele generar: receptor.pdb_predictions.csv
CSV_FILE="$WD/receptor.pdb_predictions.csv"

if [ ! -f "$CSV_FILE" ]; then
    echo "ERROR: No se encontró el archivo de predicciones $CSV_FILE"
    exit 1
fi

# 2. Extraer coordenadas usando AWK
# Explicación del comando:
# -v rank: pasamos el número de pocket (1, 2, 3...)
# FS = ",": usamos coma como separador
# NR == (rank + 1): saltamos la cabecera del CSV
# $3, $4, $5: son las columnas de center_x, center_y, center_z en P2Rank
# $6: es el pocket_radius (lo usamos para definir el tamaño de la caja)

read -r CENTER_X CENTER_Y CENTER_Z RADIUS <<EOF
$(awk -v rank="$CURRENT_POCKET" 'BEGIN { FS = "," } NR == (rank + 1) { print $3, $4, $5, $6 }' "$CSV_FILE")
EOF

# 3. Validar que obtuvimos datos
if [ -z "$CENTER_X" ]; then
    echo "ERROR: No se pudo extraer coordenadas para el pocket $CURRENT_POCKET"
    exit 1
fi

# 4. Calcular el tamaño de la caja (Size)
# Vina funciona mejor si la caja es un poco más grande que el radio del pocket.
# Multiplicamos el radio por 2.5 o usamos un mínimo de 20.0
SIZE=$(awk -v r="$RADIUS" 'BEGIN { s = r * 2.5; if (s < 20) s = 20; printf "%.1f", s }')

# 5. Generar el archivo box.txt con el formato exacto para Vina
# Usamos 'tee' para que lo veas en el log y se guarde en el archivo
cat <<EOF | tee "$CURRENT_POCKET_DIR/box.txt"
center_x = $CENTER_X
center_y = $CENTER_Y
center_z = $CENTER_Z
size_x = $SIZE
size_y = $SIZE
size_z = $SIZE
EOF

echo -e "\e[1m\e[32mOK:\e[39m Gridbox guardada en $CURRENT_POCKET_DIR/box.txt\033[0m"