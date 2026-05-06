import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Finanças - Iza & João",
    page_icon=":material/account_balance_wallet:",
    layout="wide",
    initial_sidebar_state="auto"  # auto = collapsa no mobile, expandida no desktop
)

MESES_PT = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}
MESES_PT_CURTO = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
}


def fmt_brl(valor):
    return f"R$ {valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def mes_label_pt(ano_mes_str):
    dt = pd.to_datetime(ano_mes_str)
    return f"{MESES_PT[dt.month]}/{dt.year}"


def mes_label_curto(ano_mes_str):
    dt = pd.to_datetime(ano_mes_str)
    return f"{MESES_PT_CURTO[dt.month]}/{str(dt.year)[2:]}"


# CSS global
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .main .block-container { padding-top: 1.5rem; max-width: 1400px; }

    section[data-testid="stSidebar"] { background-color: #1a1a2e !important; }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] small,
    section[data-testid="stSidebar"] .stMarkdown { color: #e0e0ff !important; font-size: 14px !important; }
    section[data-testid="stSidebar"] h3 { color: #ffffff !important; font-size: 16px !important; font-weight: 700 !important; }
    section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15) !important; }

    section[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(100,149,237,0.4) !important;
        color: #a0b4f0 !important;
    }
    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: rgba(255,255,255,0.15) !important;
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] button[kind="secondary"] p { color: #a0b4f0 !important; }

    section[data-testid="stSidebar"] [data-testid="stFileUploader"] {
        background-color: rgba(255,255,255,0.06) !important;
        border: 1px dashed rgba(100,149,237,0.5) !important;
        border-radius: 10px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] * { color: #a0b4f0 !important; }
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] { background-color: transparent !important; }
    .stSelectbox > label, .stMultiSelect > label { font-size: 14px; font-weight: 600; }

    /* Botao de collapse/expand da sidebar - Material Symbols nao carrega esses 2 icones,
       ent~ao escondemos o texto cru "keyboard_double_arrow_*" e injetamos seta unicode */
    [data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"],
    [data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"] {
        font-size: 0 !important;
        color: transparent !important;
        position: relative !important;
        width: 24px !important;
        height: 24px !important;
        display: inline-block !important;
    }
    [data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"]::before {
        content: "‹‹" !important;
        font-size: 18px !important;
        font-family: Inter, system-ui, sans-serif !important;
        font-weight: 800 !important;
        color: #a0b4f0 !important;
        position: absolute !important;
        left: 50% !important;
        top: 50% !important;
        transform: translate(-50%, -50%) !important;
    }
    [data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"]::before {
        content: "››" !important;
        font-size: 18px !important;
        font-family: Inter, system-ui, sans-serif !important;
        font-weight: 800 !important;
        color: #2d2d3a !important;
        position: absolute !important;
        left: 50% !important;
        top: 50% !important;
        transform: translate(-50%, -50%) !important;
    }

    /* Fix do "uploadUpload" duplicado - escondemos o icon e mantemos o texto */
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button [data-testid="stIconMaterial"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CLASSIFICACAO DE CATEGORIAS
# ============================================================
# ESSENCIAL = se repete todo mês, não dá pra cortar
CATEGORIAS_ESSENCIAIS = [
    'Aluguel/Financiamento', 'Contas',
    'Alimentação',
    'Combustível', 'Uber / 99', 'Pedágio / Estacionamento', 'Transporte Geral',
    'Assinatura / Financiamento',
    'Assinaturas m', 'Tarifas / Assinaturas', 'Internet / Telefone',
    'Empregados / Faxineira', 'Empregados / Funcionários',
    'Plano Saúde', 'Seguros',
    'Impostos', 'Impostos PJ', 'Simples Nacional', 'Condomínio', 'IPTU / IPVA',
    'Dividas', 'FIES',
    'Academia', 'Planejamento Financeiro',
    'IOF / Tarifas',  # taxas bancárias obrigatórias
    'Contabilidade',
    'João filho',  # escola do filho (Espaço Plenit) - essencial!
    'Educação',  # essencial
    'Financiamento Aparelho US',  # equipamento médico Santander - essencial até quitar
]

# NÃO ESSENCIAL = dá pra reduzir
CATEGORIAS_NAO_ESSENCIAIS = [
    'Restaurante / Ifood', 'Bares / Festas',
    'Compras Geral', 'Compras Moradia', 'Roupa / Sapatos / Vestuário',
    'Farmácia', 'Saúde Geral',
    'Cuidados pessoais Geral', 'Estética e Tratamentos',
    'Pets', 'Lazer Geral', 'Presentes',
    'Tecnologia / Diversas', 'Manutenção / Revisão',
    'Psciologo / Nutri / Fisio (Terapias)',
    'Ajuda Familiares / Terceiros', 'Moradia / Casa Geral',
    'Mercado', 'Beleza / Estética',
]

# EVENTUAL = pontual, NÃO projetar
CATEGORIAS_EVENTUAIS = [
    'Casamento', 'Viagens', 'Deus',
    'Ajustes / Cash  Back / Acertos', 'Outras Eventuais',
    'Médicos',
    'Trabalho - Consultório Geral', 'Aluguel Consultório',
    'Insumos / Materiais', 'Contas - Consultório', 'Marketing',
    'Acertos mãe saida',  # categoria nova criada na reuniao
    # Receitas eventuais (nao recorrentes) - confirmadas pela Iza:
    'Eventual - Ressarcimento Governo',  # Iza: "todo de uma vez, nao vai receber mais"
    'Eventual - Caucao Apt',  # Devolucao caucao - unica
]


def classificar_tipo_despesa(categoria):
    if categoria in CATEGORIAS_ESSENCIAIS:
        return 'Essencial'
    elif categoria in CATEGORIAS_NAO_ESSENCIAIS:
        return 'Não Essencial'
    elif categoria in CATEGORIAS_EVENTUAIS:
        return 'Eventual'
    else:
        return 'Outros'


# Mapeamento subcategoria -> categoria mae
# 100% IGUAL AO PLANFI (validado por engenharia reversa dos valores de mar/2026)
MAPA_CATEGORIAS = {
    # Receitas
    'Renda': ['Hospitais - Plantão (Fixo)', 'Variável (Consultório / Laudos )', 'Váriável (Consultório / Laudos )', 'Renda Geral'],
    'Entrada': ['Entrada Geral'],
    'Ajustes': ['Ajustes / Cash  Back / Acertos'],
    'Repasses': ['Repasses'],
    'Receita Eventual': ['Eventual - Ressarcimento Governo', 'Eventual - Caucao Apt'],

    # Despesas (mesmo agrupamento do Planfi)
    'Ajuda Familiares / Terceiros': ['Ajuda Familiares / Terceiros', 'Acertos mãe saida'],
    'Alimentação': ['Alimentação'],  # Planfi: SO Alimentação (Restaurante/iFood e Bares vao pra Lazer)
    'Casamento': ['Casamento'],
    'Compras': ['Compras Geral', 'Roupa / Sapatos / Vestuário', 'Tecnologia / Diversas', 'Presentes'],
    'Cuidados pessoais': ['Cuidados pessoais Geral', 'Academia', 'Estética e Tratamentos',
                          'Psciologo / Nutri / Fisio (Terapias)',
                          'Farmácia',  # ← Planfi coloca Farmacia aqui (NAO em Saude)
                          ],
    'Dívidas': ['Dividas', 'FIES', 'Financiamento Aparelho US'],
    'Educação': ['Educação'],
    'IOF / Tarifas': ['IOF / Tarifas', 'Juros/ IOF / Tarifas'],
    'João filho': ['João filho'],
    'Lazer': ['Lazer Geral', 'Restaurante / Ifood', 'Bares / Festas'],  # Planfi inclui restaurante e bares
    'Moradia / Casa': ['Aluguel/Financiamento', 'Contas', 'Manutenção / Revisão',
                       'Empregados / Faxineira', 'Assinaturas m', 'Moradia / Casa Geral',
                       'Compras Moradia'],
    'Pets': ['Pets'],
    'Planejamento Financeiro': ['Planejamento Financeiro'],
    'Saúde': ['Saúde Geral', 'Plano Saúde', 'Médicos'],  # SEM Farmacia (vai pra Cuidados pessoais)
    'Seguros': ['Seguros', 'Seguro Carro'],
    'Trabalho - Consultório': ['Trabalho - Consultório Geral', 'Aluguel Consultório', 'Contas - Consultório',
                                'Insumos / Materiais', 'Marketing', 'Empregados / Funcionários',
                                'Trafego Pago - Marketing', 'Contabilidade',
                                'Impostos', 'Impostos PJ', 'Simples Nacional',  # ← Planfi coloca todos os impostos aqui
                                'Tarifas / Assinaturas',  # ← Tambem aqui (NAO em IOF)
                                ],
    'Transporte': ['Combustível', 'Uber / 99', 'Pedágio / Estacionamento', 'Transporte Geral',
                   'Assinatura / Financiamento'],
    'Viagens': ['Viagens'],
    'Outros': ['Outros', 'Deus', 'A Categorizar'],
}

CATEGORIA_MAE = {}
for mae, subs in MAPA_CATEGORIAS.items():
    for sub in subs:
        CATEGORIA_MAE[sub] = mae


def get_categoria_mae(cat):
    return CATEGORIA_MAE.get(cat, cat)


# ============================================================
# LOAD DATA
# ============================================================
@st.cache_data(ttl=30)
def load_data(file_path=None, uploaded_file=None):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    elif file_path and os.path.exists(file_path):
        df = pd.read_csv(file_path, encoding='utf-8')
    else:
        return None

    df['Valor_num'] = df['Valor'].str.replace('R$ ', '', regex=False)\
                                  .str.replace('.', '', regex=False)\
                                  .str.replace(',', '.', regex=False)\
                                  .astype(float)

    df['Data_parsed'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
    df['Ano_Mes'] = df['Data_parsed'].dt.strftime('%Y-%m')

    col_desc = [c for c in df.columns if 'escri' in c.lower()]
    if col_desc:
        df = df.rename(columns={col_desc[0]: 'Descrição'})

    # DEBT = dívida — virar EXPENSE e forçar categoria Dividas
    mask_debt = df['Tipo'] == 'DEBT'
    df.loc[mask_debt, 'Categoria'] = 'Dividas'
    df['Tipo'] = df['Tipo'].replace('DEBT', 'EXPENSE')

    df['Categoria'] = df['Categoria'].fillna('A Categorizar')
    df['Conta'] = df['Conta'].fillna('Sem Conta')
    df['Descrição'] = df['Descrição'].fillna('')

    # "Acertos mãe saida" no Planfi NAO conta como despesa real (ajuste/repasse)
    # Tratar como TRANSFERENCIA pra ficar igual ao Planfi
    mask_acertos = df['Categoria'] == 'Acertos mãe saida'
    df.loc[mask_acertos, 'Tipo'] = 'TRANSFERENCIA'

    # ELIMINAR DISTORCAO DE PROJECAO COM RECEITAS EVENTUAIS DE FEVEREIRO:
    # 1) Ressarcimento governo (20/02): 15 PIX entre R$ 100 e R$ 1.636 = R$ 13.570 - Iza disse que nao vai receber mais
    # 2) Caucao apartamento (13/02): R$ 8.134,55 - devolucao unica
    # Reclassificar pra "Eventual - Recebimento Atrasado" (categoria que NAO entra na media)
    mask_governo = (df['Data_parsed'] == '2026-02-20') & \
                   (df['Conta'].str.contains('CAIXA PJ', case=False, na=False)) & \
                   (df['Tipo'] == 'INCOME')
    df.loc[mask_governo, 'Categoria'] = 'Eventual - Ressarcimento Governo'

    mask_caucao = (df['Data_parsed'] == '2026-02-13') & \
                  (df['Valor_num'] == 8134.55) & \
                  (df['Tipo'] == 'INCOME')
    df.loc[mask_caucao, 'Categoria'] = 'Eventual - Caucao Apt'

    # Reclassificar empréstimos como Dívidas
    df.loc[df['Descrição'].str.contains('Installment.*EMPRESTIMO|EMPRESTIMO|CDC', case=False, na=False), 'Categoria'] = 'Dividas'

    # Reclassificar Santander Sociedade de Crédito (financiamento aparelho US do João)
    # Confirmado por Iza no chat: "Será que não do aparelho de US? Ele foi Santander"
    df.loc[df['Descrição'].str.contains('SANTANDER SOCIEDADE', case=False, na=False), 'Categoria'] = 'Financiamento Aparelho US'

    df['Tipo_Despesa'] = df['Categoria'].apply(classificar_tipo_despesa)
    df['Categoria_Mae'] = df['Categoria'].apply(get_categoria_mae)

    df = gerar_projecao(df)
    return df


def gerar_projecao(df):
    todos_meses = sorted(df['Ano_Mes'].unique())
    # BUG FIX: usar mes ATUAL do calendario, NAO o ultimo do CSV
    # (CSV pode ter parcelas agendadas em meses futuros que nao sao "passado")
    mes_vigente = datetime.now().strftime('%Y-%m')
    # Considera "anteriores" so meses com dados REAIS (nao agendamentos futuros)
    meses_anteriores = [m for m in todos_meses if m < mes_vigente]
    ultimos_6m = meses_anteriores[-6:] if len(meses_anteriores) >= 6 else meses_anteriores
    df_base = df[df['Ano_Mes'].isin(ultimos_6m)]
    n = len(ultimos_6m)
    if n == 0:
        return df

    media_por_cat = df_base[df_base['Tipo'] == 'EXPENSE'].groupby('Categoria')['Valor_num'].sum() / n
    media_rec_cat = df_base[df_base['Tipo'] == 'INCOME'].groupby('Categoria')['Valor_num'].sum() / n

    # Meses futuros para projeção
    # Projetar APENAS meses verdadeiramente futuros (abril ja fechou - hoje 04/05/2026)
    meses_futuros = ['2026-05', '2026-06', '2026-07', '2026-08', '2026-09', '2026-10']

    # Para meses que já têm dados reais, calcular o que já foi gasto por categoria
    # Projeção = estimado - já gasto (só adiciona a diferença)
    gasto_real_por_mes_cat = {}
    rec_real_por_mes_cat = {}
    for mes in meses_futuros:
        df_mes_real = df[df['Ano_Mes'] == mes]
        if len(df_mes_real) > 0:
            gasto_real_por_mes_cat[mes] = df_mes_real[df_mes_real['Tipo'] == 'EXPENSE'].groupby('Categoria')['Valor_num'].sum().to_dict()
            rec_real_por_mes_cat[mes] = df_mes_real[df_mes_real['Tipo'] == 'INCOME'].groupby('Categoria')['Valor_num'].sum().to_dict()

    # Parcelas conhecidas do casal (das faturas)
    # Signature: R$ 1.347,60/mês até jun/26 (parcela 12/12)
    # BB consignado: R$ 1.886/mês até jun/28
    # Itaú Sob Medida: R$ 2.283/mês (já acabando jan/26, mas verificar)
    parcelas_conhecidas = {
        'CDC BB': {'valor': 3671.51, 'ate': '2026-12'},
        'Santander - Aparelho US (Joao)': {'valor': 2590, 'ate': '2026-12'},  # ate confirmar com Iza
    }

    rows = []
    for mes in meses_futuros:
        # Receitas: projeção - já recebido (RECEITAS EVENTUAIS NAO PROJETAM)
        for cat, val in media_rec_cat.items():
            # Pular categorias eventuais (ressarcimento governo, caucao apt, etc)
            if classificar_tipo_despesa(cat) == 'Eventual':
                continue
            ja_recebido = rec_real_por_mes_cat.get(mes, {}).get(cat, 0)
            restante = max(0, (val * 0.95) - ja_recebido)
            if restante <= 0:
                continue
            rows.append({
                'Data': f'01/{mes[5:7]}/{mes[:4]}',
                'Tipo': 'INCOME',
                'Valor': f'R$ {restante:,.2f}',
                'Valor_num': restante,
                'Descrição': f'[Projeção] {cat}',
                'Categoria': cat,
                'Conta': 'Projeção',
                'Tipo_Despesa': 'Outros',
                'Categoria_Mae': get_categoria_mae(cat),
                'Data_parsed': pd.to_datetime(f'{mes}-01'),
                'Ano_Mes': mes,
                'Recorrente': 'Não', 'Status': 'PROJECTED',
            })

        # Valores fixos manuais (corrige duplicatas do open finance)
        VALORES_FIXOS = {
            'Aluguel/Financiamento': 6500,   # Aluguel ~R$ 6.500
        }

        # Dívidas com data de término conhecida
        # Após o fim, o valor é zerado na projeção
        DIVIDAS_COM_FIM = {
            'Dividas': {
                # CDC BB R$3.671 + Santander R$2.590
                'ate_dez26': 3672,   # CDC BB - remover a partir de jan/27
            }
        }

        for cat, val in media_por_cat.items():
            # Eventuais não projetam
            if classificar_tipo_despesa(cat) == 'Eventual':
                valor_proj = 0
            else:
                valor_proj = VALORES_FIXOS.get(cat, val)

            # Ajustar dívidas: Signature acaba em jun/26
            if cat == 'Dividas' and mes > '2026-12':
                valor_proj = max(0, valor_proj - DIVIDAS_COM_FIM['Dividas']['ate_dez26'])

            # Subtrair o que já foi gasto neste mês (dados reais do CSV)
            ja_gasto = gasto_real_por_mes_cat.get(mes, {}).get(cat, 0)
            restante = max(0, valor_proj - ja_gasto)
            if restante <= 0:
                continue

            rows.append({
                'Data': f'01/{mes[5:7]}/{mes[:4]}',
                'Tipo': 'EXPENSE',
                'Valor': f'R$ {restante:,.2f}',
                'Valor_num': restante,
                'Descrição': f'[Projeção] {cat}' + (' (sem CDC BB)' if cat == 'Dividas' and mes > '2026-12' else ''),
                'Categoria': cat,
                'Conta': 'Projeção',
                'Tipo_Despesa': classificar_tipo_despesa(cat),
                'Categoria_Mae': get_categoria_mae(cat),
                'Data_parsed': pd.to_datetime(f'{mes}-01'),
                'Ano_Mes': mes,
                'Recorrente': 'Não', 'Status': 'PROJECTED',
            })

    if rows:
        df_proj = pd.DataFrame(rows)
        for col in df.columns:
            if col not in df_proj.columns:
                df_proj[col] = ''
        df = pd.concat([df, df_proj[df.columns]], ignore_index=True)

    return df


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 10px 0 6px 0;">
        <span style="font-size:26px; font-weight:900; color:#ffffff; letter-spacing:2px;">GW9</span>
        <span style="font-size:13px; font-weight:500; color:#a0b4f0; display:block; letter-spacing:3px; margin-top:-2px;">CAPITAL</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### :material/group: Iza & João")
    st.caption("Casal · Médica · Santa Catarina")
    st.caption(":material/support_agent: Assessora: Laysa Corrêa")

    st.markdown("---")

    if 'pagina' not in st.session_state:
        st.session_state.pagina = "mes"

    menu_items = [
        ("patrimonio", ":material/account_balance: Patrimônio"),
        ("mes", ":material/calendar_month: Mês a mês"),
        ("detalhe", ":material/query_stats: Detalhamento"),
        ("alertas", ":material/notifications: Alertas"),
    ]

    for key, label in menu_items:
        is_active = st.session_state.pagina == key
        btn_type = "primary" if is_active else "secondary"
        if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_type):
            st.session_state.pagina = key
            st.rerun()

    pagina = st.session_state.pagina

    st.markdown("---")

    # Pegar o CSV mais recente da pasta (padrao Izabella_transacoes_filtradas_*)
    pasta = os.path.dirname(__file__)
    csvs_planfi = sorted([f for f in os.listdir(pasta) if f.startswith('Izabella_transacoes_filtradas') and f.endswith('.csv')], reverse=True)
    if csvs_planfi:
        default_csv = os.path.join(pasta, csvs_planfi[0])
    else:
        default_csv = os.path.join(pasta, "transacoes_filtradas_2026-04-08_19-22_Planfi_2026.csv")
    uploaded = st.file_uploader(":material/upload_file: Carregar novo CSV", type=['csv'])

    if uploaded:
        df = load_data(uploaded_file=uploaded)
    else:
        df = load_data(file_path=default_csv)

    if df is None:
        st.error("Nenhum CSV encontrado.", icon="🔴")
        st.stop()

# ============================================================
# HEADER + CARD FUNCTION
# ============================================================
st.title(":material/account_balance_wallet: Finanças de vocês, Iza & João")


def card_html(bg, shadow, icon, label, value, extra=""):
    return f"""
    <div style="background:{bg}; border-radius:20px; padding:24px 18px;
         box-shadow:0 10px 30px {shadow}; color:white; margin-bottom:8px;
         min-height:200px; box-sizing:border-box;
         display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;">
      <div style="display:flex; align-items:center; gap:12px; justify-content:center; min-width:0; flex-wrap:wrap;">
        <div style="background:rgba(255,255,255,0.25); border-radius:50%;
             width:46px; height:46px; display:flex; align-items:center;
             justify-content:center; font-size:1.4rem; flex-shrink:0;">{icon}</div>
        <div style="min-width:0;">
          <div style="font-size:0.95rem; opacity:0.9; font-weight:600; letter-spacing:0.3px;">{label}</div>
          <div style="font-size:1.7rem; font-weight:800; line-height:1.15; letter-spacing:-0.5px;">{value}</div>
        </div>
      </div>
      {extra}
    </div>"""


meses_disponiveis = sorted(df['Ano_Mes'].unique())

# ============================================================
# PAGINA 0 - PATRIMONIO (foto do dinheiro deles ao longo do tempo)
# ============================================================
if pagina == "patrimonio":
    st.subheader(":material/account_balance: Patrimônio total — onde está o dinheiro de vocês?")
    st.caption("Foto do que vocês têm em cada conta ao longo do tempo. Esta é a verdade do que sobrou de fato.")

    # Saldos REAIS dos extratos (atualizar conforme novos extratos)
    # Use 0 quando nao tiver dado (ao inves de None) pra evitar NaN nos calculos
    # Pegar SEMPRE o ultimo saldo conhecido pra cada conta
    saldos = pd.DataFrame([
        # ordem: PJ Caixa, BB CC, Inter CC, Inter Investimentos, Inter PJ nova
        {"Data": "01/01/2026", "PJ Caixa": 71548, "BB CC": 2229, "Inter CC": 4943, "Inter Investimentos": 49000, "Inter PJ Nova": 0},
        {"Data": "31/01/2026", "PJ Caixa": 47059, "BB CC": 9454, "Inter CC": 6002, "Inter Investimentos": 71121, "Inter PJ Nova": 0},
        {"Data": "28/02/2026", "PJ Caixa": 68165, "BB CC": 7046, "Inter CC": 712, "Inter Investimentos": 80000, "Inter PJ Nova": 0},
        {"Data": "31/03/2026", "PJ Caixa": 34201, "BB CC": 13063, "Inter CC": 53, "Inter Investimentos": 95000, "Inter PJ Nova": 4840},
        # Abril: PJ Caixa so temos ate 09/04 (R$ 9.572). Inter PJ nova nao temos dado novo - usa o de 31/03
        {"Data": "30/04/2026", "PJ Caixa": 9572, "BB CC": 8624, "Inter CC": 471, "Inter Investimentos": 99693, "Inter PJ Nova": 4840},
    ])
    saldos["TOTAL"] = saldos[["PJ Caixa", "BB CC", "Inter CC", "Inter Investimentos", "Inter PJ Nova"]].sum(axis=1)

    # ───── CARDS GRANDES NO TOPO ─────
    inicio = saldos.iloc[0]
    atual = saldos.iloc[-1]
    var_total = atual["TOTAL"] - inicio["TOTAL"]
    var_inv = atual["Inter Investimentos"] - inicio["Inter Investimentos"]
    var_pj = atual["PJ Caixa"] - inicio["PJ Caixa"]
    var_cc = (atual["PJ Caixa"] + atual["BB CC"] + atual["Inter CC"]) - (inicio["PJ Caixa"] + inicio["BB CC"] + inicio["Inter CC"])

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown(card_html(
            "#0984e3", "rgba(9,132,227,0.35)",
            "💰", "Patrimônio HOJE",
            fmt_brl(atual["TOTAL"]),
            f'<div style="margin-top:14px; font-size:1rem;">Em janeiro: {fmt_brl(inicio["TOTAL"])}</div>'
        ), unsafe_allow_html=True)
    with col_b:
        cor = "#00b894" if var_total >= 0 else "#d63031"
        sombra = "rgba(0,184,148,0.35)" if var_total >= 0 else "rgba(214,48,49,0.35)"
        sinal = "+" if var_total >= 0 else ""
        st.markdown(card_html(
            cor, sombra,
            "📈" if var_total >= 0 else "📉",
            "Variação no ano",
            f'{sinal}{fmt_brl(var_total)}',
            f'<div style="margin-top:14px; font-size:1rem;">Em 4 meses</div>'
        ), unsafe_allow_html=True)
    with col_c:
        st.markdown(card_html(
            "#6c5ce7", "rgba(108,92,231,0.35)",
            "📊", "Reserva (CDB/LCI)",
            fmt_brl(atual["Inter Investimentos"]),
            f'<div style="margin-top:14px; font-size:1rem;">+{fmt_brl(var_inv)} (cresceu)</div>'
        ), unsafe_allow_html=True)

    st.markdown("")

    # ───── ALERTA EXPLICATIVO (HTML pra evitar markdown comer cifrão) ─────
    def esc(v):
        # Escapar cifrão pro markdown nao interpretar
        return fmt_brl(v).replace("$", "\\$")

    if var_total < 5000:
        st.markdown(
            f"""<div style="background:#ffe5e5; border-left:6px solid #d63031; border-radius:8px;
                 padding:14px 18px; margin:10px 0; color:#2d3436; font-size:0.95rem; line-height:1.6;">
            🔍 <b>A reserva CRESCEU {fmt_brl(var_inv)}, mas o patrimônio TOTAL variou {fmt_brl(var_total)}.</b><br>
            Isso significa que <b>a reserva não cresceu com dinheiro novo</b> — ela cresceu porque vocês
            <b>transferiram dinheiro da PJ pra investir</b>. O saldo da PJ Caixa caiu {fmt_brl(abs(var_pj))}
            no mesmo período. Foi mover dinheiro de bolso pra bolso.
            </div>""",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""<div style="background:#e6f9f2; border-left:6px solid #00b894; border-radius:8px;
                 padding:14px 18px; margin:10px 0; color:#2d3436; font-size:0.95rem;">
            📈 <b>Patrimônio total cresceu {fmt_brl(var_total)} no período</b> (incluindo a reserva).
            </div>""",
            unsafe_allow_html=True
        )

    # ───── GRAFICO DE EVOLUCAO ─────
    st.subheader(":material/show_chart: Evolução do patrimônio mês a mês")

    saldos_plot = saldos.copy()
    saldos_plot["Data_dt"] = pd.to_datetime(saldos_plot["Data"], format="%d/%m/%Y")

    fig_evol = go.Figure()
    cores_contas = {
        "Inter Investimentos": "#6c5ce7",
        "PJ Caixa": "#00b894",
        "BB CC": "#fdcb6e",
        "Inter CC": "#74b9ff",
        "Inter PJ Nova": "#fd79a8",
    }

    for conta in ["Inter Investimentos", "PJ Caixa", "BB CC", "Inter CC", "Inter PJ Nova"]:
        fig_evol.add_trace(go.Bar(
            name=conta,
            x=saldos_plot["Data"],
            y=saldos_plot[conta].fillna(0),
            marker_color=cores_contas[conta],
            text=[fmt_brl(v) if v and v > 1000 else "" for v in saldos_plot[conta].fillna(0)],
            textposition='inside',
            textfont=dict(color='white', size=12),
            hovertemplate='<b>%{fullData.name}</b><br>%{x}<br>R$ %{y:,.0f}<extra></extra>',
        ))

    # Linha de TOTAL no topo
    fig_evol.add_trace(go.Scatter(
        name="TOTAL",
        x=saldos_plot["Data"],
        y=saldos_plot["TOTAL"],
        mode="lines+markers+text",
        line=dict(color="#2d3436", width=4),
        marker=dict(size=14, color="#2d3436"),
        text=[fmt_brl(v) for v in saldos_plot["TOTAL"]],
        textposition="top center",
        textfont=dict(size=14, color="#2d3436", family="Inter"),
        hovertemplate='<b>TOTAL</b><br>%{x}<br>R$ %{y:,.0f}<extra></extra>',
    ))

    fig_evol.update_layout(
        barmode='stack',
        height=550,
        margin=dict(t=60, b=40, l=20, r=20),
        legend=dict(orientation='h', yanchor='bottom', y=-0.2, font=dict(size=13)),
        yaxis=dict(title="R$", tickformat=",.0f"),
        xaxis=dict(title=""),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(248,249,250,0.5)',
    )
    st.plotly_chart(fig_evol, use_container_width=True)

    # ───── TABELA DETALHADA ─────
    st.subheader(":material/table_view: Saldos detalhados por conta")

    saldos_show = saldos.copy()
    for c in ["PJ Caixa", "BB CC", "Inter CC", "Inter Investimentos", "Inter PJ Nova", "TOTAL"]:
        saldos_show[c] = saldos_show[c].apply(lambda v: fmt_brl(v) if pd.notna(v) else "—")

    st.dataframe(saldos_show, use_container_width=True, hide_index=True)

    # ───── COMPARATIVO INICIO vs FIM ─────
    st.subheader(":material/compare_arrows: Comparativo: Início vs Hoje")

    def fmt_var(v):
        sinal = "+" if v >= 0 else ""
        return f"{sinal}{fmt_brl(v)}"

    comp = pd.DataFrame([
        {"Conta": "🏥 PJ Caixa SP", "Início (jan)": fmt_brl(inicio["PJ Caixa"]),
         "Hoje (último saldo)": fmt_brl(atual["PJ Caixa"]) + (" *⚠️ saldo de 09/04*" if atual["PJ Caixa"] == 9572 else ""),
         "Variação": fmt_var(atual["PJ Caixa"] - inicio["PJ Caixa"])},
        {"Conta": "🏦 BB CC (João)", "Início (jan)": fmt_brl(inicio["BB CC"]),
         "Hoje (último saldo)": fmt_brl(atual["BB CC"]),
         "Variação": fmt_var(atual["BB CC"] - inicio["BB CC"])},
        {"Conta": "💜 Inter CC (Iza)", "Início (jan)": fmt_brl(inicio["Inter CC"]),
         "Hoje (último saldo)": fmt_brl(atual["Inter CC"]),
         "Variação": fmt_var(atual["Inter CC"] - inicio["Inter CC"])},
        {"Conta": "📊 Inter Investimentos", "Início (jan)": fmt_brl(inicio["Inter Investimentos"]),
         "Hoje (último saldo)": fmt_brl(atual["Inter Investimentos"]),
         "Variação": fmt_var(atual["Inter Investimentos"] - inicio["Inter Investimentos"])},
        {"Conta": "🆕 Inter PJ Nova (Porto Belo)", "Início (jan)": fmt_brl(inicio["Inter PJ Nova"]),
         "Hoje (último saldo)": fmt_brl(atual["Inter PJ Nova"]),
         "Variação": fmt_var(atual["Inter PJ Nova"] - inicio["Inter PJ Nova"])},
        {"Conta": "💰 TOTAL", "Início (jan)": fmt_brl(inicio["TOTAL"]),
         "Hoje (último saldo)": fmt_brl(atual["TOTAL"]),
         "Variação": fmt_var(var_total)},
    ])
    st.dataframe(comp, use_container_width=True, hide_index=True)

    # ───── A HISTORIA EM 3 PASSOS ─────
    st.subheader(":material/lightbulb: A história em 3 passos")

    col_h1, col_h2, col_h3 = st.columns(3)
    with col_h1:
        with st.container(border=True):
            st.markdown("### 1️⃣ A reserva CRESCEU ✅")
            st.markdown(f"**De {fmt_brl(inicio['Inter Investimentos'])} → {fmt_brl(atual['Inter Investimentos'])}**")
            st.markdown(f"<div style='font-size:1.8rem; font-weight:800; color:#00b894;'>+{fmt_brl(var_inv)}</div>", unsafe_allow_html=True)
            st.caption("Aportes em CDB e LCI no Inter (em 4 meses)")
    with col_h2:
        with st.container(border=True):
            st.markdown("### 2️⃣ A PJ ESVAZIOU ⚠️")
            st.markdown(f"**De {fmt_brl(inicio['PJ Caixa'])} → {fmt_brl(atual['PJ Caixa'])}**")
            cor_pj = "#d63031" if var_pj < 0 else "#00b894"
            sinal_pj = "" if var_pj < 0 else "+"
            st.markdown(f"<div style='font-size:1.8rem; font-weight:800; color:{cor_pj};'>{sinal_pj}{fmt_brl(var_pj)}</div>", unsafe_allow_html=True)
            st.caption("O saldo da empresa foi transferido pra investir")
    with col_h3:
        with st.container(border=True):
            st.markdown("### 3️⃣ Patrimônio TOTAL")
            st.markdown(f"**De {fmt_brl(inicio['TOTAL'])} → {fmt_brl(atual['TOTAL'])}**")
            cor_t = "#d63031" if var_total < 0 else ("#fdcb6e" if var_total < 5000 else "#00b894")
            sinal_t = "" if var_total < 0 else "+"
            st.markdown(f"<div style='font-size:1.8rem; font-weight:800; color:{cor_t};'>{sinal_t}{fmt_brl(var_total)}</div>", unsafe_allow_html=True)
            sub = "Líquido NEGATIVO" if var_total < 0 else ("(quase) sem mudança" if var_total < 5000 else "Crescimento real")
            st.caption(f"{sub} — foi reorganização, não geração de riqueza nova")

    st.info("""
    💡 **A leitura correta:** Vocês estão em uma fase de **reorganização patrimonial**.
    Tiraram dinheiro parado na PJ (que rendia 0%) e colocaram em CDB/LCI (que rende ~CDI).
    Isso é positivo para quem está construindo reserva. Mas **ainda não há geração líquida de riqueza**:
    o que entra é praticamente igual ao que sai. Para crescer, precisa abrir gap entre receita e despesa.
    """, icon="🎯")

    st.markdown("---")
    st.caption("📌 Saldos confirmados pelos extratos bancários (Caixa SP, BB, Inter). Atualize ao receber novos extratos.")


# ============================================================
# PAGINA 1 - MES A MES
# ============================================================
elif pagina == "mes":
    # Toggle: filtra apenas as LINHAS de projecao dentro do mes (mantem todos os meses)
    col_toggle, col_legenda = st.columns([1, 3])
    with col_toggle:
        ver_so_real = st.toggle("👁️ Esconder lançamentos projetados", value=False, key="toggle_real",
                                help="Esconde apenas as linhas marcadas como [Projeção]. Mantém todos os meses visíveis.")
    with col_legenda:
        if ver_so_real:
            st.caption("✅ Mostrando apenas dados reais (lançamentos com Conta='Projeção' escondidos)")
        else:
            st.caption("📊 Mostrando dados reais + projeção 🔮 (em meses futuros, projeção complementa o que falta)")

    # Filtrar DataFrame para esconder linhas projetadas (mantem todos os meses)
    if ver_so_real:
        df_view = df[df['Conta'] != 'Projeção']
    else:
        df_view = df

    # Todos os meses sempre visiveis no seletor
    meses_disponiveis = sorted(df_view['Ano_Mes'].unique())

    # Seletor de mês
    if 'idx_mes' not in st.session_state:
        mes_atual = datetime.now().strftime('%Y-%m')
        if mes_atual in meses_disponiveis:
            st.session_state.idx_mes = meses_disponiveis.index(mes_atual)
        else:
            meses_reais = [m for m in meses_disponiveis if m <= mes_atual]
            st.session_state.idx_mes = meses_disponiveis.index(meses_reais[-1]) if meses_reais else len(meses_disponiveis) - 1

    # Garantir que idx_mes está dentro dos meses
    if st.session_state.idx_mes >= len(meses_disponiveis):
        st.session_state.idx_mes = len(meses_disponiveis) - 1

    # Usar df_view daqui pra frente
    df = df_view

    col_espL, col_esq, col_mes_sel, col_dir, col_espR = st.columns([2, 0.3, 1.5, 0.3, 2])
    with col_esq:
        if st.button("◁", key="btn_esq", help="Mês anterior"):
            if st.session_state.idx_mes > 0:
                st.session_state.idx_mes -= 1
                st.rerun()
    with col_mes_sel:
        is_proj = meses_disponiveis[st.session_state.idx_mes] >= '2026-05'
        label_mes = mes_label_pt(meses_disponiveis[st.session_state.idx_mes])
        if is_proj:
            label_mes += " 🔮"
        st.markdown(
            f"<div style='text-align:center; font-size:1.1rem; font-weight:600; "
            f"padding:6px 16px; border:1.5px solid {'#6c5ce7' if is_proj else '#b2bec3'}; "
            f"border-radius:20px; background:{'#f0edff' if is_proj else 'white'}; white-space:nowrap;'>"
            f"{label_mes}</div>",
            unsafe_allow_html=True
        )
    with col_dir:
        if st.button("▷", key="btn_dir", help="Próximo mês"):
            if st.session_state.idx_mes < len(meses_disponiveis) - 1:
                st.session_state.idx_mes += 1
                st.rerun()

    mes_selecionado = meses_disponiveis[st.session_state.idx_mes]
    is_projecao = mes_selecionado >= '2026-05'
    df_mes = df[df['Ano_Mes'] == mes_selecionado]
    receitas_mes = df_mes[df_mes['Tipo'] == 'INCOME']
    despesas_mes = df_mes[df_mes['Tipo'] == 'EXPENSE']
    investimentos_mes = df_mes[df_mes['Tipo'] == 'INVESTMENT']
    entrou = receitas_mes['Valor_num'].sum()
    saiu = despesas_mes['Valor_num'].sum()
    investido = investimentos_mes['Valor_num'].sum()
    saldo_mes = entrou - saiu - investido

    if is_projecao:
        st.info("**Projeção** — valores estimados baseados no padrão de consumo dos últimos 6 meses", icon="🔮")

    desp_fixas_mes = despesas_mes[despesas_mes['Tipo_Despesa'] == 'Essencial']['Valor_num'].sum()
    desp_var_mes = despesas_mes[despesas_mes['Tipo_Despesa'] == 'Não Essencial']['Valor_num'].sum()
    desp_event_mes = despesas_mes[despesas_mes['Tipo_Despesa'] == 'Eventual']['Valor_num'].sum()
    desp_outros_mes = saiu - desp_fixas_mes - desp_var_mes - desp_event_mes

    # 5 Cards: Entrou | Saiu (com sub) | Sobra Operacional | Investido | Saldo Final
    sobra_operacional = entrou - saiu  # antes de descontar investimento

    # Card Saldo Operacional (entrada - saida sem investimento)
    op_bg = "#00b894" if sobra_operacional >= 0 else "#d63031"
    op_shadow = "rgba(0,184,148,0.35)" if sobra_operacional >= 0 else "rgba(214,48,49,0.35)"
    op_label = "Sobra Operacional" if sobra_operacional >= 0 else "Déficit Operacional"
    op_icon = "💵" if sobra_operacional >= 0 else "⚠️"

    # Card Saldo Final (depois de investimento)
    bal_bg = "#00b894" if saldo_mes >= 0 else "#d63031"
    bal_shadow = "rgba(0,184,148,0.35)" if saldo_mes >= 0 else "rgba(214,48,49,0.35)"
    bal_label = "Sobrou" if saldo_mes >= 0 else "Faltou"
    bal_icon = "↑" if saldo_mes >= 0 else "↓"

    # Layout responsivo: cards em flex-wrap. Saidas ocupa 2x no desktop, full no mobile.
    inv_card = card_html("#6c5ce7", "rgba(108,92,231,0.35)", "📊", "Investido", fmt_brl(investido)) if investido > 0 \
               else card_html("#b2bec3", "rgba(178,190,195,0.2)", "📊", "Investido", "R$ 0")

    op_extra = '<div style="margin-top:14px; font-size:0.85rem; opacity:0.9;">Entrada − Saída<br><i>(antes de investir)</i></div>'
    bal_extra = '<div style="margin-top:14px; font-size:0.85rem; opacity:0.9;"><i>(depois de investir)</i></div>'

    st.markdown(f"""
    <div style="display:flex; flex-wrap:wrap; gap:12px; margin-bottom:24px;">
      <div style="flex:1 1 140px;">{card_html("#00b894", "rgba(0,184,148,0.35)", "↑", "Entradas", fmt_brl(entrou))}</div>
      <div style="flex:2 1 300px;">
        <div style="background:#e17055; border-radius:20px; padding:22px 22px;
             box-shadow:0 10px 30px rgba(225,112,85,0.35); color:white; margin-bottom:8px;
             min-height:200px; box-sizing:border-box;
             display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;">
          <div style="display:flex; align-items:center; gap:14px; justify-content:center; flex-wrap:wrap;">
            <div style="background:rgba(255,255,255,0.25); border-radius:50%;
                 width:50px; height:50px; display:flex; align-items:center;
                 justify-content:center; font-size:1.5rem; flex-shrink:0;">↓</div>
            <div>
              <div style="font-size:1.05rem; opacity:0.9; font-weight:600; letter-spacing:0.3px;">Saídas</div>
              <div style="font-size:2rem; font-weight:800; line-height:1.1; letter-spacing:-0.5px;">{fmt_brl(saiu)}</div>
            </div>
          </div>
          <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:18px; width:100%;">
            <div style="flex:1 1 80px; background:rgba(255,255,255,0.22); border-radius:12px; padding:12px 6px; text-align:center; min-width:0;">
              <div style="font-size:0.78rem; opacity:0.95; margin-bottom:6px; font-weight:600;">🔒 Essencial</div>
              <div style="font-size:1.1rem; font-weight:800; line-height:1.1;">{fmt_brl(desp_fixas_mes)}</div>
            </div>
            <div style="flex:1 1 80px; background:rgba(255,255,255,0.22); border-radius:12px; padding:12px 6px; text-align:center; min-width:0;">
              <div style="font-size:0.78rem; opacity:0.95; margin-bottom:6px; font-weight:600;">🔄 Não-Essen.</div>
              <div style="font-size:1.1rem; font-weight:800; line-height:1.1;">{fmt_brl(desp_var_mes)}</div>
            </div>
            <div style="flex:1 1 80px; background:rgba(255,255,255,0.22); border-radius:12px; padding:12px 6px; text-align:center; min-width:0;">
              <div style="font-size:0.78rem; opacity:0.95; margin-bottom:6px; font-weight:600;">📦 Eventual</div>
              <div style="font-size:1.1rem; font-weight:800; line-height:1.1;">{fmt_brl(desp_event_mes)}</div>
            </div>
            <div style="flex:1 1 80px; background:rgba(255,255,255,0.22); border-radius:12px; padding:12px 6px; text-align:center; min-width:0;">
              <div style="font-size:0.78rem; opacity:0.95; margin-bottom:6px; font-weight:600;">❓ Outros</div>
              <div style="font-size:1.1rem; font-weight:800; line-height:1.1;">{fmt_brl(desp_outros_mes)}</div>
            </div>
          </div>
        </div>
      </div>
      <div style="flex:1 1 140px;">{card_html(op_bg, op_shadow, op_icon, op_label, fmt_brl(abs(sobra_operacional)), op_extra)}</div>
      <div style="flex:1 1 130px;">{inv_card}</div>
      <div style="flex:1 1 140px;">{card_html(bal_bg, bal_shadow, bal_icon, bal_label, fmt_brl(abs(saldo_mes)), bal_extra)}</div>
    </div>
    """, unsafe_allow_html=True)

    # Alerta sem categoria / A Categorizar
    a_cat = df_mes[df_mes['Categoria'].isin(['A Categorizar', 'Sem Categoria'])]
    if len(a_cat) > 0:
        total_a_cat = a_cat['Valor_num'].sum()
        st.markdown(
            f"""<div style="background:#FFD600; color:#1a1a1a; border-radius:12px;
            padding:14px 20px; font-size:1rem; font-weight:700;
            border-left:6px solid #e6c000; margin-bottom:10px;">
            ⚠️ {len(a_cat)} transações a categorizar ({fmt_brl(total_a_cat)}) — categorize no Planfi!
            </div>""",
            unsafe_allow_html=True
        )

    if 'filtro_cat_pizza' not in st.session_state:
        st.session_state.filtro_cat_pizza = None

    col_desp, col_rec = st.columns(2)

    with col_desp:
        with st.container(border=True):
            st.subheader(":material/pie_chart: Pra onde foi o dinheiro")

            desp_cat = despesas_mes.groupby('Categoria_Mae')['Valor_num'].sum().sort_values(ascending=False)
            # Destacar A Categorizar
            if 'Outros' in desp_cat.index:
                outros_val = desp_cat.get('Outros', 0)
                if outros_val > 0:
                    desp_cat = desp_cat.rename(index={'Outros': '⚠️ A Categorizar'})
            total_desp = desp_cat.sum()

            if total_desp > 0:
                desp_pct = desp_cat / total_desp * 100
                # Threshold mais baixo (1.5%) para mostrar mais categorias separadamente
                principais = desp_pct[desp_pct >= 1.5]
                outros = desp_pct[desp_pct < 1.5]

                valores_pizza = list(desp_cat[principais.index].values)
                nomes_pizza = list(principais.index)
                st.session_state.pizza_cats_principais = list(principais.index)

                if len(outros) > 0:
                    valores_pizza.append(desp_cat[outros.index].sum())
                    nomes_pizza.append(f'Outros ({len(outros)} cat.)')

                cores = ['#6c5ce7', '#00b894', '#fd79a8', '#fdcb6e', '#e17055',
                         '#74b9ff', '#a29bfe', '#55efc4', '#fab1a0', '#00cec9',
                         '#b2bec3', '#636e72', '#e84393', '#0984e3', '#dfe6e9']

                cores_pizza = []
                pull_pizza = []
                for i, nome in enumerate(nomes_pizza):
                    if '⚠️' in nome:
                        cores_pizza.append('#FFD600')
                        pull_pizza.append(0.12)
                    else:
                        cores_pizza.append(cores[i % len(cores)])
                        pull_pizza.append(0)

                fig_pizza = go.Figure()
                fig_pizza.add_trace(go.Pie(
                    labels=nomes_pizza,
                    values=valores_pizza,
                    hole=0.42,
                    texttemplate='<b>%{label}</b><br>%{customdata}',
                    textposition='outside',
                    textfont=dict(size=13, color='#2d3436'),
                    marker=dict(colors=cores_pizza, line=dict(width=2, color='white')),
                    pull=pull_pizza,
                    customdata=[fmt_brl(v) for v in valores_pizza],
                    hovertemplate='<b>%{label}</b><br>%{percent:.1%}<br>%{customdata}<extra></extra>',
                    showlegend=False,
                ))

                fig_pizza.add_trace(go.Pie(
                    labels=nomes_pizza,
                    values=valores_pizza,
                    hole=0.42,
                    texttemplate='<b>%{percent:.1%}</b>',
                    textposition='inside',
                    insidetextorientation='horizontal',
                    textfont=dict(size=18, color='#2d3436'),
                    marker=dict(colors=['rgba(0,0,0,0)'] * len(nomes_pizza), line=dict(width=0, color='rgba(0,0,0,0)')),
                    hoverinfo='skip',
                    showlegend=False,
                ))

                fig_pizza.update_layout(
                    height=560,
                    margin=dict(t=70, b=70, l=80, r=80),
                    showlegend=False,
                    uniformtext=dict(minsize=11, mode='hide'),
                    annotations=[dict(text=f'<b>{fmt_brl(saiu)}</b>', x=0.5, y=0.5, font_size=18, showarrow=False)],
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                )

                st.plotly_chart(fig_pizza, use_container_width=True)

                # Botões clicáveis por categoria (abaixo da pizza)
                st.caption("Clique para filtrar os lançamentos:")
                n_cols = min(4, len(nomes_pizza))
                btn_cols = st.columns(n_cols)
                for i, nome in enumerate(nomes_pizza):
                    cor_btn = cores_pizza[i]
                    with btn_cols[i % n_cols]:
                        is_active = st.session_state.filtro_cat_pizza == nome
                        btn_label = f"{'✅ ' if is_active else ''}{nome}"
                        if st.button(btn_label, key=f"btn_cat_{i}", use_container_width=True):
                            if is_active:
                                st.session_state.filtro_cat_pizza = None
                                st.session_state.filtro_cat_col = []
                                st.session_state.filtro_tipo_mes = "Todos"
                            else:
                                st.session_state.filtro_cat_pizza = nome
                                st.session_state.filtro_fixvar_mes = "Todos"
                                if 'Outros' not in nome:
                                    st.session_state.filtro_cat_col = [nome]
                                else:
                                    st.session_state.filtro_cat_col = []
                                st.session_state.filtro_tipo_mes = "Saída"
                            st.rerun()

                if st.session_state.filtro_cat_pizza:
                    if st.button("❌ Limpar filtro", key="limpar_pizza", use_container_width=True):
                        st.session_state.filtro_cat_pizza = None
                        st.session_state.filtro_cat_col = []
                        st.session_state.filtro_tipo_mes = "Todos"
                        st.rerun()
            else:
                st.caption("Sem despesas neste mês")

    with col_rec:
        with st.container(border=True):
            st.subheader(":material/payments: De onde veio o dinheiro")

            # Agrupar receitas pequenas em "Outros" + corrigir typo Váriável -> Variável
            receitas_norm = receitas_mes.copy()
            receitas_norm['Categoria'] = receitas_norm['Categoria'].str.replace('Váriável', 'Variável', regex=False)
            rec_cat_all = receitas_norm.groupby('Categoria')['Valor_num'].sum().sort_values(ascending=False)
            total_rec_tmp = rec_cat_all.sum()
            if total_rec_tmp > 0:
                rec_pct = rec_cat_all / total_rec_tmp * 100
                rec_principais = rec_cat_all[rec_pct >= 5]
                rec_outros = rec_cat_all[rec_pct < 5]
                if len(rec_outros) > 0:
                    rec_principais['Outros'] = rec_outros.sum()
                rec_cat = rec_principais.sort_values(ascending=True)
            else:
                rec_cat = rec_cat_all

            if len(rec_cat) > 0:
                cores_rec = ['#00b894', '#55efc4', '#81ecec', '#74b9ff',
                             '#a29bfe', '#6c5ce7', '#dfe6e9', '#b2bec3',
                             '#fdcb6e', '#fab1a0', '#e17055']

                total_rec = rec_cat.sum()
                tick_labels = [f"<b>{cat}</b><br>{v/total_rec*100:.1f}%" for cat, v in zip(rec_cat.index, rec_cat.values)]

                fig_rec = go.Figure(data=[go.Bar(
                    y=tick_labels,
                    x=rec_cat.values,
                    orientation='h',
                    marker_color=cores_rec[:len(rec_cat)],
                    text=[f"<b>{fmt_brl(v)}</b>" for v in rec_cat.values],
                    textposition='outside',
                    textfont=dict(size=18, color='#2d3436'),
                    hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>',
                    customdata=[[cat, fmt_brl(v)] for cat, v in zip(rec_cat.index, rec_cat.values)],
                )])

                max_val = rec_cat.max()
                fig_rec.update_layout(
                    height=420,
                    margin=dict(t=10, b=20, l=10, r=10),
                    xaxis=dict(range=[0, max_val * 2.4], visible=False),
                    yaxis=dict(tickfont=dict(size=16, color='#2d3436')),
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                )
                st.plotly_chart(fig_rec, use_container_width=True)
            else:
                st.caption("Sem receitas neste mês")

    # Tabela de lançamentos
    st.subheader(f":material/receipt_long: Lançamentos de {mes_label_pt(mes_selecionado)}")

    df_tabela_mes = df_mes[['Data', 'Tipo', 'Valor_num', 'Descrição', 'Categoria', 'Categoria_Mae', 'Tipo_Despesa', 'Conta']].copy()
    df_tabela_mes['Tipo_label'] = df_tabela_mes['Tipo'].map({'INCOME': 'Entrada', 'EXPENSE': 'Saída'})
    df_tabela_mes['Fixo_Var'] = df_tabela_mes.apply(
        lambda r: '' if r['Tipo'] == 'INCOME' else (
            '🔒 Essencial' if r['Tipo_Despesa'] == 'Essencial' else (
            '🔄 Não Essencial' if r['Tipo_Despesa'] == 'Não Essencial' else (
            '📦 Eventual' if r['Tipo_Despesa'] == 'Eventual' else '❓ Outros'))),
        axis=1
    )

    fc1, fc2, fc3, fc4, fc5 = st.columns(5)
    with fc1:
        filtro_tipo = st.selectbox("Tipo:", ["Todos", "Entrada", "Saída"], key="filtro_tipo_mes")
    with fc2:
        filtro_fixvar = st.selectbox("Fixo/Var:", ["Todos", "🔒 Essencial", "🔄 Não Essencial", "📦 Eventual", "❓ Outros"], index=st.session_state.get("filtro_fixvar_idx", 0), key="filtro_fixvar_mes")
    with fc3:
        cats_disponiveis = sorted(df_tabela_mes['Categoria_Mae'].unique())
        default_cat = []
        if st.session_state.filtro_cat_pizza and st.session_state.filtro_cat_pizza in cats_disponiveis:
            default_cat = [st.session_state.filtro_cat_pizza]
        filtro_cat = st.multiselect("Categoria:", cats_disponiveis, default=default_cat, key="filtro_cat_col")
    with fc4:
        contas_mes = sorted(df_tabela_mes['Conta'].unique())
        filtro_conta = st.multiselect("Conta:", contas_mes, key="filtro_conta_mes")
    with fc5:
        busca_desc = st.text_input("Buscar:", key="busca_desc_mes", placeholder="Descrição...")

    df_show = df_tabela_mes.copy()
    if filtro_tipo == "Entrada":
        df_show = df_show[df_show['Tipo'] == 'INCOME']
    elif filtro_tipo == "Saída":
        df_show = df_show[df_show['Tipo'] == 'EXPENSE']
    if filtro_fixvar != "Todos":
        df_show = df_show[df_show['Fixo_Var'] == filtro_fixvar]
    if filtro_cat:
        df_show = df_show[df_show['Categoria_Mae'].isin(filtro_cat)]
    # Se pizza clicada em "Outros (X cat.)", filtrar categorias pequenas que foram agrupadas
    elif st.session_state.filtro_cat_pizza and 'Outros' in str(st.session_state.filtro_cat_pizza) and 'cat.' in str(st.session_state.filtro_cat_pizza):
        cats_principais = st.session_state.get('pizza_cats_principais', [])
        df_show = df_show[(df_show['Tipo'] == 'EXPENSE') & (~df_show['Categoria_Mae'].isin(cats_principais))]
    if filtro_conta:
        df_show = df_show[df_show['Conta'].isin(filtro_conta)]
    if busca_desc:
        df_show = df_show[df_show['Descrição'].str.contains(busca_desc, case=False, na=False)]

    # Calcular totais por tipo (entrada vs saída)
    entradas_filt = df_show[df_show['Tipo'] == 'INCOME']['Valor_num'].sum()
    saidas_filt = df_show[df_show['Tipo'] == 'EXPENSE']['Valor_num'].sum()
    saldo_filt = entradas_filt - saidas_filt

    if entradas_filt > 0 and saidas_filt > 0:
        # Tem os dois tipos: mostrar entrada, saida e saldo liquido
        cor_saldo = "#00b894" if saldo_filt >= 0 else "#d63031"
        sinal = "+" if saldo_filt >= 0 else ""
        st.markdown(
            f"<div style='padding:8px 0; font-size:0.95rem;'>"
            f"<b>{len(df_show)} lançamentos</b> · "
            f"<span style='color:#00b894;'>↑ Entradas: <b>{fmt_brl(entradas_filt)}</b></span> · "
            f"<span style='color:#e17055;'>↓ Saídas: <b>{fmt_brl(saidas_filt)}</b></span> · "
            f"<span style='color:{cor_saldo}; font-weight:700;'>= Saldo: {sinal}{fmt_brl(saldo_filt)}</span>"
            f"</div>",
            unsafe_allow_html=True
        )
    elif entradas_filt > 0:
        st.caption(f"{len(df_show)} lançamentos · ↑ Total entradas: **{fmt_brl(entradas_filt)}**")
    elif saidas_filt > 0:
        st.caption(f"{len(df_show)} lançamentos · ↓ Total saídas: **{fmt_brl(saidas_filt)}**")
    else:
        st.caption(f"{len(df_show)} lançamentos")

    st.dataframe(
        df_show[['Data', 'Tipo_label', 'Fixo_Var', 'Valor_num', 'Descrição', 'Categoria', 'Conta']].sort_values('Data', ascending=False),
        use_container_width=True, height=420, hide_index=True,
        column_config={
            "Data": st.column_config.TextColumn("Data", width="small"),
            "Tipo_label": st.column_config.TextColumn("Tipo", width="small"),
            "Fixo_Var": st.column_config.TextColumn("Fixo/Var", width="small"),
            "Valor_num": st.column_config.NumberColumn("Valor", format="R$ %.2f", width="medium"),
            "Descrição": st.column_config.TextColumn("Descrição", width="large"),
            "Categoria": st.column_config.TextColumn("Categoria", width="medium"),
            "Conta": st.column_config.TextColumn("Conta", width="medium"),
        }
    )


# ============================================================
# PAGINA 2 - DETALHAMENTO (VISÃO DO ANO)
# ============================================================
elif pagina == "detalhe":
    # Toggle: filtra apenas as LINHAS de projecao dentro do mes (mantem todos os meses)
    col_t1, col_t2 = st.columns([1, 3])
    with col_t1:
        esconder_proj = st.toggle("👁️ Esconder lançamentos projetados", value=False, key="toggle_proj_det",
                                   help="Esconde apenas as linhas marcadas como [Projeção]. Mantém todos os meses visíveis.")
    with col_t2:
        if esconder_proj:
            st.caption("✅ Mostrando apenas dados reais")
        else:
            st.caption("📊 Mostrando dados reais + projeção 🔮")

    # Filtrar DataFrame para esconder linhas projetadas (mantem todos os meses)
    if esconder_proj:
        df_periodo = df[df['Conta'] != 'Projeção']
    else:
        df_periodo = df

    meses_uso = sorted(df_periodo['Ano_Mes'].unique())

    if not meses_uso:
        st.warning("Nenhum mês disponível.")
        st.stop()

    # Filtro de período
    todos_meses_labels = [mes_label_curto(m) for m in meses_uso]
    f1, f2 = st.columns(2)
    with f1:
        mes_ini_label = st.selectbox("De:", todos_meses_labels, index=0, key="detalhe_ini")
    with f2:
        mes_fim_label = st.selectbox("Até:", todos_meses_labels, index=len(meses_uso)-1, key="detalhe_fim")

    idx_ini = todos_meses_labels.index(mes_ini_label)
    idx_fim = todos_meses_labels.index(mes_fim_label)
    if idx_ini > idx_fim:
        idx_ini, idx_fim = idx_fim, idx_ini
    meses_filtrados = meses_uso[idx_ini:idx_fim+1]
    df_det = df_periodo[df_periodo['Ano_Mes'].isin(meses_filtrados)]

    # Cards acumulados
    periodo_txt = f"{mes_label_curto(meses_filtrados[0])} a {mes_label_curto(meses_filtrados[-1])}"
    st.caption(f":material/date_range: Período: {periodo_txt} · {len(df_det):,} transações")

    total_receita = df_det[df_det['Tipo'] == 'INCOME']['Valor_num'].sum()
    total_despesa = df_det[df_det['Tipo'] == 'EXPENSE']['Valor_num'].sum()
    total_investido = df_det[df_det['Tipo'] == 'INVESTMENT']['Valor_num'].sum()
    balanco_total = total_receita - total_despesa - total_investido

    bal_bg_d = "#00b894" if balanco_total >= 0 else "#d63031"
    bal_shadow_d = "rgba(0,184,148,0.35)" if balanco_total >= 0 else "rgba(214,48,49,0.35)"
    bal_icon_d = "↑" if balanco_total >= 0 else "↓"
    bal_label_d = "Sobrou (+)" if balanco_total >= 0 else "Faltou (−)"

    cd1, cd2, cd3, cd4 = st.columns(4)
    with cd1:
        st.markdown(card_html("#00b894", "rgba(0,184,148,0.35)", "↑", "Receita Total", fmt_brl(total_receita)), unsafe_allow_html=True)
    with cd2:
        st.markdown(card_html("#e17055", "rgba(225,112,85,0.35)", "↓", "Despesa Total", fmt_brl(total_despesa)), unsafe_allow_html=True)
    with cd3:
        st.markdown(card_html("#6c5ce7", "rgba(108,92,231,0.35)", "📊", "Investido", fmt_brl(total_investido)), unsafe_allow_html=True)
    with cd4:
        st.markdown(card_html(bal_bg_d, bal_shadow_d, bal_icon_d, bal_label_d, fmt_brl(abs(balanco_total))), unsafe_allow_html=True)

    st.subheader(":material/query_stats: Sobrou ou faltou em cada mês?")

    resumo_mensal = df_det.groupby(['Ano_Mes', 'Tipo'])['Valor_num'].sum().unstack(fill_value=0)
    if 'INCOME' not in resumo_mensal.columns:
        resumo_mensal['INCOME'] = 0
    if 'EXPENSE' not in resumo_mensal.columns:
        resumo_mensal['EXPENSE'] = 0
    if 'INVESTMENT' not in resumo_mensal.columns:
        resumo_mensal['INVESTMENT'] = 0
    resumo_mensal['Saldo'] = resumo_mensal['INCOME'] - resumo_mensal['EXPENSE'] - resumo_mensal['INVESTMENT']
    resumo_mensal = resumo_mensal.sort_index()

    meses_hist = resumo_mensal.index.tolist()
    meses_hist_label = [mes_label_curto(m) for m in meses_hist]
    cores_saldo = ['#00b894' if v >= 0 else '#e17055' for v in resumo_mensal['Saldo']]

    with st.container(border=True):
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Bar(
            x=meses_hist_label,
            y=resumo_mensal['Saldo'],
            marker_color=cores_saldo,
            text=[f'<b>{fmt_brl(v)}</b>' for v in resumo_mensal['Saldo']],
            textposition='outside',
            textfont=dict(size=16, color='#2d3436'),
            hovertemplate='<b>%{x}</b><br>%{customdata}<extra></extra>',
            customdata=[fmt_brl(v) for v in resumo_mensal['Saldo']],
        ))
        fig_hist.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

        # Linha separando passado (real)/futuro (projecao) - Abril ja eh real
        mes_corte = '2026-04'
        if mes_corte in meses_hist:
            idx_corte = meses_hist.index(mes_corte)
            fig_hist.add_vline(x=idx_corte + 0.5, line_dash="dot", line_color="#6c5ce7", line_width=2, opacity=0.8)
            y_max = resumo_mensal['Saldo'].abs().max() * 0.85
            fig_hist.add_annotation(x=idx_corte - 0.6, y=y_max, text="◀ <b>Real</b>", showarrow=False, font=dict(size=18, color="#6c5ce7"), xanchor="right")
            fig_hist.add_annotation(x=idx_corte + 0.6, y=y_max, text="<b>Projeção</b> ▶", showarrow=False, font=dict(size=18, color="#6c5ce7"), xanchor="left")

        fig_hist.update_layout(
            height=360, margin=dict(t=40, b=20),
            yaxis_visible=False, showlegend=False,
            xaxis=dict(tickfont=dict(size=16, color='#2d3436')),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with st.container(border=True):
        st.subheader(":material/lock: Essencial vs Não Essencial vs Eventual")
        desp_all = df_det[df['Tipo'] == 'EXPENSE']
        desp_tipo = desp_all.groupby(['Ano_Mes', 'Tipo_Despesa'])['Valor_num'].sum().reset_index()
        desp_tipo['Mês'] = desp_tipo['Ano_Mes'].apply(mes_label_curto)

        COR_ESSENCIAL = '#5c6bc0'
        COR_NAO_ESSENCIAL = '#ef6c00'
        COR_EVENTUAL = '#e84393'
        COR_OUTROS = '#ffd54f'

        meses_ord = [mes_label_curto(m) for m in sorted(desp_tipo['Ano_Mes'].unique())]

        fig_fixvar = go.Figure()
        for tipo, cor in [('Essencial', COR_ESSENCIAL), ('Não Essencial', COR_NAO_ESSENCIAL), ('Eventual', COR_EVENTUAL), ('Outros', COR_OUTROS)]:
            d = desp_tipo[desp_tipo['Tipo_Despesa'] == tipo]
            if d.empty:
                continue
            fig_fixvar.add_trace(go.Bar(
                x=d['Mês'], y=d['Valor_num'],
                name=tipo, marker_color=cor,
                text=[f'<b>{v/1000:.0f}k</b>' for v in d['Valor_num']],
                textposition='inside', insidetextanchor='middle',
                textfont=dict(size=16, color='#2d3436'),
            ))

        fig_fixvar.update_layout(
            barmode='stack', height=420, margin=dict(t=10, b=10),
            yaxis=dict(tickformat=",.0f", tickfont=dict(size=16)),
            xaxis=dict(tickfont=dict(size=16), categoryorder='array', categoryarray=meses_ord),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, font=dict(size=16)),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_fixvar, use_container_width=True)

    with st.container(border=True):
        st.subheader(":material/leaderboard: Onde vocês mais gastam")
        desp_reais = df_det[df_det['Tipo'] == 'EXPENSE']
        n_meses_reais = max(desp_reais['Ano_Mes'].nunique(), 1)
        top_mae = desp_reais.groupby('Categoria_Mae')['Valor_num'].sum().sort_values(ascending=True).tail(10)

        fig_top = go.Figure(data=[go.Bar(
            y=top_mae.index, x=top_mae.values, orientation='h',
            marker_color=['#6c5ce7', '#00b894', '#fd79a8', '#fdcb6e', '#e17055',
                          '#74b9ff', '#a29bfe', '#55efc4', '#fab1a0', '#00cec9'][:len(top_mae)],
            text=[f'<b>{fmt_brl(v)}</b>  ({fmt_brl(v/n_meses_reais)}/mês)' for v in top_mae.values],
            textposition='outside', textfont=dict(size=17, color='#2d3436'),
        )])
        fig_top.update_layout(
            height=420, margin=dict(t=10, r=20, l=10),
            xaxis=dict(visible=False, range=[0, top_mae.max() * 1.6]),
            yaxis=dict(tickfont=dict(size=17)), showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_top, use_container_width=True)

    # Projeção
    st.subheader(":material/auto_graph: Projeção dos próximos meses")
    st.caption("Baseado na média de Set/25 a Fev/26 (últimos 6 meses reais)")

    meses_reais_proj = sorted([m for m in df['Ano_Mes'].unique() if m < '2026-05'])
    meses_proj = ['2026-05', '2026-06', '2026-07', '2026-08', '2026-09']
    ultimos_6m_det = meses_reais_proj[-6:] if len(meses_reais_proj) >= 6 else meses_reais_proj
    df_base_det = df[df['Ano_Mes'].isin(ultimos_6m_det)]

    rec_media = df_base_det[df_base_det['Tipo'] == 'INCOME'].groupby('Ano_Mes')['Valor_num'].sum().mean()
    desp_media = df_base_det[df_base_det['Tipo'] == 'EXPENSE'].groupby('Ano_Mes')['Valor_num'].sum().mean()

    # Dívidas e parcelas conhecidas (Notion + faturas)
    dados_proj = []
    for mes, label in [('2026-04', 'Abr/26'), ('2026-05', 'Mai/26'), ('2026-06', 'Jun/26'),
                        ('2026-07', 'Jul/26'), ('2026-08', 'Ago/26'), ('2026-09', 'Set/26')]:
        rec = rec_media * 0.95
        desp = desp_media

        # Parcelas de cartão (das faturas de março)
        # BB: SgGrifeBourbo 3/10 R$153, Mercadopago 2x ~R$55, SuncoastUSA 1/10 R$1.356, Anuidade 6/12 R$83
        parc_bb = 153.50 + 24.85 + 29.98 + 83.00  # acabam ~jun/26
        parc_bb_suncoast = 1356.24  # acaba ~dez/26 (9 restantes)
        # Casas Bahia 2x R$393 (acaba ~jul/26)
        parc_casas_bahia = 392.99 if mes <= '2026-07' else 0
        # Patricia Leite R$157 (acaba ~dez/26)
        parc_patricia = 157.00
        # Hoteis.com R$1.366 (acaba ~mai/26)
        parc_hotel = 1365.56 if mes <= '2026-04' else 0  # 02/04, acaba mai/26

        # Signature: R$ 1.348/mês (acaba jun/26)
        sig = 1347.60 if mes <= '2026-06' else 0
        # BB consignado: R$ 1.886/mês (até jun/28)
        bb = 1886

        # Alívio após fim das parcelas
        alivio_sig = 1348 if mes > '2026-06' else 0
        saldo = rec - desp + alivio_sig

        dados_proj.append({
            'Mês': label,
            'Entra': rec, 'Sai': desp - alivio_sig,
            'Sobra': saldo,
            'Signature': f'R$ {sig:,.0f}' if sig > 0 else 'Quitado ✅',
            'BB Consig.': f'R$ {bb:,.0f}',
            'Parcelas cartão': f'R$ {parc_bb + parc_bb_suncoast + parc_casas_bahia + parc_patricia + parc_hotel:,.0f}',
        })

    df_proj = pd.DataFrame(dados_proj)
    st.dataframe(
        df_proj, use_container_width=True, hide_index=True,
        column_config={
            "Mês": st.column_config.TextColumn("Mês", width="small"),
            "Entra": st.column_config.NumberColumn("Entra", format="R$ %.0f"),
            "Sai": st.column_config.NumberColumn("Sai", format="R$ %.0f"),
            "Sobra": st.column_config.NumberColumn("Sobra", format="R$ %.0f"),
            "Signature": st.column_config.TextColumn("Parc. Signature"),
            "BB Consig.": st.column_config.TextColumn("BB Consignado"),
            "Parcelas cartão": st.column_config.TextColumn("Parcelas cartão"),
        }
    )

    # Gráfico: Parcelas e Dívidas mês a mês
    st.subheader(":material/credit_card: Parcelas e dívidas — mês a mês")
    st.caption("Quanto vocês pagam por mês em parcelas de cartão + empréstimos")

    meses_timeline = ['Abr/26', 'Mai/26', 'Jun/26', 'Jul/26', 'Ago/26', 'Set/26',
                      'Out/26', 'Nov/26', 'Dez/26', 'Jan/27', 'Fev/27', 'Mar/27']

    # Parcelas cartão por mês (baseado nas faturas)
    suncoast =    [1356, 1356, 1356, 1356, 1356, 1356, 1356, 1356, 1356, 0, 0, 0]  # até dez/26
    hoteis =      [1366, 1366, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # até mai/26 (02/04)
    casas_bahia = [393, 393, 393, 393, 393, 0, 0, 0, 0, 0, 0, 0]  # até ago/26
    sg_grife =    [154, 154, 154, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # até jun/26
    mercadopago = [55, 55, 55, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # até jun/26
    patricia =    [157, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # até abr/26 (11/12)
    anuidade_bb = [83, 83, 83, 83, 83, 83, 0, 0, 0, 0, 0, 0]  # até set/26
    petz =        [7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 0, 0]  # até set/26

    # Empréstimos
    signature =   [1348, 1348, 1348, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # até jun/26
    bb_consig =   [1886, 1886, 1886, 1886, 1886, 1886, 1886, 1886, 1886, 1886, 1886, 1886]  # até jun/28

    fig_parc = go.Figure()

    # Empréstimos (cores mais fortes)
    fig_parc.add_trace(go.Bar(name='BB Consignado (R$ 1.886)', x=meses_timeline, y=bb_consig,
                              marker_color='#2d3436', text=[f'{v/1000:.1f}k' if v > 0 else '' for v in bb_consig],
                              textposition='inside', textfont=dict(size=13, color='white')))
    fig_parc.add_trace(go.Bar(name='Signature (R$ 1.348)', x=meses_timeline, y=signature,
                              marker_color='#d63031', text=[f'{v/1000:.1f}k' if v > 0 else '' for v in signature],
                              textposition='inside', textfont=dict(size=13, color='white')))

    # Parcelas cartão (cores mais suaves)
    fig_parc.add_trace(go.Bar(name='SuncoastUSA (R$ 1.356)', x=meses_timeline, y=suncoast,
                              marker_color='#e17055'))
    fig_parc.add_trace(go.Bar(name='Hotéis.com (R$ 1.366)', x=meses_timeline, y=hoteis,
                              marker_color='#fdcb6e'))
    fig_parc.add_trace(go.Bar(name='Casas Bahia (R$ 393)', x=meses_timeline, y=casas_bahia,
                              marker_color='#74b9ff'))
    fig_parc.add_trace(go.Bar(name='Outras parcelas', x=meses_timeline,
                              y=[sum(x) for x in zip(sg_grife, mercadopago, patricia, anuidade_bb, petz)],
                              marker_color='#b2bec3'))

    # Total por mês como texto no topo
    totais = []
    for i in range(len(meses_timeline)):
        t = bb_consig[i] + signature[i] + suncoast[i] + hoteis[i] + casas_bahia[i] + \
            sg_grife[i] + mercadopago[i] + patricia[i] + anuidade_bb[i] + petz[i]
        totais.append(t)

    fig_parc.add_trace(go.Scatter(
        x=meses_timeline, y=[t + 300 for t in totais],
        mode='text',
        text=[f'<b>{fmt_brl(t)}</b>' for t in totais],
        textfont=dict(size=16, color='#2d3436'),
        showlegend=False,
    ))

    fig_parc.update_layout(
        barmode='stack',
        height=500, margin=dict(t=30, b=10),
        yaxis=dict(visible=False),
        xaxis=dict(tickfont=dict(size=15, color='#2d3436')),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, font=dict(size=13)),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    )

    with st.container(border=True):
        st.plotly_chart(fig_parc, use_container_width=True)

    # Resumo de alívio
    st.markdown("**Alívio progressivo:**")
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        st.metric("Hoje (Abr/26)", fmt_brl(totais[0]), border=True)
    with col_a2:
        st.metric("Jul/26", fmt_brl(totais[3]), f"-{fmt_brl(totais[0]-totais[3])}/mês", border=True)
    with col_a3:
        st.metric("Jan/27", fmt_brl(totais[9]), f"-{fmt_brl(totais[0]-totais[9])}/mês", border=True)


# ============================================================
# PAGINA 3 - ALERTAS
# ============================================================
elif pagina == "alertas":
    # ── PARCELAS DOS CARTÕES ──
    st.subheader(":material/credit_card: Parcelas dos cartões")
    st.caption("Compromissos parcelados que ainda vão cair nas próximas faturas")

    parcelas_cartao = pd.DataFrame([
        {"Compra": "🏫 Espaço Plenit (escola João)", "Cartão": "BB Ourocard", "Parcela": "R$ 1.720", "Parc.": "02/10", "Restam": "8", "Total restante": "R$ 13.760"},
        {"Compra": "🚗 V1 APP parcelado", "Cartão": "BB Ourocard", "Parcela": "R$ 1.072", "Parc.": "02/08", "Restam": "6", "Total restante": "R$ 6.432"},
        {"Compra": "🚗 V1 APP mensal (carro)", "Cartão": "BB Ourocard", "Parcela": "R$ 3.505", "Parc.": "mensal fixo", "Restam": "∞", "Total restante": "fixo"},
        {"Compra": "Catarinaco (pais pagam)", "Cartão": "BB Ourocard", "Parcela": "R$ 780", "Parc.": "03/10", "Restam": "7", "Total restante": "R$ 5.460"},
        {"Compra": "MP Funilaria", "Cartão": "BB Ourocard", "Parcela": "R$ 574", "Parc.": "01/10", "Restam": "9", "Total restante": "R$ 5.166"},
        {"Compra": "KdmCasasPre (móveis)", "Cartão": "BB Ourocard", "Parcela": "R$ 527", "Parc.": "03/12", "Restam": "9", "Total restante": "R$ 4.743"},
        {"Compra": "SC Betoneiras", "Cartão": "BB Ourocard", "Parcela": "R$ 399", "Parc.": "03/12", "Restam": "9", "Total restante": "R$ 3.591"},
        {"Compra": "TIM (telefone)", "Cartão": "BB Ourocard", "Parcela": "R$ 252", "Parc.": "10/21", "Restam": "11", "Total restante": "R$ 2.772"},
        {"Compra": "Óticas Imedia", "Cartão": "BB Ourocard", "Parcela": "R$ 250", "Parc.": "02/12", "Restam": "10", "Total restante": "R$ 2.500"},
        {"Compra": "SuperLegal CO", "Cartão": "BB Ourocard", "Parcela": "R$ 299", "Parc.": "07/10", "Restam": "3", "Total restante": "R$ 897"},
        {"Compra": "AKAD Seguros (2x)", "Cartão": "BB Ourocard", "Parcela": "R$ 233", "Parc.": "10/12", "Restam": "2", "Total restante": "R$ 466"},
        {"Compra": "HOTMART Comun", "Cartão": "BB Ourocard", "Parcela": "R$ 70", "Parc.": "11/12", "Restam": "1", "Total restante": "R$ 70"},
    ])

    st.dataframe(
        parcelas_cartao, use_container_width=True, hide_index=True,
        column_config={
            "Compra": st.column_config.TextColumn("Compra", width="medium"),
            "Cartão": st.column_config.TextColumn("Cartão", width="medium"),
            "Parcela": st.column_config.TextColumn("Parcela/mês", width="small"),
            "De/Até": st.column_config.TextColumn("Período", width="small"),
            "Restam": st.column_config.TextColumn("Restam", width="small"),
            "Total restante": st.column_config.TextColumn("Total restante", width="small"),
        }
    )

    st.error("**Saldo parcelado em faturas FUTURAS: R$ 45.872,63** (cartão BB) ⚠️ Limite usado: 93%")
    st.markdown("**Parcelas mensais recorrentes no cartão: ~R$ 8.180/mês** (Espaço Plenit + V1 APP fixo + V1 APP parc + Catarinaco + Funilaria + Kdm + SC + TIM + Óticas + SuperLegal + AKAD)")

    # Timeline visual
    st.markdown("**Quando cada parcela acaba:**")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.success("**Mai/26** — HOTMART acaba → -R$ 70/mês", icon="✅")
        st.success("**Jun/26** — AKAD Seguros acabam → -R$ 233/mês", icon="✅")
        st.info("**Jul/26** — SuperLegal acaba (10/10) → -R$ 299/mês", icon="📅")
    with col_t2:
        st.info("**Out/26** — Catarinaco acaba → -R$ 780/mês", icon="📅")
        st.warning("**Dez/26** — Espaço Plenit acaba → -R$ 1.720/mês 🎯 GRANDE alívio", icon="🎯")
        st.warning("**Jan/27** — KdmCasas + SC + Funilaria + V1 APP parc + Óticas → -R$ 2.822/mês", icon="🎯")
        st.info("**Mar/27** — TIM acaba → -R$ 252/mês", icon="💡")

    st.markdown("---")

    # ── EMPRÉSTIMOS ──
    st.subheader(":material/account_balance: Empréstimos")

    resumo = df[df['Ano_Mes'] < '2026-05'].groupby(['Ano_Mes', 'Tipo'])['Valor_num'].sum().unstack(fill_value=0)
    if 'INCOME' not in resumo.columns:
        resumo['INCOME'] = 0
    if 'EXPENSE' not in resumo.columns:
        resumo['EXPENSE'] = 0
    if 'INVESTMENT' not in resumo.columns:
        resumo['INVESTMENT'] = 0
    resumo['Saldo'] = resumo['INCOME'] - resumo['EXPENSE'] - resumo['INVESTMENT']

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("**Meses que gastaram mais do que receberam**")
            tem_negativo = False
            for mes, row in resumo.iterrows():
                if row['Saldo'] < 0:
                    tem_negativo = True
                    st.error(f"**{mes_label_pt(mes)}**: gastou {fmt_brl(abs(row['Saldo']))} a mais", icon="🔴")
            if not tem_negativo:
                st.success("Nenhum mês negativo!", icon="✅")

    with col2:
        with st.container(border=True):
            st.markdown("**Maiores gastos (período todo)**")
            desp_all = df[(df['Tipo'] == 'EXPENSE') & (df['Ano_Mes'] < '2026-04')]
            top_cats = desp_all.groupby('Categoria_Mae')['Valor_num'].sum().sort_values(ascending=False).head(5)
            n_meses_total = desp_all['Ano_Mes'].nunique()
            medals = ['1°', '2°', '3°', '4°', '5°']
            for i, (cat, val) in enumerate(top_cats.items()):
                media = val / max(n_meses_total, 1)
                st.warning(f"**{medals[i]} {cat}**: {fmt_brl(val)} total ({fmt_brl(media)}/mês)", icon="📈")

    # Dívidas em destaque
    st.subheader(":material/credit_card: Situação das dívidas")
    st.markdown("*(atualizado Abr/2026 — dados dos extratos)*")

    st.dataframe(
        pd.DataFrame([
            {"Dívida": "CDC BB (contrato 177175337)", "Parcela": "R$ 3.672", "Sai dia": "5", "Conta": "BB CC (João)", "Status": "Acaba jun/26 (parcela 6) — pedida simulação quitação"},
            {"Dívida": "🔬 Aparelho Ultrassom (Santander)", "Parcela": "R$ 2.590", "Sai dia": "6-9", "Conta": "BB CC (João)", "Status": "Equipamento médico do consultório do João — confirmar saldo/prazo"},
            {"Dívida": "💳 Empréstimo Cartão Caixa Elo (Iza)", "Parcela": "R$ 3.710", "Sai dia": "7", "Conta": "Cartão Caixa Elo (Iza)", "Status": "10 parcelas, acaba out/26 — fatura parcelada"},
            {"Dívida": "FIES (Izabela)", "Parcela": "Suspenso", "Sai dia": "—", "Conta": "—", "Status": "Em análise — possível abatimento COVID"},
        ]),
        use_container_width=True, hide_index=True,
        column_config={
            "Dívida": st.column_config.TextColumn("Dívida", width="medium"),
            "Parcela": st.column_config.TextColumn("Parcela/mês", width="small"),
            "Sai dia": st.column_config.TextColumn("Dia", width="small"),
            "Conta": st.column_config.TextColumn("Conta", width="small"),
            "Status": st.column_config.TextColumn("Status", width="large"),
        }
    )

    st.error("**💸 Dívidas mensais fixas atuais: R$ 9.972** (CDC BB R$ 3.672 + Aparelho US Santander R$ 2.590 + Empréstimo Cartão Caixa Elo R$ 3.710)\n\n📅 **Cronograma de alívio:**\n- **Jun/26**: CDC BB acaba → -R$ 3.672/mês (sobra R$ 6.300)\n- **Out/26**: Cartão Caixa acaba → -R$ 3.710/mês (sobra R$ 2.590, só Aparelho US)\n\n📌 **A confirmar com a Iza:** saldo devedor + prazo do financiamento do Aparelho US (Santander)", icon="🚨")

    # ── INVESTIMENTOS / RESERVA ──
    st.subheader(":material/savings: Investimentos e Reserva (Inter)")
    st.markdown("**Histórico de aportes em 2026**")
    st.dataframe(
        pd.DataFrame([
            {"Data": "12/01/2026", "Tipo": "Aporte CDB", "Valor": "R$ 12.000", "Produto": "CDB POS DI LIQ", "Obs": ""},
            {"Data": "16/01/2026", "Tipo": "Aporte CDB", "Valor": "R$ 10.000", "Produto": "CDB Porq Obj", "Obs": ""},
            {"Data": "19/02/2026", "Tipo": "Aporte CDB", "Valor": "R$ 17.000", "Produto": "CDB POS DI LIQ", "Obs": ""},
            {"Data": "04/03/2026", "Tipo": "Aporte CDB", "Valor": "R$ 8.000", "Produto": "CDB POS DI LIQ", "Obs": ""},
            {"Data": "28/03/2026", "Tipo": "Aporte CDB", "Valor": "R$ 1.400", "Produto": "CDB POS DI LIQ", "Obs": ""},
            {"Data": "08/04/2026", "Tipo": "Resgate", "Valor": "+R$ 3.377", "Produto": "CDB PRE 252 TBE", "Obs": "Vencimento"},
            {"Data": "08/04/2026", "Tipo": "Aporte LCI", "Valor": "R$ 3.000", "Produto": "LCI DI 720", "Obs": "Realocação CDB→LCI"},
        ]),
        use_container_width=True, hide_index=True,
    )

    col_inv1, col_inv2, col_inv3 = st.columns(3)
    with col_inv1:
        st.metric("Total aplicado", "R$ 51.400", "+R$ 51.400 desde dez/25", border=True)
    with col_inv2:
        st.metric("Saldo atual (06/abr)", "R$ 99.693", "Print Inter Investimentos", border=True)
    with col_inv3:
        st.metric("Crescimento patrimônio", "~R$ 50k", "vs dez/25 (~R$ 50k)", border=True)

    st.info("📊 **Reserva dobrou de ~R$ 50k para ~R$ 100k** (jan-abr/2026). Aportes desaceleraram em abr (só R$ 3k em LCI). Inclui depósito em juízo (processo apartamento).", icon="💰")

    st.subheader(":material/savings: Onde podem economizar")

    n_meses_real = max(df[df['Ano_Mes'] < '2026-05']['Ano_Mes'].nunique(), 1)
    desp_real = df[(df['Tipo'] == 'EXPENSE') & (df['Ano_Mes'] < '2026-05')]

    col1, col2, col3 = st.columns(3)
    with col1:
        uber_mes = desp_real[desp_real['Categoria'].isin(['Uber / 99', 'Transporte Geral', 'Pedágio / Estacionamento', 'Combustível'])]['Valor_num'].sum() / n_meses_real
        st.metric("Transporte/Uber", f"{fmt_brl(uber_mes)}/mês",
                  f"Meta: R$ 1.500 (economia de {fmt_brl(max(0, uber_mes - 1500))})",
                  delta_color="inverse", border=True)

    with col2:
        alim_mes = desp_real[desp_real['Categoria'].isin(['Alimentação', 'Restaurante / Ifood', 'Bares / Festas'])]['Valor_num'].sum() / n_meses_real
        st.metric("Alimentação/Ifood", f"{fmt_brl(alim_mes)}/mês",
                  f"Meta: R$ 4.000 (economia de {fmt_brl(max(0, alim_mes - 4000))})",
                  delta_color="inverse", border=True)

    with col3:
        cartao_limite = desp_real[desp_real['Categoria'].isin(['Compras Geral', 'Compras Moradia', 'Roupa / Sapatos / Vestuário', 'Lazer Geral'])]['Valor_num'].sum() / n_meses_real
        st.metric("Compras + Lazer", f"{fmt_brl(cartao_limite)}/mês",
                  f"Meta: R$ 3.000 (economia de {fmt_brl(max(0, cartao_limite - 3000))})",
                  delta_color="inverse", border=True)

    st.subheader(":material/assignment: Objetivos financeiros")
    st.dataframe(
        pd.DataFrame([
            {"O quê": "Reserva de emergência", "Quanto": "R$ 100.000 (6 meses despesas)", "Até quando": "Prioridade imediata", "Situação": "R$ 48.400 aplicados (CDB Inter)"},
            {"O quê": "Apartamento (entrada)", "Quanto": "R$ 400.000", "Até quando": "3 anos (2029)", "Situação": "Investir R$ 10.000/mês"},
            {"O quê": "Segundo carro", "Quanto": "A definir", "Até quando": "1-2 anos", "Situação": "Pendente"},
            {"O quê": "Viagem Quebec", "Quanto": "R$ 30.000", "Até quando": "Dez/2026", "Situação": "Separar R$ 3.000/mês"},
            {"O quê": "Segundo filho", "Quanto": "R$ 120.000 (6 meses licença)", "Até quando": "Início 2027", "Situação": "Planejar reserva"},
            {"O quê": "Limite cartão crédito", "Quanto": "Máx R$ 15.000/mês", "Até quando": "Imediato", "Situação": "Remover pagamento por aproximação"},
            {"O quê": "Aposentadoria", "Quanto": "R$ 60.000/mês com 50 anos", "Até quando": "Longo prazo", "Situação": "Iniciar previdência"},
        ]),
        use_container_width=True, hide_index=True,
    )


# ============================================================
# FOOTER
# ============================================================
st.caption(":material/favorite: Dashboard financeiro · GW9 Capital · Assessoria personalizada", text_alignment="center")