from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

API_BASE_URL = os.getenv(
    "RAG_API_URL",
    "http://localhost:8000",
)

DASHBOARD_ENDPOINT = f"{API_BASE_URL.rstrip('/')}/benchmarks/dashboard"

REQUEST_TIMEOUT_SECONDS = 10


st.set_page_config(
    page_title="RAG Benchmark Dashboard",
    page_icon="📊",
    layout="wide",
)


@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def load_dashboard_data() -> dict[str, list[dict[str, Any]]]:
    response = requests.get(
        DASHBOARD_ENDPOINT,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    payload = response.json()

    if "data" not in payload:
        raise ValueError("A resposta da API não contém o campo 'data'.")

    data = payload["data"]

    if not isinstance(data, dict):
        raise ValueError("O campo 'data' da API deve ser um objeto.")

    return data


def parse_timestamp(value: str) -> datetime:
    return datetime.strptime(
        value,
        "%Y%m%d_%H%M%S",
    )


def build_dataframe(
    dashboard_data: dict[str, list[dict[str, Any]]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for vector_store, benchmarks in dashboard_data.items():
        for benchmark in benchmarks:
            row = {
                "vector_store": vector_store,
                **benchmark,
            }

            rows.append(row)

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        return dataframe

    dataframe["datetime"] = dataframe["timestamp"].apply(parse_timestamp)

    dataframe = dataframe.sort_values(
        by=[
            "datetime",
            "vector_store",
        ]
    ).reset_index(drop=True)

    return dataframe


def filter_dataframe(
    dataframe: pd.DataFrame,
    selected_stores: list[str],
    history_limit: int | None,
) -> pd.DataFrame:
    filtered = dataframe[dataframe["vector_store"].isin(selected_stores)].copy()

    if history_limit is None:
        return filtered

    filtered = (
        filtered.sort_values(
            "datetime",
            ascending=False,
        )
        .groupby(
            "vector_store",
            group_keys=False,
        )
        .head(history_limit)
        .sort_values(
            [
                "datetime",
                "vector_store",
            ]
        )
    )

    return filtered.reset_index(drop=True)


def format_timestamp(value: datetime) -> str:
    return value.strftime("%d/%m/%Y %H:%M:%S")


def render_metric_card(
    label: str,
    value: str,
    help_text: str | None = None,
) -> None:
    st.metric(
        label=label,
        value=value,
        help=help_text,
    )


def render_latest_benchmark_cards(
    dataframe: pd.DataFrame,
) -> None:
    st.subheader("Último benchmark")

    latest_timestamp = dataframe["datetime"].max()

    latest = dataframe[dataframe["datetime"] == latest_timestamp].copy()

    best_score = latest["score"].max()

    fastest_row = latest.loc[latest["latency"].idxmin()]

    fastest_retrieval_row = latest.loc[latest["retrieval_latency"].idxmin()]

    cheapest_row = latest.loc[latest["cost"].idxmin()]

    lowest_tokens_row = latest.loc[latest["tokens"].idxmin()]

    st.caption(f"Execução: {format_timestamp(latest_timestamp)}")

    first_row = st.columns(5)

    with first_row[0]:
        render_metric_card(
            "Melhor score",
            f"{best_score:.2%}",
        )

    with first_row[1]:
        render_metric_card(
            "Menor latência",
            f"{fastest_row['latency']:.4f}s",
            str(fastest_row["vector_store"]),
        )

    with first_row[2]:
        render_metric_card(
            "Melhor retrieval",
            (f"{fastest_retrieval_row['retrieval_latency']:.4f}s"),
            str(fastest_retrieval_row["vector_store"]),
        )

    with first_row[3]:
        render_metric_card(
            "Menor custo",
            f"${cheapest_row['cost']:.8f}",
            str(cheapest_row["vector_store"]),
        )

    with first_row[4]:
        render_metric_card(
            "Menor uso de tokens",
            f"{lowest_tokens_row['tokens']:.2f}",
            str(lowest_tokens_row["vector_store"]),
        )


def render_line_chart(
    dataframe: pd.DataFrame,
    metric: str,
    title: str,
    y_label: str,
    percentage: bool = False,
) -> None:
    figure, axis = plt.subplots(
        figsize=(10, 4.5),
    )

    for vector_store in sorted(dataframe["vector_store"].unique()):
        store_data = dataframe[dataframe["vector_store"] == vector_store].sort_values(
            "datetime"
        )

        values = store_data[metric]

        if percentage:
            values = values * 100

        axis.plot(
            store_data["datetime"],
            values,
            marker="o",
            label=vector_store,
        )

    axis.set_title(title)
    axis.set_xlabel("Execução")
    axis.set_ylabel(y_label)
    axis.grid(
        visible=True,
        alpha=0.25,
    )
    axis.legend()
    axis.tick_params(
        axis="x",
        rotation=30,
    )

    figure.tight_layout()

    st.pyplot(
        figure,
        use_container_width=True,
    )

    plt.close(figure)


def render_trend_charts(
    dataframe: pd.DataFrame,
) -> None:
    st.subheader("Tendências")

    left_column, right_column = st.columns(2)

    with left_column:
        render_line_chart(
            dataframe=dataframe,
            metric="score",
            title="Score por vector store",
            y_label="Score (%)",
            percentage=True,
        )

    with right_column:
        render_line_chart(
            dataframe=dataframe,
            metric="latency",
            title="Latência total",
            y_label="Segundos",
        )

    left_column, right_column = st.columns(2)

    with left_column:
        render_line_chart(
            dataframe=dataframe,
            metric="retrieval_latency",
            title="Latência de retrieval",
            y_label="Segundos",
        )

    with right_column:
        render_line_chart(
            dataframe=dataframe,
            metric="cost",
            title="Custo por execução",
            y_label="USD",
        )

    render_line_chart(
        dataframe=dataframe,
        metric="tokens",
        title="Uso médio de tokens",
        y_label="Tokens",
    )


def get_latest_rows(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    latest_timestamp = dataframe["datetime"].max()

    return dataframe[dataframe["datetime"] == latest_timestamp].copy()


def get_best_stores(
    dataframe: pd.DataFrame,
    metric: str,
    mode: str,
) -> tuple[list[str], float]:
    if mode == "max":
        best_value = dataframe[metric].max()
    else:
        best_value = dataframe[metric].min()

    winners = dataframe[dataframe[metric] == best_value]["vector_store"].tolist()

    return winners, float(best_value)


def render_rankings(
    dataframe: pd.DataFrame,
) -> None:
    st.subheader("Rankings do último benchmark")

    latest = get_latest_rows(dataframe)

    score_stores, score_value = get_best_stores(
        latest,
        metric="score",
        mode="max",
    )

    latency_stores, latency_value = get_best_stores(
        latest,
        metric="latency",
        mode="min",
    )

    retrieval_stores, retrieval_value = get_best_stores(
        latest,
        metric="retrieval_latency",
        mode="min",
    )

    cost_stores, cost_value = get_best_stores(
        latest,
        metric="cost",
        mode="min",
    )

    token_stores, token_value = get_best_stores(
        latest,
        metric="tokens",
        mode="min",
    )

    has_multiple_runs = latest["runs"].max() > 1

    columns = st.columns(5)

    columns[0].success(
        f"🏆 Melhor score\n\n**{', '.join(score_stores)}**\n\n{score_value:.2%}"
    )

    columns[1].info(
        f"⚡ Menor latência\n\n**{', '.join(latency_stores)}**\n\n{latency_value:.4f}s"
    )

    columns[2].info(
        "🔎 Melhor retrieval\n\n"
        f"**{', '.join(retrieval_stores)}**\n\n"
        f"{retrieval_value:.4f}s"
    )

    columns[3].warning(
        f"💰 Menor custo\n\n**{', '.join(cost_stores)}**\n\n${cost_value:.8f}"
    )

    columns[4].warning(
        f"🧠 Menor uso de tokens\n\n**{', '.join(token_stores)}**\n\n{token_value:.2f}"
    )

    if has_multiple_runs:
        stable_stores, stable_value = get_best_stores(
            latest,
            metric="latency_std",
            mode="min",
        )

        st.success(
            "📐 Menor variação de latência: "
            f"**{', '.join(stable_stores)}** "
            f"({stable_value:.4f}s)"
        )
    else:
        st.caption("A estabilidade exige pelo menos duas rodadas por vector store.")


def render_latest_comparison(
    dataframe: pd.DataFrame,
) -> None:
    st.subheader("Comparação do último benchmark")

    latest = get_latest_rows(dataframe)

    comparison = latest[
        [
            "vector_store",
            "runs",
            "score",
            "latency",
            "latency_std",
            "retrieval_latency",
            "rerank_latency",
            "llm_latency",
            "tokens",
            "cost",
            "fallbacks",
        ]
    ].copy()

    comparison = comparison.rename(
        columns={
            "vector_store": "Vector Store",
            "runs": "Runs",
            "score": "Score",
            "latency": "Latency",
            "latency_std": "Latency StdDev",
            "retrieval_latency": "Retrieval",
            "rerank_latency": "Rerank",
            "llm_latency": "LLM",
            "tokens": "Tokens",
            "cost": "Cost",
            "fallbacks": "Fallbacks",
        }
    )

    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score": st.column_config.ProgressColumn(
                format="%.2f",
                min_value=0.0,
                max_value=1.0,
            ),
            "Latency": st.column_config.NumberColumn(
                format="%.4f s",
            ),
            "Latency StdDev": (
                st.column_config.NumberColumn(
                    format="%.4f s",
                )
            ),
            "Retrieval": (
                st.column_config.NumberColumn(
                    format="%.4f s",
                )
            ),
            "Rerank": st.column_config.NumberColumn(
                format="%.4f s",
            ),
            "LLM": st.column_config.NumberColumn(
                format="%.4f s",
            ),
            "Tokens": st.column_config.NumberColumn(
                format="%.2f",
            ),
            "Cost": st.column_config.NumberColumn(
                format="$%.8f",
            ),
        },
    )


def render_history_table(
    dataframe: pd.DataFrame,
) -> None:
    st.subheader("Histórico completo")

    history = dataframe[
        [
            "datetime",
            "vector_store",
            "runs",
            "score",
            "score_min",
            "score_max",
            "latency",
            "latency_min",
            "latency_max",
            "latency_std",
            "retrieval_latency",
            "retrieval_std",
            "rerank_latency",
            "llm_latency",
            "tokens",
            "cost",
            "fallbacks",
        ]
    ].copy()

    history["datetime"] = history["datetime"].apply(format_timestamp)

    history = history.rename(
        columns={
            "datetime": "Timestamp",
            "vector_store": "Vector Store",
            "runs": "Runs",
            "score": "Score",
            "score_min": "Score Min",
            "score_max": "Score Max",
            "latency": "Latency",
            "latency_min": "Latency Min",
            "latency_max": "Latency Max",
            "latency_std": "Latency StdDev",
            "retrieval_latency": "Retrieval",
            "retrieval_std": "Retrieval StdDev",
            "rerank_latency": "Rerank",
            "llm_latency": "LLM",
            "tokens": "Tokens",
            "cost": "Cost",
            "fallbacks": "Fallbacks",
        }
    )

    history = history.sort_values(
        "Timestamp",
        ascending=False,
    )

    st.dataframe(
        history,
        use_container_width=True,
        hide_index=True,
    )

    csv_data = history.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Baixar histórico em CSV",
        data=csv_data,
        file_name="benchmark_history.csv",
        mime="text/csv",
    )


