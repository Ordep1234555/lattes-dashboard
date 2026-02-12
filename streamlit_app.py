import streamlit as st
import altair as alt
import pandas as pd
import math
from pathlib import Path
import gdown

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Análise de Dados Lattes',
    page_icon=':books:',
    layout='wide',
)

# -----------------------------------------------------------------------------
# Declare some useful functions.


@st.cache_data
def get_curriculos_data():

    # DATA_FILENAME = Path(__file__).parent/'data/curriculos_processados.csv'
    url = "https://drive.google.com/uc?id=11ecM-F5dWYH4V3RqxLB_4ISLT-7iAye3"

    data_path = Path("data")
    data_path.mkdir(exist_ok=True)

    csv_path = data_path / "curriculos_processados.csv"

    if not csv_path.exists():
        gdown.download(url, str(csv_path), quiet=False)

    raw_df = pd.read_csv(csv_path,
                         dtype={
                             "ano_inicio": "Int64",
                             "ano_conclusao": "Int64"
                         })

    raw_df['grande_area'] = raw_df['grande_area'].str.split(';')
    raw_df = raw_df.explode('grande_area')
    raw_df['grande_area'] = raw_df['grande_area'].str.strip()

    MIN_YEAR = 1960
    MAX_YEAR = 2023

    raw_df = raw_df[
        (raw_df['ano_conclusao'] >= MIN_YEAR) &
        (raw_df['ano_conclusao'] <= MAX_YEAR)
    ]

    raw_df['nao_concluido_flag'] = (
        (raw_df['curso_concluido'] == False) |
        (raw_df['ano_conclusao'].isna())
    )

    return raw_df


def aggregate_by_column(df, coluna):
    new_df = df.dropna(subset=['ano_conclusao'])
    new_df = (new_df.groupby(['ano_conclusao', coluna], dropna=False)
              .size()
              .reset_index(name='quantidade')
              .sort_values([coluna, 'ano_conclusao'])
              )
    new_df[coluna] = new_df[coluna].fillna('Sem Informação')
    new_df['crescimento_pct'] = (
        new_df.groupby(coluna)['quantidade']
        .pct_change() * 100
    ).round(2)
    new_df['crescimento_pct'] = new_df['crescimento_pct'].replace(
        [float('inf'), -float('inf')], None)

    return new_df


base_df = get_curriculos_data()

# -----------------------------------------------------------------------------

'''
# Análise de Dados da Plataforma Lattes :books:

Análise de dados a partir da Plataforma Lattes. Projeto pessoal para portifólio.
O objetivo inicial era observar o impacto da pandemia de COVID-19 na formação de
estudantes de pós-graduação a partir da grande área de formação.
Dados limitados pela coleta feita ainda no início de 2025, o que pode gerar distorções.
'''

''
''

min_value = 1960
max_value = 2023

# Layout Principal
cols = st.columns([2, 4, 3])

left_cell = cols[0].container(
    border=True, height=400, vertical_alignment="top"
)
center_cell = cols[1].container(
    border=False, height=400, vertical_alignment="center"
)
right_cell = cols[2].container(
    border=False, height=400, vertical_alignment="center"
)

# Filtro de Ano e Categoria
with left_cell:
    from_year, to_year = st.slider(
        'Anos para análise:',
        min_value=min_value,
        max_value=max_value,
        value=[2010, 2021])

    tipo_analise = st.pills(
        "Tipo de análise:",
        ['Grande Área', 'Tipo de Formação',
         'Gênero', 'UF da Instituição', 'Bolsas'],
        default='Grande Área',
    )

# Dicionario da Categoria para o nome da coluna correspondente no DataFrame
coluna = {
    'Grande Área': 'grande_area',
    'Tipo de Formação': 'tipo_formacao',
    'Gênero': 'genero',
    'UF da Instituição': 'uf_instituicao',
    'Bolsas': 'flag_bolsa'
}[tipo_analise]

# Estabele DF principal
current_df = aggregate_by_column(base_df, coluna)
options = [x for x in sorted(
    current_df[coluna].unique()) if x != 'Sem Informação']

if not len(options):
    st.warning(f"Selecione pelo menos uma opção para a coluna '{coluna}'.")

