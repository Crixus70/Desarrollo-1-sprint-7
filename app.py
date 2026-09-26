from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ruta al archivo CSV con los movimientos de inventario
DATA_PATH = Path(__file__).resolve().parent / \
    "aguacate_hass_agosto_septiembre_ejercicio.csv"
REQUIRED_COLUMNS = {
    "fecha",
    "id_movimiento",
    "tipo_movimiento",
    "destino",
    "entradas_kg",
    "salidas_kg",
    "mermas_kg",
    "existencia_inicial_cd_kg",
    "existencia_actual_cd_kg",
}
CITY_ORDER = ["Ciudad de Mexico", "Guadalajara", "Monterrey"]

# Configuración de la página de Streamlit y carga de datos
st.set_page_config(
    page_title="Ruta Hass | Control logístico",
    layout="wide",
)

# Función para cargar los movimientos desde el CSV con validaciones y caché de Streamlit


@st.cache_data(show_spinner="Cargando movimientos...")
def load_movements(file_path: str) -> pd.DataFrame:
    movements = pd.read_csv(file_path)
    missing_columns = REQUIRED_COLUMNS.difference(movements.columns)
    if missing_columns:
        raise ValueError(
            "Faltan columnas requeridas en el CSV: "
            + ", ".join(sorted(missing_columns))
        )
# Validación de fechas y conversión a tipo datetime
    movements["fecha"] = pd.to_datetime(
        movements["fecha"], format="%d/%m/%Y", errors="coerce"
    )
    if movements["fecha"].isna().any():
        raise ValueError(
            "Hay fechas vacías o con formato distinto a DD/MM/AAAA.")
# Ordenar los movimientos por fecha e ID antes de devolverlos
    return movements.sort_values(["fecha", "id_movimiento"]).reset_index(drop=True)


# Título y descripción del panel de Streamlit
st.title("Ruta Hass | Centro de distribución Puebla")
st.caption(
    "Veracruz → Puebla → Ciudad de México · Guadalajara · Monterrey"
    "  |  Panel de logística e inventario · Escenario didáctico"
)
# Comprobación de existencia del archivo CSV
if not DATA_PATH.exists():
    st.error(f"No se encontró el conjunto de datos: {DATA_PATH.name}")
    st.stop()
# Cargar los movimientos desde el CSV y manejar errores de lectura
try:
    df = load_movements(str(DATA_PATH))
except (OSError, ValueError, pd.errors.ParserError) as error:
    st.error(f"No fue posible cargar el conjunto de datos. {error}")
    st.stop()
# Validación de conciliación de existencias y unicidad de IDs
expected_stock = (
    df["existencia_inicial_cd_kg"]
    + df["entradas_kg"]
    - df["salidas_kg"]
    - df["mermas_kg"]
)
if not df["id_movimiento"].is_unique or not expected_stock.eq(
    df["existencia_actual_cd_kg"]
).all():
    st.error(
        "El libro de movimientos no concilia. Revisa IDs y saldos antes de usar el panel.")
    st.stop()

# Filtro de periodo de análisis en la barra lateral
with st.sidebar:
    st.header("Periodo de análisis")
    date_range = st.date_input(
        "Selecciona fecha inicial y final",
        value=(df["fecha"].min().date(), df["fecha"].max().date()),
        min_value=df["fecha"].min().date(),
        max_value=df["fecha"].max().date(),
        format="DD/MM/YYYY",
    )
    st.caption("El conjunto considera operación de lunes a sábado.")
#
if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.info("Selecciona una fecha inicial y una fecha final para consultar el periodo.")
    st.stop()

start_date, end_date = map(pd.Timestamp, date_range)
period_df = df[df["fecha"].between(start_date, end_date)].copy()
if period_df.empty:
    st.info("No hay movimientos en las fechas seleccionadas.")
    st.stop()
# Filtro de destinos en la barra lateral
with st.sidebar:
    st.header("Destinos")
    selected_destinations = st.multiselect(
        "Filtrar despachos por ciudad",
        options=CITY_ORDER,
        default=CITY_ORDER,
    )
    st.caption(
        "El filtro cambia la comparación por ciudad; el balance conserva todos los destinos.")

