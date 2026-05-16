import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from langgraph.graph import StateGraph, END
from state import InventoryState
from agents.supervisor import supervisor_node
from agents.inventory import inventory_node
from agents.order import order_node
from agents.restock import restock_node
from agents.report import report_node
from agents.stock_advisor import stock_advisor_node


def route_from_supervisor(state: InventoryState) -> str:
    return state.get("next", "FINISH")


def build_graph() -> StateGraph:
    graph = StateGraph(InventoryState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("inventory", inventory_node)
    graph.add_node("order", order_node)
    graph.add_node("restock", restock_node)
    graph.add_node("report", report_node)
    graph.add_node("stock_advisor", stock_advisor_node)

    graph.set_entry_point("supervisor")

    graph.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "inventory": "inventory",
            "order": "order",
            "restock": "restock",
            "report": "report",
            "stock_advisor": "stock_advisor",
            "FINISH": END,
        },
    )

    for agent in ["inventory", "order", "restock", "report", "stock_advisor"]:
        graph.add_edge(agent, "supervisor")

    return graph.compile()


inventory_graph = build_graph()
