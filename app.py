import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# =============================================================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS
# =============================================================================
st.set_page_config(page_title="Dashboard Unificado - Evolución por Competencias", layout="wide", page_icon="📊")

st.markdown("""
<style>
    div[data-testid="stRadio"] label { background-color: transparent !important; padding: 5px 10px; border-radius: 5px; }
    div[data-testid="stRadio"] label:hover { background-color: #f0f2f6 !important; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DICCIONARIOS Y CONSTANTES (Nombres Cortos para Áreas)
# =============================================================================
DICCIONARIO_AREAS_CORTO = {
    '0001-ART Y CULT': 'ART Y CULT', '0002-CAST SEGNL': 'CAST SEGNL',
    '0003-INGLES EXT': 'INGLES EXT', '0004-CIENC TEC': 'CIENC TEC',
    '0005-COMU': 'COMU', '0006-DESEN TIC': 'DESEN TIC',
    '0007-GEST AUTO': 'GEST AUTO', '0010-DESARR PCC': 'DESARR PCC',
    '014-CCSS': 'CCSS', '017-COMU': 'COMU', '031-EFIS': 'EFIS',
    '032-ETRA': 'ETRA', '035-EREL': 'EREL', '057-INGL': 'INGL',
    '063-MATE': 'MATE', '067-PPSS': 'PPSS', 'M797-QUEM797': 'Quechua',
}

AREAS_PRIMARIA = ['ART Y CULT', 'INGLES EXT', 'CIENC TEC', 'COMU', 'EFIS', 'EREL', 'MATE', 'PPSS', 'DESEN TIC', 'GEST AUTO']
AREAS_SECUNDARIA = ['ART Y CULT', 'CAST SEGNL', 'CIENC TEC', 'DESARR PCC', 'CCSS', 'COMU', 'EFIS', 'ETRA', 'EREL', 'INGL', 'MATE', 'DESEN TIC', 'GEST AUTO', 'Quechua']

COLORES_NIVELES = {'C': '#d32f2f', 'B': '#fbc02d', 'A': '#388e3c', 'AD': '#1565c0', '0': '#9e9e9e'}
ORDEN_NIVELES = ['C', 'B', 'A', 'AD']
NOMBRES_NIVELES = {'C': 'Inicio (C)', 'B': 'Proceso (B)', 'A': 'Logro Previsto (A)', 'AD': 'Logro Destacado (AD)', '0': 'Sin calificar (0)'}

# =============================================================================
# CARGA Y UNIFICACIÓN DE DATOS
# =============================================================================
@st.cache_data
def cargar_datos_unificados():
    ruta_pri = 'data/data_primaria.xlsx'
    ruta_sec = 'data/data_secundaria.xlsx'
    
    dfs = []
    if os.path.exists(ruta_pri):
        df_pri = pd.read_excel(ruta_pri)
        df_pri['Nivel_Educativo'] = 'Primaria'
        dfs.append(df_pri)
    if os.path.exists(ruta_sec):
        df_sec = pd.read_excel(ruta_sec)
        df_sec['Nivel_Educativo'] = 'Secundaria'
        dfs.append(df_sec)
        
    if not dfs:
        st.error("No se encontraron los archivos Excel en la carpeta 'data/'.")
        st.stop()
        
    df = pd.concat(dfs, ignore_index=True)
    
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
    df['Area_Limpia'] = df['Área'].map(DICCIONARIO_AREAS_CORTO).fillna(df['Área'])
    
    return df

df_original = cargar_datos_unificados()

# =============================================================================
# SIDEBAR: FILTROS EN CASCADA
# =============================================================================
st.sidebar.title("🏫 Filtros de Navegación")

# 1. Nivel Educativo
niveles = ['Todos'] + sorted(df_original['Nivel_Educativo'].unique().tolist())
nivel_sel = st.sidebar.radio("1. Nivel Educativo", niveles, horizontal=True)
df_nivel = df_original if nivel_sel == 'Todos' else df_original[df_original['Nivel_Educativo'] == nivel_sel]

# 2. Trimestre (Dinámico)
trimestres_disp = sorted(df_nivel['Trimestre'].unique().tolist())
opciones_trim = [f"Solo {t}" for t in trimestres_disp] + ["Comparar Todos"]
trim_sel = st.sidebar.radio("2. Trimestre", opciones_trim, horizontal=True)

# 3. Grado (Orden Lógico)
orden_grados_base = ['PRIMERO', 'SEGUNDO', 'TERCERO', 'CUARTO', 'QUINTO', 'SEXTO']
grados_disponibles = [g for g in orden_grados_base if g in df_nivel['Grado'].unique()]
grados = ['Todos'] + grados_disponibles
grado_sel = st.sidebar.selectbox("3. Grado", grados)
df_grado = df_nivel if grado_sel == 'Todos' else df_nivel[df_nivel['Grado'] == grado_sel]

# 4. Sección
secciones = ['Todas'] + sorted(df_grado['Sección'].unique().tolist())
seccion_sel = st.sidebar.selectbox("4. Sección", secciones)
df_seccion = df_grado if seccion_sel == 'Todas' else df_grado[df_grado['Sección'] == seccion_sel]

# 5. Área Curricular (Filtrada por Nivel)
if nivel_sel == 'Primaria':
    areas_filtradas = [a for a in AREAS_PRIMARIA if a in df_seccion['Area_Limpia'].unique()]
elif nivel_sel == 'Secundaria':
    areas_filtradas = [a for a in AREAS_SECUNDARIA if a in df_seccion['Area_Limpia'].unique()]
else:
    areas_filtradas = sorted(df_seccion['Area_Limpia'].unique().tolist())

areas = ['Todas'] + areas_filtradas
area_sel = st.sidebar.selectbox("5. Área Curricular", areas)
df_area = df_seccion if area_sel == 'Todas' else df_seccion[df_seccion['Area_Limpia'] == area_sel]

# 6. Competencias
competencias = sorted(df_area['Nombre Competencia'].unique().tolist())
comp_sel = st.sidebar.multiselect("6. Competencias", competencias, default=competencias)

# =============================================================================
# APLICAR FILTROS FINALES
# =============================================================================
df_filtrado = df_area[df_area['Nombre Competencia'].isin(comp_sel)].copy()

if trim_sel != "Comparar Todos":
    trim_elegido = trim_sel.replace("Solo ", "")
    df_filtrado = df_filtrado[df_filtrado['Trimestre'] == trim_elegido]

# =============================================================================
# ENCABEZADO Y KPIs
# =============================================================================
st.title("📊 Evolución del Aprendizaje por Competencias")
st.markdown(f"**Nivel:** `{nivel_sel}` | **Grado:** `{grado_sel}` | **Sección:** `{seccion_sel}` | **Área:** `{area_sel}`")
st.divider()

if df_filtrado.empty:
    st.warning("⚠️ No hay datos disponibles para la combinación de filtros seleccionada.")
    st.stop()

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
with col1: st.metric(" Total Estudiantes", total_estudiantes)
with col2: st.metric("🔴 Inicio (C)", f"{pct_c:.1f}%")
with col3: st.metric("🟡 Proceso (B)", f"{pct_b:.1f}%")
with col4: st.metric("🟢 Previsto (A)", f"{pct_a:.1f}%")
with col5: st.metric("🔵 Destacado (AD)", f"{pct_ad:.1f}%")
with col6: st.metric("⚪ Sin calificar", f"{pct_sin_cal:.1f}%")

st.divider()

# =============================================================================
# SEMÁFORO DE DESEMPEÑO POR ÁREA
# =============================================================================
st.subheader("🚦 Semáforo de Desempeño por Área")
st.markdown("*Indicador de salud pedagógica basado en el % de Logro (A + AD). Rojo (<50%), Amarillo (50-75%), Verde (>75%).*")

df_calif_area = df_filtrado[df_filtrado['Nivel_Corto'] != '0']
if not df_calif_area.empty:
    area_logro = df_calif_area[df_calif_area['Nivel_Corto'].isin(['A', 'AD'])].groupby('Area_Limpia').size()
    area_total = df_calif_area.groupby('Area_Limpia').size()
    area_pct = (area_logro / area_total * 100).fillna(0).round(1)
    
    areas_to_show = area_pct.index.tolist()
    
    if areas_to_show:
        cols_per_row = 5
        for i in range(0, len(areas_to_show), cols_per_row):
            cols = st.columns(min(cols_per_row, len(areas_to_show) - i))
            for j, area in enumerate(areas_to_show[i:i+cols_per_row]):
                pct = area_pct[area]
                if pct < 50:
                    bg_color, text_color, status = "#d32f2f", "white", "🔴 GRAVE"
                elif pct < 75:
                    bg_color, text_color, status = "#fbc02d", "black", "🟡 ALERTA"
                else:
                    bg_color, text_color, status = "#388e3c", "white", "🟢 BUEN CAMINO"
                
                with cols[j]:
                    st.markdown(f"""
                    <div style="background-color: {bg_color}; color: {text_color}; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.2); height: 100%;">
                        <h4 style="margin: 0; font-size: 1.1rem; font-weight: bold;">{area}</h4>
                        <h2 style="margin: 10px 0; font-size: 2.2rem; font-weight: bold;">{pct}%</h2>
                        <p style="margin: 0; font-weight: bold; font-size: 0.9rem;">{status}</p>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No hay áreas con datos calificados para mostrar el semáforo.")
else:
    st.info("No hay estudiantes calificados en los filtros seleccionados.")

st.divider()

# =============================================================================
# GRÁFICO 1: BARRAS APILADAS
# =============================================================================
st.subheader("📊 1. Distribución de Niveles por Competencia")

if trim_sel == "Comparar Todos":
    st.info("💡 Para ver la distribución detallada, selecciona un trimestre específico ('Solo T1', etc.). Para comparar evolución, usa el Mapa de Calor.")
else:
    st.markdown("*Cada barra representa el 100% de estudiantes evaluados en este trimestre.*")

    def formatear_nombre(nombre):
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
        df_nivel_chart = df_barras[df_barras['Nivel_Corto'] == nivel]
        custom_data = [[row['Nombre Competencia'], row['Trimestre'], row['Cantidad'], row['Porcentaje']] for _, row in df_nivel_chart.iterrows()]
        color_texto = 'black' if nivel in ['B', 'C'] else 'white'

        fig_barras.add_trace(go.Bar(
            name=f"Estudiantes en {NOMBRES_NIVELES[nivel]}",
            x=df_nivel_chart['Nombre_Corto'],
            y=df_nivel_chart['Porcentaje'],
            marker_color=COLORES_NIVELES[nivel],
            marker_line=dict(color='black', width=1.2),
            text=df_nivel_chart['Porcentaje'].apply(lambda x: f"{x:.2f} %".replace('.', ',') if x > 0 else ""),
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
# GRÁFICO 2: HEATMAP
# =============================================================================
st.subheader("🗺️ 2. Mapa de Calor: Evolución del Logro")
st.markdown("*Muestra el % de estudiantes en Logro (**A + AD**). Pasa el cursor para ver el desglose.*")

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
# TABLA MATRIZ
# =============================================================================
st.subheader("📋 3. Matriz de Detalle: Cantidades Exactas")
tabla_data = df_filtrado.groupby(['Nombre Competencia', 'Trimestre', 'Nivel_Corto']).size().reset_index(name='Cantidad')
tabla_pivot = tabla_data.pivot_table(index='Nombre Competencia', columns=['Trimestre', 'Nivel_Corto'], values='Cantidad', fill_value=0).reset_index()
tabla_pivot.columns = ['_'.join(col).strip('_') if isinstance(col, tuple) and col[1] != '' else col[0] for col in tabla_pivot.columns.values]

cols_ordenadas = ['Nombre Competencia']
for nivel in ORDEN_NIVELES:
    for trim in sorted(df_filtrado['Trimestre'].unique()):
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
st.caption("Dashboard interactivo unificado | Control de Calidad Educativa | Paleta: Semáforo educativo")
