import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configurações iniciais
CSV_FILE = "controle_pdas.csv"
DATE_FORMAT = "%d/%m/%Y %H:%M:%S"

# Inicializar o DataFrame
def init_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        
        # Converter colunas de data
        df["Data Retirada"] = pd.to_datetime(df["Data Retirada"], errors='coerce')
        df["Data Devolução"] = pd.to_datetime(df["Data Devolução"], errors='coerce')
    else:
        df = pd.DataFrame(columns=[
            "Matrícula", 
            "Data Retirada", 
            "Número PDA", 
            "Data Devolução"
        ])
    return df

# Salvar dados
def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# Verificar se usuário já tem PDA ativo
def usuario_tem_pda_ativo(df, matricula):
    # Normalizar matrícula
    matricula = matricula.strip().upper()
    
    # Encontrar PDAs ativos para a matrícula
    filtro = (df["Matrícula"].str.strip().str.upper() == matricula) & (df["Data Devolução"].isna())
    registros = df[filtro]
    
    if not registros.empty:
        return registros.iloc[0]["Número PDA"]
    return None

# Verificar se PDA já está emprestado
def pda_esta_emprestado(df, pda_num):
    # Normalizar número do PDA
    pda_num = pda_num.strip().upper()
    
    # Verificar se há registro ativo para o PDA
    filtro = (df["Número PDA"].str.strip().str.upper() == pda_num) & (df["Data Devolução"].isna())
    return not df[filtro].empty

# Encontrar registro para devolução
def encontrar_registro_devolucao(df, matricula, pda_num):
    # Normalizar entradas
    matricula = matricula.strip().upper()
    pda_num = pda_num.strip().upper()
    
    # Criar filtro
    filtro = (df["Matrícula"].str.strip().str.upper() == matricula) & \
             (df["Número PDA"].str.strip().str.upper() == pda_num) & \
             (df["Data Devolução"].isna())
    
    # Retornar o primeiro registro encontrado
    registros = df[filtro]
    return registros.index[0] if not registros.empty else None

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
            matricula = st.text_input("Matrícula:", key="matricula", max_chars=20)
        with col2:
            pda_num = st.text_input("Número do PDA:", key="pda_num", max_chars=20)
        
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
                                "Matrícula": matricula.strip().upper(),
                                "Data Retirada": datetime.now(),
                                "Número PDA": pda_num.strip().upper(),
                                "Data Devolução": None
                            }
                            df = pd.concat([df, pd.DataFrame([novo_registro])], ignore_index=True)
                            save_data(df)
                            st.success(f"✅ PDA {pda_num} retirado com sucesso!")
                else:  # Devolução
                    # Encontrar registro para devolução
                    registro_idx = encontrar_registro_devolucao(df, matricula, pda_num)
                    
                    if registro_idx is None:
                        st.error("❌ Registro não encontrado! Verifique se:")
                        st.error("- A matrícula está correta")
                        st.error("- O número do PDA está correto")
                        st.error("- O PDA ainda não foi devolvido")
                    else:
                        # Atualizar data de devolução
                        df.at[registro_idx, "Data Devolução"] = datetime.now()
                        save_data(df)
                        st.success(f"✅ PDA {pda_num} devolvido com sucesso!")
    
    # Histórico e estatísticas
    st.divider()
    st.subheader("Histórico de Movimentações")
    
    # Filtros
    with st.expander("Filtros", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            filtrar_matricula = st.text_input("Filtrar por matrícula:", key="filtro_mat")
        with col2:
            filtrar_pda = st.text_input("Filtrar por PDA:", key="filtro_pda")
        with col3:
            status = st.selectbox("Status:", ["Todos", "Ativos", "Devolvidos"])
    
    # Aplicar filtros
    df_display = df.copy()
    
    # Normalizar filtros
    if filtrar_matricula:
        filtrar_matricula = filtrar_matricula.strip().upper()
        df_display = df_display[
            df_display["Matrícula"].str.strip().str.upper() == filtrar_matricula
        ]
    
    if filtrar_pda:
        filtrar_pda = filtrar_pda.strip().upper()
        df_display = df_display[
            df_display["Número PDA"].str.strip().str.upper() == filtrar_pda
        ]
    
    if status == "Ativos":
        df_display = df_display[df_display["Data Devolução"].isna()]
    elif status == "Devolvidos":
        df_display = df_display[df_display["Data Devolução"].notna()]
    
    # Formatar datas para exibição
    df_display["Data Retirada"] = df_display["Data Retirada"].apply(
        lambda x: x.strftime(DATE_FORMAT) if not pd.isna(x) else "N/A"
    )
    
    df_display["Data Devolução"] = df_display["Data Devolução"].apply(
        lambda x: x.strftime(DATE_FORMAT) if not pd.isna(x) else "Em uso"
    )
    
    # Mostrar histórico
    st.dataframe(
        df_display[["Matrícula", "Número PDA", "Data Retirada", "Data Devolução"]],
        hide_index=True,
        use_container_width=True,
        height=400
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
        data=df.to_csv(index=False, date_format=DATE_FORMAT).encode("utf-8"),
        file_name=f"controle_pdas_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()