# Filtro de opções dentro da Categoria selecionada
with left_cell:
    selected_options = st.multiselect(
        f'{tipo_analise} para análise:',
        options=options,
        default=options,
        placeholder='Selecione uma ou mais opções'
    )

n_cols1 = math.ceil(len(selected_options) / 2)
n_cols2 = math.ceil(len(selected_options) / 3)

# DFs com anos e opções selecionadas
filtered_df = current_df[
    (current_df[coluna].isin(selected_options))
    & (current_df['ano_conclusao'] <= to_year)
    & (from_year <= current_df['ano_conclusao'])
]
null_df = current_df[
    (current_df[coluna] == 'Sem Informação')
    & (current_df['ano_conclusao'] <= to_year)
    & (from_year <= current_df['ano_conclusao'])
]

first_year = filtered_df[filtered_df['ano_conclusao'] == from_year]
last_year = filtered_df[filtered_df['ano_conclusao'] == to_year]
n = to_year - from_year

total_conclusoes_ano = filtered_df.groupby(
    'ano_conclusao')['quantidade'].sum().reset_index()
total_conclusoes_ano['crescimento_pct'] = (
    total_conclusoes_ano['quantidade']
    .pct_change() * 100
).round(2)
total_conclusoes_ano['crescimento_pct'] = total_conclusoes_ano['crescimento_pct'].fillna(
    0).replace([float('inf'), -float('inf')], 0)
melhor_ano = total_conclusoes_ano.loc[total_conclusoes_ano['crescimento_pct'].idxmax(
)]
pior_ano = total_conclusoes_ano.loc[total_conclusoes_ano['crescimento_pct'].idxmin(
)]

cagr_list = []
for i, selected in enumerate(selected_options):
    first_row = first_year[first_year[coluna] == selected]
    last_row = last_year[last_year[coluna] == selected]
    first_quantidade = first_row['quantidade'].iat[0] if not first_row.empty else 0
    last_quantidade = last_row['quantidade'].iat[0] if not last_row.empty else 0

    if (first_quantidade == 0 or last_quantidade == 0 or n == 0):
        cagr_list.append((selected, 0))
    else:
        cagr = (last_quantidade / first_quantidade) ** (1/n) - 1
        cagr_list.append((selected, cagr * 100))

cagr_df = pd.DataFrame(
    cagr_list,
    columns=[coluna, 'carg']
).sort_values('carg', ascending=False)

melhor_crescimento = cagr_df.loc[cagr_df['carg'].idxmax()]
pior_crescimento = cagr_df.loc[cagr_df['carg'].idxmin()]

taxa = (
    base_df
    .groupby(['ano_inicio', coluna])
    .agg(
        total=('nao_concluido_flag', 'count'),
        nao_concluidos=('nao_concluido_flag', 'sum')
    )
    .reset_index()
)

taxa['taxa_nao_conclusao'] = (
    taxa['nao_concluidos'] / taxa['total']
)

filtered_taxa = taxa[
    (taxa[coluna].isin(selected_options))
    & (taxa['ano_inicio'] <= to_year)
    & (from_year <= taxa['ano_inicio'])
]

with center_cell:
    chart = (
        alt.Chart(
            filtered_df, title=f'Número de Conclusões por Ano - {tipo_analise}')
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "ano_conclusao:O",
                title="Ano de Conclusão",
                axis=alt.Axis(labelAngle=0)
            ),
            y=alt.Y(
                "quantidade:Q",
                title="Número de Conclusões"
            ),
            color=alt.Color(
                f"{coluna}:N",
                title=tipo_analise
            ),
            tooltip=[
                alt.Tooltip("ano_conclusao:O", title="Ano"),
                alt.Tooltip(f"{coluna}:N", title=tipo_analise),
                alt.Tooltip("quantidade:Q", title="Conclusões")
            ]
        )
        .configure_legend(disable=True)
    )
    st.altair_chart(chart, use_container_width=True)

with right_cell:
    chart = (
        alt.Chart(
            filtered_df, title=f'Distribuição de Conclusões por {tipo_analise}')
        .mark_arc()
        .encode(
            alt.Theta(
                "quantidade:Q",
                aggregate='sum',
                title="Número de Conclusões"
            ),
            alt.Color(
                f"{coluna}:N",
                title=tipo_analise
            )
        )
    )
    st.altair_chart(chart, use_container_width=True)