# Cálculo de métricas de inventario para el periodo seleccionado
opening_stock = int(period_df.iloc[0]["existencia_inicial_cd_kg"])
closing_stock = int(period_df.iloc[-1]["existencia_actual_cd_kg"])
inbound_kg = int(period_df["entradas_kg"].sum())
outbound_kg = int(period_df["salidas_kg"].sum())
waste_kg = int(period_df["mermas_kg"].sum())

# Presentación de métricas de inventario en el panel
st.subheader("Resumen del periodo")
metric_columns = st.columns(4)
metric_columns[0].metric("Existencia al cierre", f"{closing_stock:,} kg")
metric_columns[1].metric("Entradas", f"{inbound_kg:,} kg")
metric_columns[2].metric("Salidas", f"{outbound_kg:,} kg")
metric_columns[3].metric("Mermas", f"{waste_kg:,} kg")

# Verificación de conciliación del balance del periodo
if opening_stock + inbound_kg - outbound_kg - waste_kg != closing_stock:
    st.error(
        "El balance del periodo no concilia; revisa los movimientos antes de decidir.")
    st.stop()
#   Flujo de inventario desde la existencia inicial hasta los destinos y la existencia final
st.subheader("Flujo de inventario")
destination_totals = (
    period_df.loc[period_df["tipo_movimiento"] == "Salida"]
    .groupby("destino")["salidas_kg"]
    .sum()
    .reindex(CITY_ORDER, fill_value=0)
)
flow_labels = [
    "Existencia inicial",
    "Recepciones desde Veracruz",
    "Centro de distribución · Puebla",
    "Ciudad de México",
    "Guadalajara",
    "Monterrey",
    "Mermas registradas",
    "Existencia final",
]
flow_values = [
    opening_stock,
    inbound_kg,
    int(destination_totals["Ciudad de Mexico"]),
    int(destination_totals["Guadalajara"]),
    int(destination_totals["Monterrey"]),
    waste_kg,
    closing_stock,
]
flow_figure = go.Figure(
    go.Sankey(
        arrangement="snap",
        node={
            "pad": 20,
            "thickness": 18,
            "line": {"color": "white", "width": 1},
            "label": flow_labels,
            "color": [
                "#79a88b",
                "#2a9d8f",
                "#457b9d",
                "#e9a23b",
                "#df7b43",
                "#c85c5c",
                "#9b6a68",
                "#6a9c78",
            ],
        },
        link={
            "source": [0, 1, 2, 2, 2, 2, 2],
            "target": [2, 2, 3, 4, 5, 6, 7],
            "value": flow_values,
        },
    )
)
flow_figure.update_layout(
    title="Del inventario inicial a los destinos y al cierre",
    height=470,
    font={"size": 13},
    margin={"l": 8, "r": 8, "t": 55, "b": 8},
)
st.plotly_chart(flow_figure, width="stretch")

left_column, right_column = st.columns([1.3, 1])
with left_column:
    daily_stock = (
        period_df.groupby("fecha", as_index=False)
        .tail(1)[["fecha", "existencia_actual_cd_kg"]]
        .sort_values("fecha")
    )
    stock_figure = px.line(
        daily_stock,
        x="fecha",
        y="existencia_actual_cd_kg",
        markers=True,
        title="Existencia diaria al cierre en Puebla",
        labels={"fecha": "Fecha",
                "existencia_actual_cd_kg": "Existencia (kg)"},
    )
    st.plotly_chart(stock_figure, width="stretch")

with right_column:
    dispatches = period_df.loc[
        (period_df["tipo_movimiento"] == "Salida")
        & period_df["destino"].isin(selected_destinations)
    ]
    by_destination = (
        dispatches.groupby("destino", as_index=False)["salidas_kg"]
        .sum()
        .sort_values("salidas_kg", ascending=True)
    )
    if by_destination.empty:
        st.info("No hay salidas para los destinos seleccionados en este periodo.")
    else:
        destination_figure = px.bar(
            by_destination,
            x="salidas_kg",
            y="destino",
            orientation="h",
            text_auto=".2s",
            title="Despachos por destino",
            labels={"destino": "Destino", "salidas_kg": "Kilogramos"},
        )
        st.plotly_chart(destination_figure, width="stretch")