def render_sidebar(
    dataframe: pd.DataFrame,
) -> tuple[list[str], int | None]:
    st.sidebar.header("Filtros")

    available_stores = sorted(dataframe["vector_store"].unique())

    selected_stores = st.sidebar.multiselect(
        "Vector stores",
        options=available_stores,
        default=available_stores,
    )

    history_options = {
        "Últimos 3": 3,
        "Últimos 5": 5,
        "Últimos 10": 10,
        "Todos": None,
    }

    selected_history = st.sidebar.selectbox(
        "Quantidade de benchmarks",
        options=list(history_options.keys()),
        index=3,
    )

    st.sidebar.divider()

    if st.sidebar.button(
        "Atualizar dados",
        use_container_width=True,
    ):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.caption(f"API: {API_BASE_URL}")

    return (
        selected_stores,
        history_options[selected_history],
    )


def render_empty_state() -> None:
    st.warning("Nenhum benchmark foi encontrado.")

    st.info(
        "Execute o benchmark antes de abrir "
        "o dashboard:\n\n"
        "`python -m benchmarks.run --runs 3`"
    )


def main() -> None:
    st.title("📊 RAG Benchmark Dashboard")

    st.caption(
        "Comparação histórica de qualidade, latência, retrieval, custo e tokens."
    )

    try:
        dashboard_data = load_dashboard_data()
    except requests.ConnectionError:
        st.error("Não foi possível conectar à API.")

        st.code("python -m uvicorn app.api.main:app --reload")

        st.stop()
    except requests.HTTPError as error:
        st.error(f"A API retornou um erro ao carregar os benchmarks: {error}")

        st.stop()
    except (
        requests.RequestException,
        ValueError,
    ) as error:
        st.error(f"Não foi possível carregar os dados: {error}")

        st.stop()

    dataframe = build_dataframe(dashboard_data)

    if dataframe.empty:
        render_empty_state()
        st.stop()

    selected_stores, history_limit = render_sidebar(dataframe)

    if not selected_stores:
        st.warning("Selecione pelo menos um vector store.")

        st.stop()

    filtered_dataframe = filter_dataframe(
        dataframe=dataframe,
        selected_stores=selected_stores,
        history_limit=history_limit,
    )

    if filtered_dataframe.empty:
        render_empty_state()
        st.stop()

    render_latest_benchmark_cards(filtered_dataframe)

    st.divider()

    render_rankings(filtered_dataframe)

    st.divider()

    render_trend_charts(filtered_dataframe)

    st.divider()

    render_latest_comparison(filtered_dataframe)

    st.divider()

    render_history_table(filtered_dataframe)


if __name__ == "__main__":
    main()