st.header(f'Resumo entre {from_year} e {to_year}', divider='gray')

total_conclusoes = total_conclusoes_ano['quantidade'].sum()
total_null = null_df['quantidade'].sum()
total_nao_concluidos = filtered_taxa['nao_concluidos'].sum()
total_iniciados = filtered_taxa['total'].sum()

main_cols = st.columns([1, 1, 1, 2])

with main_cols[0]:
    with st.container(border=True, height=150):
        cols = st.columns(2)

        with cols[0]:
            st.metric(
                label='Total de Conclusões ✅',
                value=f"{total_conclusoes:,}"
            )

        with cols[1]:
            st.metric(
                label=f'{tipo_analise} nulo ❌',
                value=f"{total_null:,}"
            )

with main_cols[1]:
    with st.container(border=True, height=150):
        cols = st.columns(2)

        with cols[0]:
            st.metric(
                label='Total Iniciados ✅',
                value=f"{total_iniciados:,}"
            )

        with cols[1]:
            st.metric(
                label='Total Não Concluídos ❌',
                value=f"{total_nao_concluidos:,}"
            )

with main_cols[2]:
    with st.container(border=True, height=150):
        cols = st.columns(2)

        with cols[0]:
            st.metric(
                label='Melhor Ano 📈',
                value=f"{int(melhor_ano['ano_conclusao'])}",
                delta=f"{melhor_ano['crescimento_pct']}%"
            )

        with cols[1]:
            st.metric(
                label=f'Pior Ano 📉',
                value=f"{int(pior_ano['ano_conclusao'])}",
                delta=f"{pior_ano['crescimento_pct']}%"
            )

with main_cols[3]:
    with st.container(border=True, height=150):
        cols = st.columns(2)

        with cols[0]:
            st.metric(
                label='Maior Crescimento 📈',
                value=f"{melhor_crescimento[coluna]}",
                delta=f"{melhor_crescimento['carg']:,.2f}%"
            )

        with cols[1]:
            st.metric(
                label='Menor Crescimento 📉',
                value=f"{pior_crescimento[coluna]}",
                delta=f"{pior_crescimento['carg']:,.2f}%"
            )

''

st.header('Crescimento Médio Anual Composto', divider='gray',
          help="CAGR (Crescimento Anual Composto) é uma métrica que mede o crescimento médio anual de um investimento ou indicador ao longo de um período. (Valor Final / Valor Inicial)^(1/n) - 1, onde n é o número de anos.")

''

cols = st.columns(3)

for i, selected in enumerate(selected_options):
    col = cols[i % len(cols)]

    with col:
        value = f"{first_quantidade} → {last_quantidade}"
        carg_row = cagr_df[cagr_df[coluna] == selected]
        carg_value = carg_row['carg'].iat[0] if not carg_row.empty else 0

        st.metric(
            label=f'{selected}',
            value=value,
            delta=f"{carg_value:,.2f}%",
            delta_color="normal" if carg_value != 0 else "off"
        )

''

chart = alt.Chart(cagr_df).mark_bar().encode(
    x=alt.X('carg:Q', title='CAGR (%)'),
    y=alt.Y(
        f"{coluna}:N",
        sort='-x',
        title=None
    ),
    color=alt.condition(
        alt.datum["carg"] > 0,
        alt.value("#2ca02c"),
        alt.value("#d62728")
    ),
    tooltip=[
        alt.Tooltip(f"{coluna}:N", title=tipo_analise),
        alt.Tooltip('carg:Q', title='CAGR (%)', format='.2f')
    ]
).properties(
    height=400
)

st.altair_chart(chart, use_container_width=True)

''

st.header(f'Crescimento Percentual Anual', divider='gray',
          help="Crescimento percentual anual é a variação percentual de um indicador de um ano para o outro. ((Valor Ano Atual - Valor Ano Anterior) / Valor Ano Anterior) * 100")

''

cols = st.columns(3)

