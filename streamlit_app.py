import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os
import time

# Configurações iniciais
CSV_FILE = "controle_pdas.csv"
DATE_FORMAT = "%d/%m/%Y %H:%M:%S"

# Inicializar o DataFrame
@st.cache_resource(show_spinner=False)
def init_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(
            CSV_FILE,
            parse_dates=["Data Retirada", "Data Devolução"],
            dayfirst=True
        )
    else:
        df = pd.DataFrame(columns=[
            "Matrícula", 
            "Data Retirada", 
            "Número PDA", 
            "Data Devolução"
        ])
        df.to_csv(CSV_FILE, index=False, date_format=DATE_FORMAT)
    
    # Converter colunas de data para datetime se necessário
    if not df.empty:
        if not pd.api.types.is_datetime64_any_dtype(df["Data Retirada"]):
            df["Data Retirada"] = pd.to_datetime(df["Data Retirada"], dayfirst=True)
        if not pd.api.types.is_datetime64_any_dtype(df["Data Devolução"]):
            df["Data Devolução"] = pd.to_datetime(df["Data Devolução"], dayfirst=True)
    
    return df

# Salvar dados
def save_data(df):
    df.to_csv(CSV_FILE, index=False, date_format=DATE_FORMAT)
    st.cache_resource.clear()

# Verificar se usuário já tem PDA ativo
def usuario_tem_pda_ativo(df, matricula):
    filtro = (df["Matrícula"] == matricula) & (df["Data Devolução"].isna())
    registros = df[filtro]
    if not registros.empty:
        return registros.iloc[0]["Número PDA"]
    return None

# Verificar se PDA já está emprestado
def pda_esta_emprestado(df, pda_num):
    filtro = (df["Número PDA"] == pda_num) & (df["Data Devolução"].isna())
    return not df[filtro].empty

# Interface principal
def main():
    st.set_page_config(
        page_title="Controle de PDAs", 
        page_icon="📱",
        layout="centered"
    )
    
    st.title("📱 Controle de PDAs")
    st.caption("Sistema de registro de entrada e saída de equipamentos")
    
    # Carregar dados
    df = init_data()
    
    # Formulário de operação
    with st.form("operacao_form", clear_on_submit=True):
        operacao = st.radio(
            "Selecione a operação:", 
            ("Retirada de PDA", "Devolução de PDA"),
            horizontal=True
        )
        
        col1, col2 = st.columns(2)
        with col1:
            matricula = st.text_input("Matrícula:", key="matricula", max_chars=20).strip().upper()
        with col2:
            pda_num = st.text_input("Número do PDA:", key="pda_num", max_chars=20).strip().upper()
        
        submitted = st.form_submit_button("Confirmar Operação")
        
        if submitted:
            if not matricula or not pda_num:
                st.error("Preencha todos os campos!")
            else:
                if operacao == "Retirada de PDA":
                    # Verificar se usuário já tem PDA ativo
                    pda_ativo = usuario_tem_pda_ativo(df, matricula)
                    if pda_ativo:
                        st.error(f"ERRO: Usuário já possui PDA {pda_ativo} ativo!")
                    else:
                        # Verificar se PDA já está emprestado
                        if pda_esta_emprestado(df, pda_num):
                            st.error(f"ERRO: PDA {pda_num} já está emprestado!")
                        else:
                            # Registrar nova retirada
                            novo_registro = {
                                "Matrícula": matricula,
                                "Data Retirada": datetime.now(),
                                "Número PDA": pda_num,
                                "Data Devolução": None
                            }
                            df = pd.concat([df, pd.DataFrame([novo_registro])], ignore_index=True)
                            save_data(df)
                            st.success(f"✅ PDA {pda_num} retirado com sucesso!")
                else:  # Devolução
                    # Encontrar registro correspondente
                    filtro = (df["Matrícula"] == matricula) & \
                             (df["Número PDA"] == pda_num) & \
                             (df["Data Devolução"].isna())
                    
                    registros = df[filtro]
                    
                    if registros.empty:
                        st.error("❌ Registro não encontrado ou PDA já devolvido!")
                    else:
                        # Atualizar data de devolução
                        idx = registros.index[0]
                        df.at[idx, "Data Devolução"] = datetime.now()
                        save_data(df)
                        st.success(f"✅ PDA {pda_num} devolvido com sucesso!")
    
    # Histórico e estatísticas
    st.divider()
    st.subheader("Histórico de Movimentações")
    
    # Filtros
    with st.expander("Filtros", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            filtrar_matricula = st.text_input("Filtrar por matrícula:", key="filtro_mat").strip().upper()
        with col2:
            filtrar_pda = st.text_input("Filtrar por PDA:", key="filtro_pda").strip().upper()
        with col3:
            status = st.selectbox("Status:", ["Todos", "Ativos", "Devolvidos"])
    
    # Aplicar filtros
    df_display = df.copy()
    if filtrar_matricula:
        df_display = df_display[df_display["Matrícula"] == filtrar_matricula]
    if filtrar_pda:
        df_display = df_display[df_display["Número PDA"] == filtrar_pda]
    if status == "Ativos":
        df_display = df_display[df_display["Data Devolução"].isna()]
    elif status == "Devolvidos":
        df_display = df_display[df_display["Data Devolução"].notna()]
    
    # Formatar datas para exibição
    df_display["Data Retirada"] = df_display["Data Retirada"].dt.strftime(DATE_FORMAT)
    df_display["Data Devolução"] = df_display["Data Devolução"].apply(
        lambda x: x.strftime(DATE_FORMAT) if not pd.isna(x) else "Em uso"
    )
    
    # Mostrar histórico
    st.dataframe(
        df_display,
        column_order=["Matrícula", "Número PDA", "Data Retirada", "Data Devolução"],
        hide_index=True,
        use_container_width=True,
        height=300
    )
    
    # Estatísticas
    st.divider()
    st.subheader("Estatísticas")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        total_pdas = df["Número PDA"].nunique()
        st.metric("Total de PDAs", total_pdas)
    with col2:
        ativos = df["Data Devolução"].isna().sum()
        st.metric("PDAs Ativos", ativos)
    with col3:
        movimentacoes = len(df)
        st.metric("Total Movimentações", movimentacoes)
    
    # Exportar dados
    st.download_button(
        label="Exportar Dados (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"controle_pdas_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()
