# Ruta Hass | Panel de logística e inventario

Aplicación web didáctica para explorar los movimientos de aguacate Hass de una startup con centro de distribución en Puebla. El escenario representa recepciones desde Veracruz y despachos a Ciudad de México, Guadalajara y Monterrey.

## Propósito

Reunir entradas, salidas, mermas y existencias en un panel que facilite revisar el flujo de inventario y comparar despachos por periodo y destino. Es un ejercicio de logística y cadena de suministro, no un sistema operativo de inventarios ni una evaluación de inocuidad.

## Funcionalidades

- Filtros por periodo y ciudad de destino.
- Indicadores de entradas, salidas, mermas y existencia al cierre.
- Gráfica Sankey del flujo desde la existencia inicial y las recepciones hasta los destinos, mermas y saldo final.
- Tendencia diaria de existencias y comparación de despachos por destino.
- Casillas opcionales para mostrar un histograma de tamaños de despacho y un dispersograma de entradas frente a salidas diarias.
- Tabla de movimientos filtrados con opción para descargarla como CSV.
- Validación de columnas, fechas, identificadores únicos y conciliación de cada movimiento antes de presentar los resultados.

## Datos

El archivo `aguacate_hass_agosto_septiembre_ejercicio.csv` contiene un escenario didáctico de 245 movimientos entre agosto y septiembre de 2026. Las temperaturas son ilustrativas, no registros verificados de AccuWeather ni mediciones del producto. No utilizar estos datos para tomar decisiones sobre una operación real.

## Instalación y ejecución

Desde la raíz del repositorio, instala las dependencias y ejecuta Streamlit:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

La aplicación local se abrirá en `http://localhost:8501`.
