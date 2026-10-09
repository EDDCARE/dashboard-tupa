import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# =============================================================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS
# =============================================================================
st.set_page_config(page_title="Dashboard Evolución por Competencias", layout="wide", page_icon="📊")

st.markdown("""
<style>
    /* Limpiar fondo de los botones de radio del filtro de trimestre */
    div[data-testid="stRadio"] label {
        background-color: transparent !important;
        padding: 5px 10px;
        border-radius: 5px;
    }
    div[data-testid="stRadio"] label:hover {
        background-color: #f0f2f6 !important;
    }
    /* Ajuste de métricas */
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DICCIONARIOS Y CONSTANTES
# =============================================================================
DICCIONARIO_AREAS = {
    '0001-ART Y CULT': 'Arte y Cultura',
    '0004-CIENC TEC': 'Ciencia y Tecnología',
    '0006-DESEN TIC': 'DESEN TIC',
    '0007-GEST AUTO': 'GEST AUTO',
    '0010-DESARR PCC': 'Desarrollo Personal y Ciudadano',
    '014-CCSS': 'Ciencias Sociales',
    '031-EFIS': 'Educación Física',
    '032-ETRA': 'Educación para el Trabajo',
    '035-EREL': 'Educación Religiosa',
    '057-INGL': 'Inglés',
    '063-MATE': 'Matemática',
    '017-COMU': 'Comunicación',
    'M797-QUEM797': 'Quechua',
}

COLORES_NIVELES = {'C': '#d32f2f', 'B': '#fbc02d', 'A': '#388e3c', 'AD': '#1565c0', '0': '#9e9e9e'}
ORDEN_NIVELES = ['C', 'B', 'A', 'AD']
NOMBRES_NIVELES = {'C': 'Inicio (C)', 'B': 'Proceso (B)', 'A': 'Logro Previsto (A)', 'AD': 'Logro Destacado (AD)', '0': 'Sin calificar (0)'}

# =============================================================================
# CARGA Y LIMPIEZA DE DATOS
# =============================================================================
@st.cache_data
def cargar_datos():
    df = pd.read_excel('test2Tupa.xlsx')
    cols_privadas = ['Nombres', 'Cód. Estudiante']
    df = df.drop(columns=[c for c in cols_privadas if c in df.columns], errors='ignore')
    df = df.drop(columns=[c for c in df.columns if str(c).startswith('Columna')], errors='ignore')
    df = df.dropna(subset=['Grado', 'Sección', 'Área', 'Trimestre', 'Nombre Competencia', 'Nivel de Logro'])
    
    def extraer_nivel(texto):
        texto = str(texto)
        if '(AD)' in texto: return 'AD'
        if '(A)' in texto: return 'A'
        if '(B)' in texto: return 'B'
        if '(C)' in texto: return 'C'
        return '0'
        
    df['Nivel_Corto'] = df['Nivel de Logro'].apply(extraer_nivel)
    df['Area_Limpia'] = df['Área'].map(DICCIONARIO_AREAS)
    df = df.dropna(subset=['Area_Limpia'])
    return df

df_original = cargar_datos()

# =============================================================================
# SIDEBAR: FILTROS EN CASCADA
# =============================================================================
st.sidebar.title("📌 Filtros de Navegación")
grados = ['Todos'] + sorted(df_original['Grado'].unique().tolist())
grado_sel = st.sidebar.selectbox("1. Grado", grados)

df_grado = df_original if grado_sel == 'Todos' else df_original[df_original['Grado'] == grado_sel]

secciones = ['Todas'] + sorted(df_grado['Sección'].unique().tolist())
seccion_sel = st.sidebar.selectbox("2. Sección", secciones)

df_seccion = df_grado if seccion_sel == 'Todas' else df_grado[df_grado['Sección'] == seccion_sel]

areas = ['Todas'] + sorted(df_seccion['Area_Limpia'].unique().tolist())
area_sel = st.sidebar.selectbox("3. Área Curricular", areas)

df_area = df_seccion if area_sel == 'Todas' else df_seccion[df_seccion['Area_Limpia'] == area_sel]

competencias = sorted(df_area['Nombre Competencia'].unique().tolist())
comp_sel = st.sidebar.multiselect("4. Competencias", competencias, default=competencias)

trimestre_sel = st.sidebar.radio("5. Trimestre a visualizar", ['Ambos (T1 vs T2)', 'Solo T1', 'Solo T2'], horizontal=True)

# =============================================================================
# APLICAR FILTROS Y ENCABEZADO
# =============================================================================
df_filtrado = df_area[df_area['Nombre Competencia'].isin(comp_sel)].copy()
if trimestre_sel == 'Solo T1': df_filtrado = df_filtrado[df_filtrado['Trimestre'] == 'T1']
elif trimestre_sel == 'Solo T2': df_filtrado = df_filtrado[df_filtrado['Trimestre'] == 'T2']

st.title("📊 Evolución del Aprendizaje por Competencias")
st.markdown(f"**Grado:** `{grado_sel}` | **Sección:** `{seccion_sel}` | **Área:** `{area_sel}`")
st.divider()

if df_filtrado.empty:
    st.warning("⚠️ No hay datos disponibles para la combinación de filtros seleccionada.")
    st.stop()

# =============================================================================
# KPIs (Estudiantes únicos y niveles separados)
# =============================================================================
total_estudiantes = df_filtrado['ID'].nunique() if 'ID' in df_filtrado.columns else len(df_filtrado)
df_calificados = df_filtrado[df_filtrado['Nivel_Corto'] != '0']
df_sin_calificar = df_filtrado[df_filtrado['Nivel_Corto'] == '0']
total_calificados = len(df_calificados)

pct_c = (df_calificados['Nivel_Corto'] == 'C').sum() / total_calificados * 100 if total_calificados > 0 else 0
pct_b = (df_calificados['Nivel_Corto'] == 'B').sum() / total_calificados * 100 if total_calificados > 0 else 0
pct_a = (df_calificados['Nivel_Corto'] == 'A').sum() / total_calificados * 100 if total_calificados > 0 else 0
pct_ad = (df_calificados['Nivel_Corto'] == 'AD').sum() / total_calificados * 100 if total_calificados > 0 else 0
pct_sin_cal = len(df_sin_calificar) / len(df_filtrado) * 100 if len(df_filtrado) > 0 else 0

col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1: st.metric("📝 Total Estudiantes", total_estudiantes)
with col2: st.metric("🔴 Inicio (C)", f"{pct_c:.1f}%")
with col3: st.metric("🟡 Proceso (B)", f"{pct_b:.1f}%")
with col4: st.metric("🟢 Previsto (A)", f"{pct_a:.1f}%")
with col5: st.metric("🔵 Destacado (AD)", f"{pct_ad:.1f}%")
with col6: st.metric("⚪ Sin calificar", f"{pct_sin_cal:.1f}%")

st.divider()

# =============================================================================
# GRÁFICO 1: BARRAS APILADAS (Condicional y Mejorado)
# =============================================================================
st.subheader("📊 1. Distribución de Niveles por Competencia")

if trimestre_sel == 'Ambos (T1 vs T2)':
    st.info("💡 Para ver la distribución detallada de niveles, selecciona **'Solo T1'** o **'Solo T2'** en el filtro de la izquierda. Para comparar la evolución entre ambos, usa el Mapa de Calor más abajo.")
else:
    st.markdown("*Cada barra representa el 100% de estudiantes evaluados en este trimestre.*")

    def formatear_nombre(nombre, max_chars=40):
        if len(nombre) <= max_chars: return nombre
        palabras = nombre.split()
        lineas = []
        linea_actual = ""
        for palabra in palabras:
            if len(linea_actual) + len(palabra) + 1 <= 25:
                linea_actual = linea_actual + " " + palabra if linea_actual else palabra
            else:
                if linea_actual: lineas.append(linea_actual)
                linea_actual = palabra
        if linea_actual: lineas.append(linea_actual)
        if len(lineas) > 3: lineas = lineas[:2] + [lineas[2][:20] + "..."]
        return "<br>".join(lineas)

    df_barras = df_calificados.groupby(['Nombre Competencia', 'Trimestre', 'Nivel_Corto']).size().reset_index(name='Cantidad')
    total_por_grupo = df_barras.groupby(['Nombre Competencia', 'Trimestre'])['Cantidad'].transform('sum')
    df_barras['Porcentaje'] = (df_barras['Cantidad'] / total_por_grupo * 100).round(2)
    df_barras['Nombre_Corto'] = df_barras['Nombre Competencia'].apply(formatear_nombre)

    fig_barras = go.Figure()

    for nivel in ORDEN_NIVELES:
        df_nivel = df_barras[df_barras['Nivel_Corto'] == nivel]
        custom_data = [[row['Nombre Competencia'], row['Trimestre'], row['Cantidad'], row['Porcentaje']] for _, row in df_nivel.iterrows()]
        color_texto = 'black' if nivel in ['B', 'C'] else 'white'

        fig_barras.add_trace(go.Bar(
            name=f"Estudiantes en {NOMBRES_NIVELES[nivel]}",
            x=df_nivel['Nombre_Corto'],
            y=df_nivel['Porcentaje'],
            marker_color=COLORES_NIVELES[nivel],
            marker_line=dict(color='black', width=1.2),
            text=df_nivel['Porcentaje'].apply(lambda x: f"{x:.2f} %".replace('.', ',') if x > 0 else ""),
            textposition='inside',
            textfont=dict(color=color_texto, size=11, family='Arial Black'),
            hovertemplate=(
                "<b>%{fullData.name}</b><br>"
                "━━━━━━━━━━━━━━━━━━━━<br>"
                "<b>Competencia:</b> %{customdata[0]}<br>"
                "<b>Trimestre:</b> %{customdata[1]}<br>"
                "━━━━━━━━━━━━━━━━━━━━<br>"
                "<b>Cantidad:</b> %{customdata[2]} estudiantes<br>"
                "<b>Porcentaje:</b> %{customdata[3]:.2f}%<br>"
                "<extra></extra>"
            ),
            customdata=custom_data
        ))

    fig_barras.update_layout(
        barmode='stack', xaxis_title='', yaxis_title='',
        yaxis=dict(range=[0, 100], dtick=10, ticksuffix="%", showgrid=True, gridcolor='#666666', gridwidth=0.8, zeroline=True, zerolinecolor='black', zerolinewidth=1.5),
        xaxis=dict(showgrid=True, gridcolor='#666666', gridwidth=0.8, tickangle=0, tickfont=dict(size=11, color='black', family='Arial Black')),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5, font=dict(size=11, color='black')),
        height=520, margin=dict(l=60, r=40, t=60, b=120), plot_bgcolor='white', paper_bgcolor='white', font=dict(color='black')
    )
    fig_barras.update_xaxes(showline=True, linewidth=1.5, linecolor='black', mirror=True)
    fig_barras.update_yaxes(showline=True, linewidth=1.5, linecolor='black', mirror=True)

    st.plotly_chart(fig_barras, use_container_width=True)

st.divider()

# =============================================================================
# GRÁFICO 2: HEATMAP (EVOLUCIÓN T1 VS T2)
# =============================================================================
st.subheader("🗺️ 2. Mapa de Calor: Evolución del Logro (T1 vs T2)")
st.markdown("*Muestra el % de estudiantes en Logro (**A + AD**). Pasa el cursor para ver el desglose por nivel.*")

df_heatmap = df_calificados.copy()
df_heatmap['Es_Logro'] = df_heatmap['Nivel_Corto'].isin(['A', 'AD']).astype(int)
heatmap_data = df_heatmap.groupby(['Nombre Competencia', 'Trimestre']).agg({'Es_Logro': ['sum', 'count']}).reset_index()
heatmap_data.columns = ['Nombre Competencia', 'Trimestre', 'Logro_Cantidad', 'Total_Calificados']
heatmap_data['Porcentaje_Logro'] = (heatmap_data['Logro_Cantidad'] / heatmap_data['Total_Calificados'] * 100).round(1)

desglose = df_calificados.groupby(['Nombre Competencia', 'Trimestre', 'Nivel_Corto']).size().reset_index(name='Cantidad')
desglose_pivot = desglose.pivot_table(index=['Nombre Competencia', 'Trimestre'], columns='Nivel_Corto', values='Cantidad', fill_value=0).reset_index()
heatmap_data = heatmap_data.merge(desglose_pivot, on=['Nombre Competencia', 'Trimestre'], how='left')

def crear_tooltip(row):
    total = row['Total_Calificados']
    if total == 0: return "Sin evaluaciones"
    c = row.get('C', 0); b = row.get('B', 0); a = row.get('A', 0); ad = row.get('AD', 0)
    return (f"<b>{row['Nombre Competencia']}</b><br>"
            f"<b>Trimestre:</b> {row['Trimestre']} | <b>Evaluados:</b> {total}<br>"
            f"🔵 <b>Destacado (AD):</b> {ad} ({ad/total*100:.1f}%)<br>"
            f"🟢 <b>Previsto (A):</b> {a} ({a/total*100:.1f}%)<br>"
            f"🟡 <b>Proceso (B):</b> {b} ({b/total*100:.1f}%)<br>"
            f"🔴 <b>Inicio (C):</b> {c} ({c/total*100:.1f}%)<br>"
            f"<b>% Logro (A+AD):</b> {row['Porcentaje_Logro']:.1f}%")

heatmap_data['Tooltip'] = heatmap_data.apply(crear_tooltip, axis=1)

fig_heatmap = go.Figure(go.Heatmap(
    z=heatmap_data['Porcentaje_Logro'], x=heatmap_data['Trimestre'], y=heatmap_data['Nombre Competencia'],
    colorscale=[[0, '#d32f2f'], [0.5, '#fbc02d'], [1, '#388e3c']], zmin=0, zmax=100,
    text=heatmap_data['Porcentaje_Logro'].apply(lambda x: f"{x:.1f}%"),
    texttemplate="%{text}", textfont=dict(size=14, color='white'),
    hovertemplate="%{customdata}<extra></extra>", customdata=heatmap_data['Tooltip'],
    colorbar=dict(title="% Logro")
))
fig_heatmap.update_layout(xaxis_title='Trimestre', yaxis_title='Competencia', height=400, margin=dict(l=200, r=50, t=50, b=50), yaxis=dict(autorange='reversed'))
st.plotly_chart(fig_heatmap, use_container_width=True)

st.divider()

# =============================================================================
# TABLA MATRIZ: DETALLE EXACTO (ORDEN CORREGIDO: T1 y T2 LADO A LADO POR NIVEL)
# =============================================================================
st.subheader("📋 3. Matriz de Detalle: Cantidades Exactas")
tabla_data = df_filtrado.groupby(['Nombre Competencia', 'Trimestre', 'Nivel_Corto']).size().reset_index(name='Cantidad')
tabla_pivot = tabla_data.pivot_table(index='Nombre Competencia', columns=['Trimestre', 'Nivel_Corto'], values='Cantidad', fill_value=0).reset_index()
tabla_pivot.columns = ['_'.join(col).strip('_') if isinstance(col, tuple) and col[1] != '' else col[0] for col in tabla_pivot.columns.values]

# ORDEN CORREGIDO: Primero el NIVEL, luego el TRIMESTRE (para que T1 y T2 queden juntos)
cols_ordenadas = ['Nombre Competencia']
for nivel in ORDEN_NIVELES:  # 'C', 'B', 'A', 'AD'
    for trim in ['T1', 'T2']:
        col_name = f"{trim}_{nivel}"
        if col_name in tabla_pivot.columns:
            cols_ordenadas.append(col_name)
            
tabla_pivot = tabla_pivot[[c for c in cols_ordenadas if c in tabla_pivot.columns]]

rename_dict = {
    col: f"{col.split('_')[0]} - {NOMBRES_NIVELES.get(col.split('_')[1], col.split('_')[1])}" 
    for col in tabla_pivot.columns if col != 'Nombre Competencia'
}
tabla_pivot = tabla_pivot.rename(columns=rename_dict)

st.dataframe(tabla_pivot, use_container_width=True, hide_index=True)

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.caption("Dashboard interactivo | Control de Calidad Educativa | Paleta: Semáforo educativo")