# Desafío opcional: cada casilla controla la visibilidad de su gráfica.
st.subheader("Exploración interactiva")
st.write(
    "Selecciona una o ambas casillas para explorar los despachos y el flujo diario."
)

# El histograma usa cantidades de salida y respeta el periodo y los destinos seleccionados.
dispatch_data = period_df.loc[
    (period_df["tipo_movimiento"] == "Salida")
    & period_df["destino"].isin(selected_destinations),
    "salidas_kg",
]
histogram_column, scatter_column = st.columns(2)

with histogram_column:
    # Evita ofrecer una gráfica vacía si no hay despachos en la selección.
    hist_checkbox = st.checkbox(
        "Construir histograma",
        disabled=dispatch_data.empty,
        key="show_dispatch_histogram",
    )
    if hist_checkbox:
        st.write("Distribución de kilogramos por despacho seleccionado.")
        histogram = go.Figure(
            data=[go.Histogram(x=dispatch_data, nbinsx=12, name="Despachos")]
        )
        histogram.update_layout(
            title_text="Distribución del volumen por despacho",
            xaxis_title="Kilogramos por despacho",
            yaxis_title="Número de despachos",
        )
        st.plotly_chart(histogram, width="stretch")

with scatter_column:
    # La dispersión compara por día las entradas y todas las salidas del centro.
    scatter_checkbox = st.checkbox(
        "Construir gráfico de dispersión",
        key="show_inbound_outbound_scatter",
    )
    if scatter_checkbox:
        st.write("Cada punto representa un día de operación.")
        # Se conservan todos los destinos para comparar el flujo total del centro.
        daily_flow = period_df.groupby("fecha", as_index=False)[
            ["entradas_kg", "salidas_kg"]
        ].sum()
        scatter = go.Figure(
            data=[
                go.Scatter(
                    x=daily_flow["entradas_kg"],
                    y=daily_flow["salidas_kg"],
                    mode="markers",
                    text=daily_flow["fecha"].dt.strftime("%d/%m/%Y"),
                    hovertemplate=(
                        "Fecha: %{text}<br>"
                        "Entradas: %{x:,} kg<br>"
                        "Salidas: %{y:,} kg<extra></extra>"
                    ),
                )
            ]
        )
        axis_max = max(
            daily_flow["entradas_kg"].max(),
            daily_flow["salidas_kg"].max(),
        )
        scatter.add_shape(
            type="line",
            x0=0,
            y0=0,
            x1=axis_max,
            y1=axis_max,
            line={"color": "gray", "dash": "dash"},
        )
        scatter.update_layout(
            title_text="Entradas y salidas diarias",
            xaxis_title="Entradas (kg)",
            yaxis_title="Salidas (kg)",
        )
        st.plotly_chart(scatter, width="stretch")

with st.expander("Consultar movimientos del periodo"):
    visible_columns = [
        "fecha",
        "id_movimiento",
        "tipo_movimiento",
        "destino",
        "entradas_kg",
        "salidas_kg",
        "mermas_kg",
        "existencia_actual_cd_kg",
    ]
    st.dataframe(
        period_df[visible_columns],
        hide_index=True,
        width="stretch",
        column_config={"fecha": st.column_config.DateColumn(
            "Fecha", format="DD/MM/YYYY")},
    )
    st.download_button(
        "Descargar movimientos del periodo",
        data=period_df[visible_columns].to_csv(
            index=False).encode("utf-8-sig"),
        file_name="movimientos_aguacate_hass.csv",
        mime="text/csv",
    )
# Pie de página con información didáctica
st.caption(
    "Datos didácticos para análisis de logística y cadena de suministro. "
    "Las temperaturas son ilustrativas, no mediciones verificadas."
)
