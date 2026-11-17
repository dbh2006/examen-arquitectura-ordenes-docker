
#!/bin/sh
set -eu

SQLCMD=/opt/mssql-tools18/bin/sqlcmd

echo "Esperando a SQL Server..."

until "$SQLCMD" \
  -S db -U sa \
  -P "$MSSQL_SA_PASSWORD" \
  -C -Q "SELECT 1" -b -o /dev/null
do
  sleep 5
done

echo "SQL Server disponible."

EXISTE=$("$SQLCMD" \
  -S db -U sa \
  -P "$MSSQL_SA_PASSWORD" \
  -C -h -1 -W \
  -Q "SET NOCOUNT ON; SELECT DB_ID('OrdenesDB')" \
  | tr -d '\r[:space:]')

if [ "$EXISTE" = "NULL" ]; then
  echo "Creando base de datos y datos iniciales..."

  "$SQLCMD" \
    -S db -U sa \
    -P "$MSSQL_SA_PASSWORD" \
    -C -b -i /scripts/init.sql

  echo "Inicializacion completada."
else
  echo "OrdenesDB ya existe. Se conservan los datos."
fi
