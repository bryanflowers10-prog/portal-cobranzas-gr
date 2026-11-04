import streamlit as st
import pandas as pd
import os
import re

# Configuración de la pestaña del navegador
st.set_page_config(
    page_title="GR Inmobiliaria | Portal de Clientes",
    page_icon="🏢",
    layout="centered"
)

# Estilos CSS personalizados para darle acabado corporativo y ocultar marcas de agua
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .banner-corporativo {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        padding: 28px 20px;
        border-radius: 14px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }
    .banner-corporativo h1 {
        color: #ffffff;
        margin: 0;
        font-size: 28px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .banner-corporativo p {
        color: #d1e8e2;
        margin-top: 8px;
        font-size: 15px;
        margin-bottom: 0;
    }
    .pie-pagina {
        text-align: center;
        color: #6c757d;
        font-size: 13px;
        margin-top: 40px;
        padding-top: 15px;
        border-top: 1px solid #e9ecef;
    }
    </style>
""", unsafe_allow_html=True)

# Mostrar logo si existe en la carpeta
if os.path.exists("logo.png"):
    col_l1, col_l2, col_l3 = st.columns([1.2, 1, 1.2])
    with col_l2:
        st.image("logo.png", use_container_width=True)

# Encabezado Corporativo
st.markdown("""
    <div class="banner-corporativo">
        <h1>🏢 GR INMOBILIARIA</h1>
        <p>Portal Oficial de Autogestión — Consulta de Pagos y Boletas Electrónicas</p>
    </div>
""", unsafe_allow_html=True)

ARCHIVO_EXCEL = "base_datos_pagos.xlsx"

def normalizar_lote(texto):
    """Convierte 'u 9', 'U-09' o 'U9' en un formato estándar para que el cliente no falle al buscar"""
    limpio = re.sub(r'[^A-Z0-9]', '', str(texto).upper())
    return limpio

def extraer_numero_cuota(texto):
    """Extrae el número de la cuota para ordenarlas de menor a mayor (Cuota 1, Cuota 2...)"""
    numeros = re.findall(r'\d+', str(texto))
    return int(numeros[0]) if numeros else 999

if not os.path.exists(ARCHIVO_EXCEL):
    st.info("🛠️ El portal se encuentra sincronizando la base de datos. Intente nuevamente en unos minutos.")
else:
    df = pd.read_excel(ARCHIVO_EXCEL, dtype=str)
    
    if df.empty:
        st.info("📄 Aún no hay comprobantes publicados en el sistema.")
    else:
        with st.container(border=True):
            st.markdown("#### 🔐 Acceso exclusivo para Propietarios")
            st.caption("Seleccione su proyecto e ingrese los datos de su lote para descargar sus boletas en PDF.")
            
            lista_proyectos = sorted(df["Proyecto"].dropna().unique().tolist())
            proyecto_sel = st.selectbox("📍 1. Proyecto Inmobiliario:", lista_proyectos)
            
            col1, col2 = st.columns(2)
            with col1:
                mz_lote_input = st.text_input("🏡 2. Manzana y Lote:", placeholder="Ejemplo: U-9 o B-5")
            with col2:
                dni_input = st.text_input("🪪 3. DNI del Titular:", max_chars=12, placeholder="Ingrese su DNI")
                
            buscar = st.button("🔍 Consultar Mi Estado de Pagos", use_container_width=True, type="primary")

        if buscar:
            if not dni_input.strip() or not mz_lote_input.strip():
                st.warning("⚠️ Por favor, complete tanto su Manzana/Lote como el número de DNI del titular.")
            else:
                lote_buscado = normalizar_lote(mz_lote_input)
                dni_buscado = re.sub(r'\D', '', dni_input)
                
                # Crear columna temporal normalizada para comparar sin importar guiones o espacios
                df["Lote_Norm"] = df["Manzana_Lote"].apply(normalizar_lote)
                df["DNI_Norm"] = df["DNI"].apply(lambda x: re.sub(r'\D', '', str(x)))
                
                resultados = df[
                    (df["Proyecto"] == proyecto_sel) & 
                    (df["Lote_Norm"] == lote_buscado) & 
                    (df["DNI_Norm"] == dni_buscado)
                ].copy()
                
                if resultados.empty:
                    st.error("❌ No se encontraron comprobantes con esos datos. Verifique haber elegido el Proyecto correcto, su Manzana/Lote y el DNI del titular.")
                else:
                    # Ordenar automáticamente por número de cuota (Cuota 1, Cuota 2, etc.)
                    resultados["Orden_Cuota"] = resultados["Cuota"].apply(extraer_numero_cuota)
                    resultados = resultados.sort_values(by="Orden_Cuota", ascending=True)
                    
                    cliente_nombre = resultados.iloc[0]["Cliente"]
                    lote_mostrar = resultados.iloc[0]["Manzana_Lote"]
                    
                    st.success(f"✅ **Propietario(a):** {cliente_nombre}")
                    
                    # Tarjetas de resumen para el cliente
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Proyecto", proyecto_sel)
                    m2.metric("Ubicación (Mz/Lote)", lote_mostrar)
                    m3.metric("Cuotas Registradas", len(resultados))
                    
                    st.divider()
                    st.markdown("#### 📂 Historial de Vouchers y Boletas de Venta")
                    
                    for index, fila in resultados.iterrows():
                        with st.container(border=True):
                            c_info, c_img = st.columns([1.4, 1])
                            
                            with c_info:
                                st.markdown(f"### 📌 {fila['Cuota']}")
                                st.write(f"**Fecha de registro:** {fila['Fecha_Registro']}")
                                st.write(f"**Titular:** {fila['Cliente']}")
                                st.write("")
                                
                                ruta_pdf = fila["Ruta_Boleta"]
                                if os.path.exists(ruta_pdf):
                                    with open(ruta_pdf, "rb") as pdf_file:
                                        nombre_limpio = f"Boleta_{proyecto_sel}_{lote_mostrar}_{fila['Cuota']}.pdf".replace(" ", "_")
                                        st.download_button(
                                            label="📥 Descargar Boleta Electrónica (PDF)",
                                            data=pdf_file,
                                            file_name=nombre_limpio,
                                            mime="application/pdf",
                                            key=f"pdf_{index}",
                                            use_container_width=True,
                                            type="primary"
                                        )
                                else:
                                    st.warning("⚠️ El archivo PDF no se encuentra disponible localmente.")
                                    
                            with c_img:
                                ruta_img = fila["Ruta_Voucher"]
                                if os.path.exists(ruta_img):
                                    with open(ruta_img, "rb") as img_file:
                                        st.image(img_file.read(), caption=f"Voucher de pago ({fila['Cuota']})", use_container_width=True)

st.markdown("""
    <div class="pie-pagina">
        <b>GR Inmobiliaria — Área de Cobranza y Postventa</b><br>
        Arequipa, Perú | Atención de consultas sobre sus comprobantes de pago.
    </div>
""", unsafe_allow_html=True)