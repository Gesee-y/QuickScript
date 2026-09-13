import unittest
from src.tags import (
    IncoherenceKind,
    newTagGraph,
    add_node,
    validate_tags,
)


class TestTagEngine(unittest.TestCase):

    def setUp(self) -> None:
        """Set up a deterministic TagGraph fixture before each test execution."""
        # Graph Structure:
        # Root (id=0)
        # ├── L1 (id=1)
        # │   ├── CS (id=2)
        # │   │   └── Algo (id=4)
        # │   └── Math (id=3)
        # │       └── Algo (id=4)  <-- Shared node
        # └── Literature (id=5)
        self.graph = newTagGraph()

        # Build Graph
        self.l1_id = add_node(self.graph, parent=0, name="L1")
        self.cs_id = add_node(self.graph, parent=self.l1_id, name="CS")
        self.math_id = add_node(self.graph, parent=self.l1_id, name="Math")
        self.lit_id = add_node(self.graph, parent=0, name="Literature")

        # "Algo" is reachable via both CS and Math
        self.algo_id_cs = add_node(self.graph, parent=self.cs_id, name="Algo")
        self.algo_id_math = add_node(
            self.graph, parent=self.math_id, name="Algo"
        )

    # --- GRAPH CONSTRUCTION TESTS ---

    def test_add_node_deduplication(self) -> None:
        """Verify that adding an existing node name reuses its assigned node_id."""
        initial_node_count = len(self.graph.nodes)
        existing_id = add_node(self.graph, parent=self.l1_id, name="CS")

        self.assertEqual(existing_id, self.cs_id)
        self.assertEqual(len(self.graph.nodes), initial_node_count)

    # --- VALIDATION: SUCCESS CASES ---

    def test_validate_tags_valid_sequence(self) -> None:
        """Verify that a fully connected sequential path returns zero incoherences."""
        valid_path = ["L1", "CS", "Algo"]
        errors = validate_tags(self.graph, valid_path)

        self.assertEqual(len(errors), 0)

    # --- VALIDATION: UNKNOWN TAGS ---

    def test_validate_tags_unknown_tag(self) -> None:
        """Verify that a non-existent tag returns UNKNOWN_TAG with an empty possible_path."""
        invalid_path = ["L1", "CyberSecurity", "Algo"]
        errors = validate_tags(self.graph, invalid_path)

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].kind, IncoherenceKind.UNKNOWN_TAG)
        self.assertEqual(errors[0].name, "CyberSecurity")
        self.assertEqual(errors[0].possible_path, [])

    def test_validate_tags_unknown_tag_short_circuits(self) -> None:
        """Verify that UNKNOWN_TAG checks halt further path validation."""
        invalid_path = ["NonExistentRoot", "CS"]
        errors = validate_tags(self.graph, invalid_path)

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].kind, IncoherenceKind.UNKNOWN_TAG)

    # --- VALIDATION: INCOMPLETE PATHS (BFS RESOLUTION) ---

    def test_validate_tags_incomplete_path_single_gap(self) -> None:
        """Verify that skipping an intermediate node produces the corrected BFS path."""
        # Skipping 'CS' or 'Math' directly from L1 -> Algo
        incomplete_path = ["L1", "Algo"]
        errors = validate_tags(self.graph, incomplete_path)

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].kind, IncoherenceKind.INCOMPLETE_PATH)
        self.assertEqual(errors[0].name, "Algo")

        # Expect BFS to find both valid paths: [L1, CS, Algo] and [L1, Math, Algo]
        expected_cs_path = ["L1", "CS", "Algo"]
        expected_math_path = ["L1", "Math", "Algo"]

        self.assertIn(expected_cs_path, errors[0].possible_path)
        self.assertIn(expected_math_path, errors[0].possible_path)

    # --- VALIDATION: INEXISTANT LINKS ---

    def test_validate_tags_inexistant_link(self) -> None:
        """Verify that jumping between unreachable subtrees yields INEXISTANT_LINK."""
        # Literature and Algo have no valid topological path connecting them
        disconnected_path = ["Literature", "Algo"]
        errors = validate_tags(self.graph, disconnected_path)

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].kind, IncoherenceKind.INEXISTANT_LINK)
        self.assertEqual(errors[0].name, "Algo")
        self.assertEqual(errors[0].possible_path, [])


if __name__ == "__main__":
    unittest.main()