"""Tests for social trust algorithms."""

import pytest
import numpy as np
import scipy.sparse as sp
from trust_network.algorithms.social import EigenTrustAlgorithm, AppleseedAlgorithm, PageRankAlgorithm
from config.settings import EigenTrustConfig, AppleseedConfig, PageRankConfig

class TestEigenTrust:
    """Test EigenTrust algorithm."""
    
    def test_simple_matrix(self):
        """Test EigenTrust on simple matrix."""
        config = EigenTrustConfig()
        algorithm = EigenTrustAlgorithm(config)
        
        # Create simple 3x3 matrix
        matrix = sp.csr_matrix([
            [1.0, 0.8, 0.0],
            [0.6, 1.0, 0.7],
            [0.0, 0.5, 1.0]
        ])
        
        scores = algorithm.compute(matrix)
        
        assert len(scores) == 3
        assert np.all(scores >= 0)
        assert np.abs(scores.sum() - 1.0) < 1e-6  # Should sum to 1
    
    def test_convergence(self):
        """Test that EigenTrust converges."""
        config = EigenTrustConfig()
        config.iterations = 10
        config.alpha = 0.15
        
        algorithm = EigenTrustAlgorithm(config)
        
        # Create random matrix
        np.random.seed(42)
        data = np.random.random((5, 5))
        matrix = sp.csr_matrix(data)
        
        scores = algorithm.compute(matrix)
        
        assert algorithm.iterations_used <= config.iterations
        assert len(scores) == 5
    
    def test_empty_matrix(self):
        """Test EigenTrust on empty matrix."""
        config = EigenTrustConfig()
        algorithm = EigenTrustAlgorithm(config)
        
        matrix = sp.csr_matrix((0, 0))
        scores = algorithm.compute(matrix)
        
        assert len(scores) == 0

class TestAppleseed:
    """Test Appleseed algorithm."""
    
    def test_simple_matrix(self):
        """Test Appleseed on simple matrix."""
        config = AppleseedConfig()
        algorithm = AppleseedAlgorithm(config)
        
        matrix = sp.csr_matrix([
            [1.0, 0.8, 0.0],
            [0.6, 1.0, 0.7],
            [0.0, 0.5, 1.0]
        ])
        
        scores = algorithm.compute(matrix, converters=["node_0"], node_to_idx={"node_0": 0, "node_1": 1, "node_2": 2})
        
        assert len(scores) == 3
        assert np.all(scores >= 0)
        assert np.abs(scores.sum() - 1.0) < 1e-6  # Should sum to 1
    
    def test_seed_node_preference(self):
        """Test that Appleseed gives preference to seed nodes."""
        config = AppleseedConfig()
        config.energy = 0.5  # High decay for clearer signal
        config.iterations = 50
        
        algorithm = AppleseedAlgorithm(config)
        
        # Create matrix where node 0 is well connected
        matrix = sp.csr_matrix([
            [1.0, 1.0, 1.0],
            [0.1, 1.0, 0.1],
            [0.1, 0.1, 1.0]
        ])
        
        scores = algorithm.compute(matrix, converters=["node_0"], node_to_idx={"node_0": 0, "node_1": 1, "node_2": 2})
        
        # Node 0 should have highest score as it's the seed
        assert scores[0] > scores[1]
        assert scores[0] > scores[2]

class TestPageRank:
    """Test PageRank algorithm."""
    
    def test_simple_matrix(self):
        """Test PageRank on simple matrix."""
        config = PageRankConfig()
        algorithm = PageRankAlgorithm(config)
        
        matrix = sp.csr_matrix([
            [1.0, 0.8, 0.0],
            [0.6, 1.0, 0.7],
            [0.0, 0.5, 1.0]
        ])
        
        scores = algorithm.compute(matrix)
        
        assert len(scores) == 3
        assert np.all(scores >= 0)
        assert np.abs(scores.sum() - 1.0) < 1e-6  # Should sum to 1
    
    def test_dangling_nodes(self):
        """Test PageRank with dangling nodes."""
        config = PageRankConfig()
        algorithm = PageRankAlgorithm(config)
        
        # Node 2 is dangling (no outgoing edges)
        matrix = sp.csr_matrix([
            [1.0, 0.5, 0.5],
            [0.5, 1.0, 0.5],
            [0.0, 0.0, 1.0]  # Self-loop only
        ])
        
        scores = algorithm.compute(matrix)
        
        assert len(scores) == 3
        assert np.all(scores >= 0)
        # Should still sum to 1 despite dangling node
        assert np.abs(scores.sum() - 1.0) < 1e-6