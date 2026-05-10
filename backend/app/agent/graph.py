try:
    from langgraph.graph import END, START, StateGraph

    from app.agent.state import AdhikarAgentState

    def build_agent_graph():
        async def pass_through(state: AdhikarAgentState) -> AdhikarAgentState:
            return state

        graph = StateGraph(AdhikarAgentState)
        for node in [
            "load_session",
            "extract_profile_facts",
            "detect_life_event",
            "merge_profile_update",
            "compute_candidate_schemes",
            "compute_profile_completeness",
            "should_match_or_ask",
            "select_next_question",
            "run_eligibility_match",
            "format_result",
            "persist_session",
        ]:
            graph.add_node(node, pass_through)
        graph.add_edge(START, "load_session")
        graph.add_edge("load_session", "extract_profile_facts")
        graph.add_edge("extract_profile_facts", "detect_life_event")
        graph.add_edge("detect_life_event", "merge_profile_update")
        graph.add_edge("merge_profile_update", "compute_candidate_schemes")
        graph.add_edge("compute_candidate_schemes", "compute_profile_completeness")
        graph.add_edge("compute_profile_completeness", "should_match_or_ask")
        graph.add_conditional_edges("should_match_or_ask", lambda state: "match" if state.get("profile_completeness", 0) >= 75 else "ask", {"match": "run_eligibility_match", "ask": "select_next_question"})
        graph.add_edge("run_eligibility_match", "format_result")
        graph.add_edge("select_next_question", "persist_session")
        graph.add_edge("format_result", "persist_session")
        graph.add_edge("persist_session", END)
        return graph.compile()

except Exception:  # pragma: no cover
    def build_agent_graph():
        return None
