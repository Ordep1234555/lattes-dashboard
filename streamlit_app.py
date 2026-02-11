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

    conclusoes_df = raw_df.dropna(subset=['ano_conclusao', 'grande_area', 'tipo_formacao',
                                  'genero', 'uf_instituicao', 'flag_bolsa'])
    conclusoes_df = conclusoes_df[
        (conclusoes_df['ano_conclusao'] >= MIN_YEAR) &
        (conclusoes_df['ano_conclusao'] <= MAX_YEAR)
    ]

    return conclusoes_df


def aggregate_by_column(df, coluna):
    return (
        df.groupby(['ano_conclusao', coluna])
        .size()
        .reset_index(name='quantidade')
    )


base_df = get_curriculos_data()

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# Análise de Dados da Plataforma Lattes :books:

Análise de dados a partir da Plataforma Lattes. Projeto pessoal para portifólio.
O objetivo inicial era observar o impacto da pandemia de COVID-19 na formação de
estudantes de pós-graduação a partir da grande área de formação.
Dados limitados pela coleta feita ainda no início de 2025, o que pode gerar distorções.
'''

# Add some spacing
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
options = current_df[coluna].unique()

if not len(options):
    st.warning(f"Selecione pelo menos uma opção para a coluna '{coluna}'.")

selected_options = st.multiselect(
    f'{tipo_analise} para análise:',
    options=options,
    default=options.tolist())

''
''
''

# Filter the data
filtered_df = current_df[
    (current_df[coluna].isin(selected_options))
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
''

first_year = current_df[current_df['ano_conclusao'] == from_year]
last_year = current_df[current_df['ano_conclusao'] == to_year]

st.header(f'Crescimento entre {from_year} e {to_year}', divider='gray')

''

cols = st.columns(3)

for i, area in enumerate(selected_options):
    col = cols[i % len(cols)]

    with col:
        first_quantidade = first_year[first_year[coluna]
                                      == area]['quantidade'].iat[0]
        last_quantidade = last_year[last_year[coluna]
                                    == area]['quantidade'].iat[0]

        if math.isnan(first_quantidade):
            value = f"{first_quantidade} → {last_quantidade}"
            delta = 'n/a'
            delta_color = 'off'
        else:
            value = f"{first_quantidade} → {last_quantidade}"
            delta = f'{((last_quantidade - first_quantidade) / first_quantidade * 100):,.2f}%'
            delta_color = 'normal'

        st.metric(
            label=f'{area}',
            value=value,
            delta=delta,
            delta_color=delta_color
        )
