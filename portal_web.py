import streamlit as st
import pandas as pd
import os
import re
import base64

# Configuración de la página con el nombre oficial corregido
st.set_page_config(
    page_title="GR Inversiones Inmobiliaria | Portal de Clientes",
    page_icon="🏢",
    layout="centered"
)

# Clave de acceso para tu panel administrativo
CLAVE_ADMIN = "GR2026"
ARCHIVO_EXCEL = "base_datos_pagos.xlsx"

PROYECTOS_OFICIALES = [
    "RESIDENCIAL JADE",
    "VALLE DE PLATA",
    "VILLA VICTORIA",
    "JOYA DORADA",
    "MISTI LODGE"
]

# Detectar automáticamente el nuevo Logo GR3.png y convertirlo para incrustarlo dentro del banner blanco
ruta_logo = None
for candidato in ["Logo GR3.png", "Logo GR3.png.png", "logo.png", "logo.png.png", "LOGO.PNG", "logo.jpg"]:
    if os.path.exists(candidato):
        ruta_logo = candidato
        break

html_logo = ""
if ruta_logo:
    with open(ruta_logo, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
    html_logo = f'<img src="data:image/png;base64,{logo_b64}" class="logo-corporativo" alt="GR Inversiones Inmobiliaria">'

# Estilos CSS corporativos con los colores Azul Marino (#1b3668) y Dorado (#f5a623) del nuevo logo
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .tarjeta-cabecera {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-top: 6px solid #1b3668;
        border-bottom: 4px solid #f5a623;
        padding: 28px 20px 24px 20px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.18);
    }
    .logo-corporativo {
        max-width: 95px;
        height: auto;
        margin-bottom: 6px;
        display: inline-block;
    }
    .tarjeta-cabecera h1 {
        color: #1b3668 !important;
        margin: 4px 0 6px 0;
        font-size: 25px;
        font-weight: 800;
        letter-spacing: 1.2px;
    }
    .tarjeta-cabecera p {
        color: #4a5568 !important;
        margin: 0;
        font-size: 14.5px;
        font-weight: 500;
    }
    .pie-pagina {
        text-align: center;
        color: #a0aec0;
        font-size: 13px;
        margin-top: 45px;
        padding-top: 15px;
        border-top: 1px solid #2d3748;
    }
    </style>
""", unsafe_allow_html=True)

# Mostrar el logo y el título juntos dentro de la tarjeta blanca para que luzca impecable en modo oscuro y claro
st.markdown(f"""
    <div class="tarjeta-cabecera">
        {html_logo}
        <h1>GR INVERSIONES INMOBILIARIA</h1>
        <p>Portal Oficial de Autogestión — Consulta de Pagos y Boletas Electrónicas</p>
    </div>
