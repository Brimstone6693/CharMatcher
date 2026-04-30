"""
Test suite for Graph Overlord module.
"""

import sys
sys.path.insert(0, '/workspace')

from modules.Graph_Overlord import (
    InterestNode,
    Edge,
    EdgeType,
    InterestGraph,
    TemplateManager,
    GraphCalculator,
)


def test_interest_node():
    """Test InterestNode creation and properties."""
    print("Testing InterestNode...")
    
    # Test basic node creation
    node = InterestNode(id="test1", name="Test Node")
    assert node.id == "test1"
    assert node.name == "Test Node"
    assert node.att == 0.0
    assert node.int == 0.0
    assert not node.locked
    assert node.active
    
    # Test node with user values
    node2 = InterestNode(id="test2", name="Test Node 2", user_att=80.0, user_int=60.0)
    assert node2.user_att == 80.0
    assert node2.user_int == 60.0
    assert node2.user_weight_att == 0.8
    assert node2.user_weight_int == 0.6
    
    # Test automatic weight calculation
    node3 = InterestNode(id="test3", name="Test Node 3", user_att=-50.0)
    assert node3.user_weight_att == 0.5
    assert node3.user_int is not None  # Should be computed
    
    # Test serialization
    data = node2.to_dict()
    node4 = InterestNode.from_dict(data)
    assert node4.id == node2.id
    assert node4.user_att == node2.user_att
    
    print("✓ InterestNode tests passed")


def test_edge():
    """Test Edge creation and properties."""
    print("Testing Edge...")
    
    # Test parent edge creation
    edge = Edge.create_parent_edge("parent1", "child1")
    assert edge.type == EdgeType.PARENT
    assert edge.source_id == "parent1"
    assert edge.target_id == "child1"
    assert edge.w_down_att == 0.7
    assert edge.w_down_int == 0.6
    
    # Test association edge creation
    edge2 = Edge.create_association_edge("node1", "node2", att_level='strong_positive')
    assert edge2.type == EdgeType.ASSOCIATION
    assert edge2.fw_att == 0.9
    assert edge2.bw_att == 0.9
    
    # Test serialization
    data = edge.to_dict()
    edge3 = Edge.from_dict(data)
    assert edge3.source_id == edge.source_id
    assert edge3.type == edge.type
    
    print("✓ Edge tests passed")


def test_graph():
    """Test InterestGraph structure."""
    print("Testing InterestGraph...")
    
    graph = InterestGraph()
    
    # Add nodes using new API
    graph.add_node("root", "Root", is_category=True)
    graph.add_node("child1", "Child 1")
    graph.add_node("child2", "Child 2")
    
    assert len(graph.nodes) == 3
    
    # Add parent edges
    edge1 = Edge.create_parent_edge("root", "child1")
    edge2 = Edge.create_parent_edge("root", "child2")
    
    assert graph.add_edge(edge1)
    assert graph.add_edge(edge2)
    
    # Verify structure
    assert graph.get_parent("child1") == "root"
    assert graph.get_parent("child2") == "root"
    assert "child1" in graph.get_children("root")
    assert "child2" in graph.get_children("root")
    
    # Get root nodes
    roots = graph.get_root_nodes()
    assert "root" in roots
    
    # Test deactivation
    graph.set_node_active("root", False, recursive=True)
    assert not graph.is_node_effectively_active("child1")
    assert not graph.is_node_effectively_active("child2")
    
    # Test serialization
    json_str = graph.to_json()
    graph2 = InterestGraph.from_json(json_str)
    assert len(graph2.nodes) == 3
    
    print("✓ InterestGraph tests passed")


