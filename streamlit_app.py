import streamlit as st
import altair as alt
import pandas as pd
import math
from pathlib import Path
import gdown

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Análise de Dados da Plataforma Lattes',
    page_icon=':books:',  # This is an emoji shortcode. Could be a URL too.
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

from_year, to_year = st.slider(
    'Anos para análise:',
    min_value=min_value,
    max_value=max_value,
    value=[2010, 2021])

tipo_analise = st.segmented_control(
    "Tipo de análise:",
    ['Grande Área', 'Tipo de Formação',
     'Gênero', 'UF da Instituição', 'Bolsas'],
    default='Grande Área',
)

coluna = {
    'Grande Área': 'grande_area',
    'Tipo de Formação': 'tipo_formacao',
    'Gênero': 'genero',
    'UF da Instituição': 'uf_instituicao',
    'Bolsas': 'flag_bolsa'
}[tipo_analise]

current_df = aggregate_by_column(base_df, coluna)
options = [x for x in sorted(
    current_df[coluna].unique()) if x != 'Sem Informação']

if not len(options):
    st.warning(f"Selecione pelo menos uma opção para a coluna '{coluna}'.")

selected_options = st.multiselect(
    f'{tipo_analise} para análise:',
    options=options,
    default=options,
    placeholder='Selecione uma ou mais opções'
)

''

# Filter the data
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

st.header('Formações ao longo dos anos', divider='gray')

''

chart = (
    alt.Chart(filtered_df)
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
)

st.altair_chart(chart, use_container_width=True)

''

st.header(f'Resumo entre {from_year} e {to_year}', divider='gray')

''

cols = st.columns(2)

total_conclusoes = filtered_df['quantidade'].sum()
total_null = null_df['quantidade'].sum()
total_conclusoes_coluna = (
    filtered_df.groupby(coluna)['quantidade']
    .sum()
    .reset_index()
    .sort_values(by='quantidade', ascending=False)
)

with cols[0]:
    st.metric(
        label='Total de Conclusões ✅',
        value=f"{total_conclusoes:,}"
    )

with cols[1]:
    st.metric(
        label=f'Total {tipo_analise} nulo ❌',
        value=f"{total_null:,}"
    )
''

cols = st.columns(3)

for i, selected in enumerate(selected_options):
    col = cols[i % len(cols)]

    with col:
        row_conclusoes_coluna = total_conclusoes_coluna.loc[
            total_conclusoes_coluna[coluna] == selected, 'quantidade']
        valor_conclusoes_coluna = row_conclusoes_coluna.iat[
            0] if not row_conclusoes_coluna.empty else 0
        st.metric(
            label=f'Total {selected}',
            value=f"{valor_conclusoes_coluna:,}"
        )

''

first_year = current_df[current_df['ano_conclusao'] == from_year]
last_year = current_df[current_df['ano_conclusao'] == to_year]
n = to_year - from_year

''

st.header(
    f'Crescimento Médio Anual Composto', divider='gray')

''

cols = st.columns(3)
cagr_list = []

for i, selected in enumerate(selected_options):
    col = cols[i % len(cols)]

    with col:
        first_row = first_year[first_year[coluna] == selected]
        last_row = last_year[last_year[coluna] == selected]
        first_quantidade = first_row['quantidade'].iat[0] if not first_row.empty else 0
        last_quantidade = last_row['quantidade'].iat[0] if not last_row.empty else 0

        if (first_quantidade == 0 or last_quantidade == 0):
            value = f"{first_quantidade} → {last_quantidade}"
            delta = 'n/a'
            delta_color = 'off'
        else:
            value = f"{first_quantidade} → {last_quantidade}"
            cagr = (last_quantidade / first_quantidade) ** (1/n) - 1
            cagr_list.append((selected, cagr * 100))
            delta = f'{(cagr * 100):,.2f}%'
            delta_color = 'normal'

        st.metric(
            label=f'{selected}',
            value=value,
            delta=delta,
            delta_color=delta_color
        )

cagr_df = pd.DataFrame(
    cagr_list,
    columns=[coluna, 'carg']
).sort_values('carg', ascending=False)

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

st.header(f'Crescimento Percentual Anual', divider='gray')

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

crescimento_df = (
    filtered_df
    .groupby(coluna)['crescimento_pct']
    .mean()
    .reset_index(name='Crescimento médio (%)')
    .sort_values(by='Crescimento médio (%)', ascending=False)
)

crescimento_df = crescimento_df.rename(columns={
    coluna: tipo_analise
})

''
st.header(f'Crescimento Médio Anual', divider='gray')
''
st.dataframe(
    crescimento_df.style
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

base_df['nao_concluido_flag'] = (
    (base_df['curso_concluido'] == False) |
    (base_df['ano_conclusao'].isna())
)

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

tabela_taxa = (
    base_df
    .groupby('ano_inicio')
    .agg(
        total=('nao_concluido_flag', 'count'),
        nao_concluidos=('nao_concluido_flag', 'sum')
    )
    .reset_index()
)
tabela_taxa['taxa_nao_conclusao'] = (
    tabela_taxa['nao_concluidos'] / tabela_taxa['total']
)
filtered_tabela_taxa = tabela_taxa[
    (tabela_taxa['ano_inicio'] <= to_year)
    & (from_year <= tabela_taxa['ano_inicio'])
]
filtered_tabela_taxa = filtered_tabela_taxa.sort_values(
    'taxa_nao_conclusao', ascending=False)

filtered_tabela_taxa = filtered_tabela_taxa.rename(columns={
    'ano_inicio': 'Ano de Início',
    'total': 'Cursos Concluídos',
    'nao_concluidos': 'Cursos Não Concluídos',
    'taxa_nao_conclusao': 'Taxa de Não Conclusão (%)'
})

cols = st.columns(2)

for i, categoria in enumerate(selected_options):

    df_cat = filtered_taxa[
        filtered_taxa[coluna] == categoria
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
        st.markdown(f"**{categoria}**")
        st.altair_chart(chart, use_container_width=True)

st.dataframe(
    filtered_tabela_taxa.style
    .format({'Taxa de Não Conclusão (%)': '{:.2%}'})
    .background_gradient(
        subset=['Taxa de Não Conclusão (%)'],
        cmap='Reds'
    ),
    hide_index=True,
    use_container_width=True
)
