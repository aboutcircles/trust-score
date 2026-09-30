"""Tests for core network functionality."""

import pytest
import numpy as np
from trust_network import TrustNetwork
from config.settings import NetworkConfig

class TestTrustNetwork:
    """Test cases for TrustNetwork class."""
    
    def test_empty_network(self):
        """Test creating an empty network."""
        config = NetworkConfig()
        network = TrustNetwork(config)
        
        assert len(network.nodes) == 0
        assert len(network.edges) == 0
        assert len(network.converters) == 0
    
    def test_add_node(self):
        """Test adding nodes to network."""
        config = NetworkConfig()
        network = TrustNetwork(config)
        
        network.add_node("Alice", is_converter=False)
        network.add_node("ConvX", is_converter=True)
        
        assert len(network.nodes) == 2
        assert "Alice" in network.nodes
        assert "ConvX" in network.nodes
        assert "ConvX" in network.converters
        assert "Alice" not in network.converters
    
    def test_add_edge(self):
        """Test adding edges to network."""
        config = NetworkConfig()
        network = TrustNetwork(config)
        
        network.add_edge("Alice", "Bob", 0.8)
        
        assert len(network.edges) == 1
        assert len(network.nodes) == 2  # Nodes created automatically
        
        edge = network.edges[0]
        assert edge.source == "Alice"
        assert edge.target == "Bob"
        assert edge.weight == 0.8
    
    def test_invalid_edge_weight(self):
        """Test that invalid edge weights raise errors."""
        config = NetworkConfig()
        network = TrustNetwork(config)
        
        with pytest.raises(ValueError):
            network.add_edge("Alice", "Bob", 0.0)  # Invalid weight
        
        with pytest.raises(ValueError):
            network.add_edge("Alice", "Bob", 1.5)  # Invalid weight
    
    def test_set_balance(self):
        """Test setting token balances."""
        config = NetworkConfig()
        network = TrustNetwork(config)
        
        network.set_balance("Alice", "T_A", 1000.0)
        
        assert "Alice" in network.balances
        assert "T_A" in network.balances["Alice"]
        assert network.balances["Alice"]["T_A"] == 1000.0
    
    def test_set_conversion_rate(self):
        """Test setting conversion rates."""
        config = NetworkConfig()
        network = TrustNetwork(config)
        
        network.add_node("ConvX", is_converter=True)
        network.set_conversion_rate("ConvX", "T_A", 1.0)
        
        assert "ConvX" in network.rates
        assert "T_A" in network.rates["ConvX"]
        assert network.rates["ConvX"]["T_A"] == 1.0
    
    def test_conversion_rate_non_converter(self):
        """Test that setting rates for non-converters raises error."""
        config = NetworkConfig()
        network = TrustNetwork(config)
        
        network.add_node("Alice", is_converter=False)
        
        with pytest.raises(ValueError):
            network.set_conversion_rate("Alice", "T_A", 1.0)
    
    def test_compute_trust_scores_empty(self):
        """Test computing scores on empty network."""
        config = NetworkConfig()
        network = TrustNetwork(config)
        
        with pytest.raises(ValueError):
            network.compute_trust_scores()
    
    def test_simple_network_scores(self):
        """Test computing scores on a simple network."""
        config = NetworkConfig()
        config.trust_network.algorithms.social = "eigentrust"
        config.trust_network.algorithms.liquidity = "hybrid"
        
        network = TrustNetwork(config)
        
        # Add nodes
        network.add_node("Alice")
        network.add_node("Bob")
        network.add_node("ConvX", is_converter=True)
        
        # Add edges
        network.add_edge("Alice", "Bob", 0.8)
        network.add_edge("ConvX", "Alice", 1.0)
        
        # Add balances and rates
        network.set_balance("Alice", "Alice", 1000)
        network.set_conversion_rate("ConvX", "Alice", 1.0)
        
        # Compute scores
        results = network.compute_trust_scores()
        
        assert len(results.scores) == 3
        assert "Alice" in results.scores
        assert "Bob" in results.scores
        assert "ConvX" in results.scores
        
        # All scores should be between 0 and 1
        for score in results.scores.values():
            assert 0 <= score.composite_score <= 1
            assert 0 <= score.social_score <= 1
            assert 0 <= score.liquidity_score <= 1

@pytest.fixture
def sample_network():
    """Create a sample network for testing."""
    config = NetworkConfig()
    network = TrustNetwork(config)
    
    # Add nodes
    network.add_node("Alice")
    network.add_node("Bob") 
    network.add_node("Charlie")
    network.add_node("ConvX", is_converter=True)
    
    # Add edges
    network.add_edge("Alice", "Bob", 0.9)
    network.add_edge("Bob", "Charlie", 0.8)
    network.add_edge("ConvX", "Alice", 1.0)
    
    # Add balances
    network.set_balance("Alice", "Alice", 1000)
    network.set_balance("Bob", "Bob", 800)
    network.set_balance("Charlie", "Charlie", 600)
    
    # Add rates
    network.set_conversion_rate("ConvX", "Alice", 1.0)
    network.set_conversion_rate("ConvX", "Bob", 0.9)
    
    return network

class TestTrustNetworkWithData:
    """Test network functionality with sample data."""
    
    def test_find_trust_path(self, sample_network):
        """Test finding trust paths."""
        path = sample_network.find_trust_path("Alice", "Charlie")
        
        assert path is not None
        assert path.is_valid
        assert path.nodes[0] == "Alice"
        assert path.nodes[-1] == "Charlie"
        assert path.trust_value > 0
    
    def test_no_path_exists(self, sample_network):
        """Test when no path exists."""
        # Add isolated node
        sample_network.add_node("Isolated")
        
        path = sample_network.find_trust_path("Alice", "Isolated")
        assert path is None
    
    def test_get_ranking(self, sample_network):
        """Test getting node rankings."""
        ranking = sample_network.get_ranking(top_n=3)
        
        assert len(ranking) <= 3
        assert all(isinstance(item, tuple) for item in ranking)
        assert all(len(item) == 2 for item in ranking)
        
        # Check that ranking is sorted
        scores = [score for _, score in ranking]
        assert scores == sorted(scores, reverse=True)
    
    def test_network_statistics(self, sample_network):
        """Test network statistics computation."""
        results = sample_network.compute_trust_scores()
        stats = results.network_stats
        
        assert stats.num_nodes == 4
        assert stats.num_edges == 3
        assert stats.num_converters == 1
        assert 0 <= stats.density <= 1
        assert stats.avg_clustering >= 0