def test_calculator():
    """Test GraphCalculator propagation."""
    print("Testing GraphCalculator...")
    
    graph = InterestGraph()
    
    # Create simple tree using new API
    graph.add_node("root", "Root", is_category=True, user_att=80.0, user_int=70.0)
    graph.add_node("child1", "Child 1")
    graph.add_node("child2", "Child 2")
    
    graph.add_edge(Edge.create_parent_edge("root", "child1"))
    graph.add_edge(Edge.create_parent_edge("root", "child2"))
    
    # Run calculator
    calculator = GraphCalculator(graph)
    iterations = calculator.calculate()
    
    assert iterations > 0
    assert iterations <= 100
    
    # Check that values propagated
    assert graph.nodes["child1"].att != 0.0 or graph.nodes["child1"].int != 0.0
    assert graph.nodes["child2"].att != 0.0 or graph.nodes["child2"].int != 0.0
    
    # Values should be in valid ranges
    assert -100 <= graph.nodes["child1"].att <= 100
    assert 0 <= graph.nodes["child1"].int <= 100
    assert -100 <= graph.nodes["child2"].att <= 100
    assert 0 <= graph.nodes["child2"].int <= 100
    
    print(f"  Converged in {iterations} iterations")
    print(f"  Root: att={graph.nodes['root'].att:.2f}, int={graph.nodes['root'].int:.2f}")
    print(f"  Child1: att={graph.nodes['child1'].att:.2f}, int={graph.nodes['child1'].int:.2f}")
    print(f"  Child2: att={graph.nodes['child2'].att:.2f}, int={graph.nodes['child2'].int:.2f}")
    
    print("✓ GraphCalculator tests passed")


def test_templates():
    """Test TemplateManager."""
    print("Testing TemplateManager...")
    
    manager = TemplateManager()
    manager.create_builtin_templates()
    
    # Check templates were created
    assert "sports" in manager.templates
    assert "intellectual_games" in manager.templates
    assert "creative_arts" in manager.templates
    
    # Get sports template
    sports = manager.get_template("sports")
    assert sports is not None
    assert len(sports.nodes) > 0
    assert len(sports.edges) > 0
    
    # Insert template into graph
    graph = InterestGraph()
    graph.add_node("root", "My Interests", is_category=True)
    
    inserted = manager.insert_template(sports, graph, parent_node_id="root")
    
    assert len(inserted) > 0
    assert len(graph.nodes) == len(inserted) + 1  # +1 for root
    
    print(f"  Inserted {len(inserted)} nodes from sports template")
    print("✓ TemplateManager tests passed")


def test_full_workflow():
    """Test complete workflow scenario."""
    print("Testing full workflow...")
    
    # Create graph
    graph = InterestGraph()
    
    # Create template manager and load builtins
    manager = TemplateManager()
    manager.create_builtin_templates()
    
    # Add root node using new API
    graph.add_node("user_interests", "User Interests", is_category=True)
    
    # Insert multiple templates
    sports_inserted = manager.insert_template(
        manager.get_template("sports"),
        graph,
        parent_node_id="user_interests"
    )
    
    games_inserted = manager.insert_template(
        manager.get_template("intellectual_games"),
        graph,
        parent_node_id="user_interests"
    )
    
    print(f"  Total nodes: {len(graph.nodes)}")
    print(f"  Sports nodes: {len(sports_inserted)}")
    print(f"  Games nodes: {len(games_inserted)}")
    
    # User rates some nodes
    chess_node_id = next((nid for nid in graph.nodes if "chess" in nid), None)
    if chess_node_id:
        graph.nodes[chess_node_id].user_att = 90.0
        graph.nodes[chess_node_id].user_int = 85.0
    
    football_node_id = next((nid for nid in graph.nodes if "football" in nid), None)
    if football_node_id:
        graph.nodes[football_node_id].user_att = 60.0
        graph.nodes[football_node_id].user_int = 70.0
    
    # Calculate
    calculator = GraphCalculator(graph)
    iterations = calculator.calculate()
    
    print(f"  Calculation converged in {iterations} iterations")
    
    # Show results
    high_interest = [
        (node.name, node.att, node.int)
        for node in graph.nodes.values()
        if node.int > 50 and node.att > 0
    ]
    
    print(f"  High interest nodes: {len(high_interest)}")
    
    # Check uncertainty
    uncertain = [node for node in graph.nodes.values() if node.needs_clarification]
    print(f"  Uncertain nodes: {len(uncertain)}")
    
    # Test deactivation
    if sports_inserted:
        graph.set_node_active(sports_inserted[0], False, recursive=True)
        active_count = len(graph.get_active_nodes())
        print(f"  Active nodes after deactivating sports: {active_count}")
    
    print("✓ Full workflow tests passed")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Graph Overlord Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_interest_node()
        test_edge()
        test_graph()
        test_calculator()
        test_templates()
        test_full_workflow()
        
        print()
        print("=" * 60)
        print("All tests passed successfully! ✓")
        print("=" * 60)
        return True
    except Exception as e:
        print()
        print("=" * 60)
        print(f"Test failed with error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