for i, selected in enumerate(selected_options):
    col = cols[i % len(cols)]

    with col:
        selected_df = filtered_df[filtered_df[coluna] == selected]
        st.markdown(f"{selected}")
        chart = alt.Chart(selected_df).mark_bar().encode(
            x=alt.X('ano_conclusao:O', title='Ano'),
            y=alt.Y(
                'crescimento_pct:Q',
                title='Crescimento (%)',
                scale=alt.Scale(zero=True)
            ),
            color=alt.condition(
                alt.datum.crescimento_pct > 0,
                alt.value("#2ca02c"),
                alt.value("#d62728")
            ),
            tooltip=[
                alt.Tooltip('ano_conclusao:O', title='Ano'),
                alt.Tooltip('crescimento_pct:Q',
                            title='Crescimento (%)', format='.2f')
            ]
        ).properties(
            height=300
        )
        st.altair_chart(chart, use_container_width=True)

crescimento_area_df = (
    filtered_df
    .groupby(coluna)['crescimento_pct']
    .mean()
    .reset_index(name='Crescimento médio (%)')
    .sort_values(by='Crescimento médio (%)', ascending=True)
)

crescimento_area_df = crescimento_area_df.rename(columns={
    coluna: tipo_analise
})

crescimento_ano_df = (
    filtered_df
    .groupby('ano_conclusao')['crescimento_pct']
    .mean()
    .reset_index(name='Crescimento médio (%)')
    .sort_values(by='Crescimento médio (%)', ascending=True)
)

crescimento_ano_df = crescimento_ano_df.rename(columns={
    'ano_conclusao': 'Ano de Conclusão'
})

''
st.header(f'Crescimento Médio Anual', divider='gray')
''

cols = st.columns(2)

with cols[0]:
    st.dataframe(
        crescimento_area_df.style
        .format({'Crescimento médio (%)': '{:.2f}%'})
        .background_gradient(
            subset=['Crescimento médio (%)'],
            cmap='RdYlGn'
        ),
        hide_index=True,
        use_container_width=True
    )

with cols[1]:
    st.dataframe(
        crescimento_ano_df.style
        .format({'Crescimento médio (%)': '{:.2f}%'})
        .background_gradient(
            subset=['Crescimento médio (%)'],
            cmap='RdYlGn'
        ),
        hide_index=True,
        use_container_width=True
    )

''
st.header(f'Cursos Não Concluídos Por Ano de Início', divider='gray')
''

cols = st.columns(2)

for i, selected in enumerate(selected_options):

    df_cat = filtered_taxa[
        filtered_taxa[coluna] == selected
    ]

    if df_cat.empty:
        continue

    base = alt.Chart(df_cat)

    # 📊 Barras (valor absoluto)
    bars = base.mark_bar(opacity=0.6).encode(
        x=alt.X('ano_inicio:O', title=None),
        y=alt.Y('nao_concluidos:Q', title='Qtd'),
        tooltip=[
            'ano_inicio',
            'nao_concluidos',
            alt.Tooltip('taxa_nao_conclusao:Q', format='.2%')
        ]
    )

    # 📈 Linha (percentual)
    line = base.mark_line(
        strokeWidth=2,
        color='red'
    ).encode(
        x='ano_inicio:O',
        y=alt.Y(
            'taxa_nao_conclusao:Q',
            axis=alt.Axis(format='%'),
            title='Taxa'
        )
    )

    chart = alt.layer(bars, line).resolve_scale(
        y='independent'
    ).properties(
        height=250
    )

    with cols[i % 2]:
        st.markdown(f"**{selected}**")
        st.altair_chart(chart, use_container_width=True)

filtered_taxa = filtered_taxa.rename(columns={
    'ano_inicio': 'Ano de Início',
    coluna: tipo_analise,
    'total': 'Cursos Concluídos',
    'nao_concluidos': 'Cursos Não Concluídos',
    'taxa_nao_conclusao': 'Taxa de Não Conclusão (%)'
}).sort_values('Taxa de Não Conclusão (%)', ascending=False)

st.dataframe(
    filtered_taxa.style
    .format({'Taxa de Não Conclusão (%)': '{:.2%}'})
    .background_gradient(
        subset=['Taxa de Não Conclusão (%)'],
        cmap='Reds'
    ),
    hide_index=True,
    use_container_width=True
)
