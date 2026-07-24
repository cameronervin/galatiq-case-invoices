from pathlib import Path

from backend.app.infrastructure.graph.provider import GraphProvider


def test_graph_provider_reuses_compiled_graph(tmp_path: Path) -> None:
    provider = GraphProvider(tmp_path / "app.db")

    try:
        graph = provider.invoice_graph()

        assert graph is provider.invoice_graph()
    finally:
        provider.close()


def test_graph_exposes_the_take_home_agent_roles(tmp_path: Path) -> None:
    provider = GraphProvider(tmp_path / "app.db")

    try:
        node_names = set(provider.invoice_graph().get_graph().nodes)
    finally:
        provider.close()

    assert {
        "extraction_agent",
        "validation_agent",
        "approval_agent",
        "critic_agent",
        "payment_agent",
    } <= node_names
