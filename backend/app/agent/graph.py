try:
    from langgraph.graph import END, START, StateGraph

    from app.agent.state import AdhikarAgentState

    NODE_ORDER = [
        "load_session",
        "extract_profile_facts",
        "detect_life_event",
        "process_pending_confirmation",
        "retrieve_semantic_candidates",
        "merge_profile_update",
        "compute_profile_completeness",
        "run_eligibility_match",
        "choose_response",
        "persist_session",
    ]

    def build_agent_graph(nodes: dict | None = None):
        if nodes is None:
            from app.services.sessions.session_service import agent_graph_nodes

            nodes = agent_graph_nodes()
        missing = [name for name in NODE_ORDER if name not in nodes]
        if missing:
            raise ValueError(f"Missing agent graph nodes: {', '.join(missing)}")
        graph = StateGraph(AdhikarAgentState)
        for node in NODE_ORDER:
            graph.add_node(node, nodes[node])
        graph.add_edge(START, "load_session")
        graph.add_edge("load_session", "extract_profile_facts")
        graph.add_edge("extract_profile_facts", "detect_life_event")
        graph.add_edge("detect_life_event", "process_pending_confirmation")
        graph.add_edge("process_pending_confirmation", "retrieve_semantic_candidates")
        graph.add_edge("retrieve_semantic_candidates", "merge_profile_update")
        graph.add_edge("merge_profile_update", "compute_profile_completeness")
        graph.add_edge("compute_profile_completeness", "run_eligibility_match")
        graph.add_edge("run_eligibility_match", "choose_response")
        graph.add_edge("choose_response", "persist_session")
        graph.add_edge("persist_session", END)
        return graph.compile()

except Exception:  # pragma: no cover
    def build_agent_graph(nodes: dict | None = None):
        raise RuntimeError("LangGraph is not available.")
