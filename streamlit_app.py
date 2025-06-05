import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Nome do arquivo CSV para armazenar os dados
CSV_FILE = "controle_pdas.csv"

# Inicializar o DataFrame se o arquivo não existir
def init_data():
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=[
            "Matrícula", 
            "Data Retirada", 
            "Número PDA", 
            "Data Devolução"
        ])
        df.to_csv(CSV_FILE, index=False)

# Carregar dados do CSV
def load_data():
    return pd.read_csv(CSV_FILE, parse_dates=["Data Retirada", "Data Devolução"])

# Salvar dados no CSV
def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# Verificar se usuário já tem PDA ativo
def usuario_tem_pda_ativo(df, matricula):
    filtro = (df["Matrícula"] == matricula) & (df["Data Devolução"].isna())
    if not df[filtro].empty:
        return df[filtro].iloc[0]["Número PDA"]
    return None

# Verificar se PDA já está emprestado
def pda_esta_emprestado(df, pda_num):
    filtro = (df["Número PDA"] == pda_num) & (df["Data Devolução"].isna())
    return not df[filtro].empty

# Interface Streamlit
def main():
    st.title("📱 Controle de PDAs")
    st.subheader("Registro de Entrada e Saída de Equipamentos")
    
    init_data()
    df = load_data()
    
    # Seleção de operação
    operacao = st.radio("Selecione a operação:", 
                        ("Retirada de PDA", "Devolução de PDA"),
                        horizontal=True)
    
    # Campos de entrada
    matricula = st.text_input("Matrícula:", max_chars=20).strip().upper()
    pda_num = st.text_input("Número do PDA:", max_chars=20).strip().upper()
    
    # Botão de confirmação
    if st.button("Confirmar Operação"):
        if not matricula or not pda_num:
            st.error("Preencha todos os campos!")
            return
            
        if operacao == "Retirada de PDA":
            # Verifica se usuário já tem PDA ativo
            pda_ativo = usuario_tem_pda_ativo(df, matricula)
            if pda_ativo:
                st.error(f"ERRO: Usuário já possui PDA {pda_ativo} ativo!")
                return
                
            # Verifica se PDA já está emprestado
            if pda_esta_emprestado(df, pda_num):
                st.error(f"ERRO: PDA {pda_num} já está emprestado!")
                return
                
            # Registra nova retirada
            novo_registro = pd.DataFrame([{
                "Matrícula": matricula,
                "Data Retirada": datetime.now(),
                "Número PDA": pda_num,
                "Data Devolução": None
            }])
            
            df = pd.concat([df, novo_registro], ignore_index=True)
            save_data(df)
            st.success(f"PDA {pda_num} retirado com sucesso!")
            
        else:  # Devolução
            # Encontra registro correspondente
            filtro = (df["Matrícula"] == matricula) & \
                     (df["Número PDA"] == pda_num) & \
                     (df["Data Devolução"].isna())
                     
            registros = df[filtro]
            
            if registros.empty:
                st.error("Registro não encontrado ou PDA já devolvido!")
            else:
                # Atualiza data de devolução
                idx = registros.index[0]
                df.at[idx, "Data Devolução"] = datetime.now()
                save_data(df)
                st.success(f"PDA {pda_num} devolvido com sucesso!")
    
    # Exibir histórico
    st.divider()
    st.subheader("Histórico de Movimentações")
    
    # Filtros para o histórico
    col1, col2 = st.columns(2)
    with col1:
        filtrar_matricula = st.text_input("Filtrar por matrícula:").strip().upper()
    with col2:
        filtrar_pda = st.text_input("Filtrar por PDA:").strip().upper()
    
    # Aplicar filtros
    df_display = df.copy()
    if filtrar_matricula:
        df_display = df_display[df_display["Matrícula"] == filtrar_matricula]
    if filtrar_pda:
        df_display = df_display[df_display["Número PDA"] == filtrar_pda]
    
    # Mostrar dataframe formatado
    st.dataframe(
        df_display.sort_values("Data Retirada", ascending=False),
        column_config={
            "Data Retirada": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
            "Data Devolução": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm")
        },
        hide_index=True,
        height=300
    )
    
    # Estatísticas
    st.divider()
    st.subheader("Estatísticas")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de PDAs", df["Número PDA"].nunique())
    with col2:
        st.metric("Emprestados Ativos", df["Data Devolução"].isna().sum())
    with col3:
        st.metric("Total de Movimentações", len(df))

if __name__ == "__main__":
    main()