""", unsafe_allow_html=True)

def normalizar_lote(texto):
    return re.sub(r'[^A-Z0-9]', '', str(texto).upper())

def normalizar_proyecto(texto):
    limpio = str(texto).upper().strip()
    limpio = re.sub(r'^CUOTAS\s+', '', limpio).strip()
    return limpio

def extraer_numero_cuota(texto):
    numeros = re.findall(r'\d+', str(texto))
    return int(numeros[0]) if numeros else 999

def cargar_datos():
    columnas = [
        "Fecha_Registro", "Proyecto", "Manzana_Lote", "Cuota", 
        "Cliente", "DNI", "Ruta_Voucher", "Ruta_Boleta", "Estado"
    ]
    if not os.path.exists(ARCHIVO_EXCEL):
        return pd.DataFrame(columns=columnas)
    df = pd.read_excel(ARCHIVO_EXCEL, dtype=str).fillna("")
    if "Estado" not in df.columns:
        df["Estado"] = "ACTIVO"
    df.loc[df["Estado"] == "", "Estado"] = "ACTIVO"
    df["Proyecto"] = df["Proyecto"].apply(normalizar_proyecto)
    return df

df = cargar_datos()

# Pestañas: Vista de Clientes vs. Panel de Gestión Administrativa
tab_cliente, tab_admin = st.tabs(["🔍 Consulta de Propietarios", "⚙️ Gestión de Clientes (Admin)"])

# ==============================================================================
# PESTAÑA 1: PORTAL DE AUTOGESTIÓN PARA EL CLIENTE
# ==============================================================================
with tab_cliente:
    with st.container(border=True):
        st.markdown("#### 🔐 Acceso para Propietarios")
        st.caption("Seleccione su proyecto e ingrese su ubicación y DNI del titular para visualizar sus vouchers y descargar sus boletas.")
        
        proyectos_en_bd = sorted([p for p in df["Proyecto"].unique().tolist() if p])
        lista_proyectos = sorted(list(set(PROYECTOS_OFICIALES + proyectos_en_bd)))
        
        proyecto_sel = st.selectbox("📍 1. Proyecto Inmobiliario:", lista_proyectos)
        
        col1, col2 = st.columns(2)
        with col1:
            mz_lote_input = st.text_input("🏡 2. Manzana y Lote:", placeholder="Ej: U-9 o B-5")
        with col2:
            dni_input = st.text_input("🪪 3. DNI del Titular:", max_chars=12, placeholder="Ingrese su DNI")
            
        buscar = st.button("🔍 Consultar Mis Comprobantes", use_container_width=True, type="primary")

    if buscar:
        if not dni_input.strip() or not mz_lote_input.strip():
            st.warning("⚠️ Por favor, complete tanto su Manzana/Lote como el número de DNI del titular.")
        elif df.empty:
            st.info("📄 El sistema aún no cuenta con comprobantes registrados.")
        else:
            lote_buscado = normalizar_lote(mz_lote_input)
            dni_buscado = re.sub(r'\D', '', dni_input)
            
            df["Lote_Norm"] = df["Manzana_Lote"].apply(normalizar_lote)
            df["DNI_Norm"] = df["DNI"].apply(lambda x: re.sub(r'\D', '', str(x)))
            
            # Filtra únicamente contratos ACTIVOS del propietario actual
            resultados = df[
                (df["Proyecto"] == proyecto_sel) & 
                (df["Lote_Norm"] == lote_buscado) & 
                (df["DNI_Norm"] == dni_buscado) &
                (df["Estado"] == "ACTIVO")
            ].copy()
            
            if resultados.empty:
                st.error("❌ No se encontraron comprobantes activos con esos datos. Verifique el Proyecto elegido, su Manzana/Lote y el DNI del titular actual.")
            else:
                resultados["Orden_Cuota"] = resultados["Cuota"].apply(extraer_numero_cuota)
                resultados = resultados.sort_values(by="Orden_Cuota", ascending=True)
                
                cliente_nombre = resultados.iloc[-1]["Cliente"]
                lote_mostrar = resultados.iloc[-1]["Manzana_Lote"]
                
                st.success(f"✅ **Titular Actual:** {cliente_nombre}")
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Proyecto", proyecto_sel)
                m2.metric("Mz / Lote", lote_mostrar)
                m3.metric("Cuotas Registradas", len(resultados))
                
                st.divider()
                st.markdown("#### 📂 Historial de Vouchers y Boletas Electrónicas")
                
                for index, fila in resultados.iterrows():
                    with st.container(border=True):
                        c_info, c_img = st.columns([1.3, 1.1])
                        
                        with c_info:
                            st.markdown(f"### 📌 {fila['Cuota']}")
                            st.write(f"**Fecha de registro:** {fila['Fecha_Registro']}")
                            st.write(f"**Titular:** {fila['Cliente']}")
                            st.write("")
                            
                            # Soporte para PDF en carpeta del repositorio o link de Google Drive
                            ruta_pdf = str(fila.get("Ruta_Boleta", "")).strip().replace("\\", "/")
                            if ruta_pdf.startswith("http"):
                                st.link_button("📥 Descargar Boleta (PDF)", ruta_pdf, use_container_width=True, type="primary")
                            elif ruta_pdf and os.path.exists(ruta_pdf):
                                with open(ruta_pdf, "rb") as pdf_file:
                                    nombre_descarga = f"Boleta_{proyecto_sel}_{lote_mostrar}_{fila['Cuota']}.pdf".replace(" ", "_")
                                    st.download_button(
                                        label="📥 Descargar Boleta (PDF)",
                                        data=pdf_file,
                                        file_name=nombre_descarga,
                                        mime="application/pdf",
                                        key=f"pdf_{index}",
                                        use_container_width=True,
                                        type="primary"
                                    )
                            else:
                                st.warning("⚠️ Boleta PDF en proceso de sincronización.")
                                
                        with c_img:
                            # Soporte para 1, 2 o más vouchers por cada boleta (separados por ';')
                            cadena_vouchers = str(fila.get("Ruta_Voucher", "")).strip()
                            lista_vouchers = [v.strip().replace("\\", "/") for v in cadena_vouchers.split(";") if v.strip()]
                            
                            if not lista_vouchers:
                                st.info("Voucher no disponible")
                            else:
                                for num_v, v_item in enumerate(lista_vouchers, start=1):
                                    etiqueta_v = f"Voucher {num_v} ({fila['Cuota']})" if len(lista_vouchers) > 1 else f"Voucher ({fila['Cuota']})"
                                    if v_item.startswith("http"):
                                        st.link_button(f"👁️ Ver {etiqueta_v}", v_item, use_container_width=True)
                                    elif os.path.exists(v_item):
                                        with open(v_item, "rb") as img_file:
                                            st.image(img_file.read(), caption=etiqueta_v, use_container_width=True)
                                    else:
                                        st.caption(f"🖼️ {etiqueta_v} pendiente de sincronizar.")

# ==============================================================================
# PESTAÑA 2: PANEL DE ADMINISTRACIÓN (TRASPASOS, RESOLUCIONES Y EDICIÓN)
# ==============================================================================
with tab_admin:
    st.markdown("#### 🛠️ Administración de Lotes y Clientes")
    clave_ingresada = st.text_input("🔑 Clave de Administrador:", type="password", placeholder="Ingrese su contraseña")
    
    if clave_ingresada == CLAVE_ADMIN:
        st.success("Acceso administrativo autorizado.")
        
        opcion_admin = st.radio(
            "Seleccione la operación que desea realizar:",
            [
                "1. Cambio de Titular / Traspaso (Mantiene las cuotas pagadas)",
                "2. Resolución de Contrato (Libera el lote para nuevo cliente desde Cuota 1)",
                "3. Editor directo de registros y enlaces (Tabla completa)"
            ]
        )
        
        st.divider()
        
        # OPCIÓN 1: TRASPASO DE PROPIETARIO
        if opcion_admin.startswith("1."):
            st.markdown("##### 🔄 Cambio de Titular / Traspaso de Lote")
            st.caption("Transfiere todas las cuotas activas de un lote al nuevo propietario (actualiza Nombre y DNI).")
            
            c1, c2 = st.columns(2)
            with c1:
                proy_traspaso = st.selectbox("Proyecto del Lote:", sorted(list(set(PROYECTOS_OFICIALES + df["Proyecto"].unique().tolist()))))
            with c2:
                lote_traspaso = st.text_input("Manzana y Lote a traspasar (Ej: U-9):")
                
            c3, c4 = st.columns(2)
            with c3:
                nuevo_nombre = st.text_input("Nuevo Nombre del Propietario:").upper().strip()
            with c4:
                nuevo_dni = re.sub(r'\D', '', st.text_input("Nuevo DNI del Propietario:"))
                
            if st.button("💾 Aplicar Traspaso de Titularidad", type="primary"):
                lote_norm = normalizar_lote(lote_traspaso)
                mascara = (
                    (df["Proyecto"] == proy_traspaso) & 
                    (df["Manzana_Lote"].apply(normalizar_lote) == lote_norm) & 
                    (df["Estado"] == "ACTIVO")
                )
                cantidad = mascara.sum()
                if cantidad == 0:
                    st.error("❌ No se encontraron cuotas activas para ese Proyecto y Lote.")
                elif not nuevo_nombre or not nuevo_dni:
                    st.warning("⚠️ Complete el nuevo nombre y el nuevo DNI.")
                else:
                    df.loc[mascara, "Cliente"] = nuevo_nombre
                    df.loc[mascara, "DNI"] = nuevo_dni
                    df.to_excel(ARCHIVO_EXCEL, index=False)
                    st.success(f"✅ Se actualizaron {cantidad} cuotas del lote {lote_traspaso} a nombre de {nuevo_nombre} (DNI: {nuevo_dni}).")

        # OPCIÓN 2: RESOLUCIÓN DE CONTRATO (NUEVA VENTA DESDE CUOTA 1)
        elif opcion_admin.startswith("2."):
            st.markdown("##### 📁 Resolución de Contrato (Liberar Lote)")
            st.caption("Archiva los pagos del cliente anterior como 'RESUELTO' para que no se mezclen cuando el nuevo comprador empiece a pagar desde la Cuota 1.")
            
            c1, c2 = st.columns(2)
            with c1:
                proy_res = st.selectbox("Proyecto:", sorted(list(set(PROYECTOS_OFICIALES + df["Proyecto"].unique().tolist()))))
            with c2:
                lote_res = st.text_input("Manzana y Lote resuelto (Ej: U-9):")
                
            if st.button("⚠️ Archivar Contrato Anterior y Liberar Lote", type="primary"):
                lote_norm = normalizar_lote(lote_res)
                mascara = (
                    (df["Proyecto"] == proy_res) & 
                    (df["Manzana_Lote"].apply(normalizar_lote) == lote_norm) & 
                    (df["Estado"] == "ACTIVO")
                )
                cantidad = mascara.sum()
                if cantidad == 0:
                    st.error("❌ No hay ningún contrato activo en ese lote.")
                else:
                    titular_ant = df.loc[mascara, "Cliente"].iloc[0]
                    df.loc[mascara, "Estado"] = "RESUELTO"
                    df.to_excel(ARCHIVO_EXCEL, index=False)
                    st.success(f"✅ Se archivaron {cantidad} cuotas del titular anterior ({titular_ant}). El lote {lote_res} está libre para registrar al nuevo propietario desde la Cuota 1.")

        # OPCIÓN 3: EDITOR COMPLETO TIPO EXCEL
        elif opcion_admin.startswith("3."):
            st.markdown("##### 📝 Editor General de la Base de Datos")
            st.caption("Nota: Si una boleta tiene 2 vouchers, coloca sus rutas o links de Drive en 'Ruta_Voucher' separados por punto y coma (;).")
            
            df_editado = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            
            col_g, col_d = st.columns(2)
            with col_g:
                if st.button("💾 Guardar Cambios en el Servidor", use_container_width=True, type="primary"):
                    df_editado.to_excel(ARCHIVO_EXCEL, index=False)
                    st.success("✅ Base de datos actualizada correctamente.")
            with col_d:
                if os.path.exists(ARCHIVO_EXCEL):
                    with open(ARCHIVO_EXCEL, "rb") as f_excel:
                        st.download_button(
                            "📥 Descargar copia en Excel (.xlsx)",
                            data=f_excel,
                            file_name="base_datos_pagos_actualizada.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )

st.markdown("""
    <div class="pie-pagina">
        <b>GR Inversiones Inmobiliaria — Área de Cobranza y Postventa</b><br>
        Arequipa, Perú | Sistema de Consulta Disponible 24/7
    </div>
""", unsafe_allow_html=True)