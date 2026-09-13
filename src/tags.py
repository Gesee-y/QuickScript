  # ###################################################################################################################################################################### # 
 # ############################################################################ TAGS GENERATOR ########################################################################## #
# ###################################################################################################################################################################### #

from collections import deque
from dataclasses import dataclass
from enum import Enum
import os

class IncoherenceKind(Enum):
    UNKNOWN_TAG = "TAG_INEXISTANT"
    INCOMPLETE_PATH = "INCOMPLETE_PATH"
    INEXISTANT_LINK = "INEXISTANT_LINK"

@dataclass
class TagIncoherence:
	kind: IncoherenceKind
	name: str
	from_tag: str
	possible_path: list[list[str]]

#
@dataclass
class TagNode:
    id: int
    name: str
    parent: int
    children: set[int]

#
@dataclass
class TagGraph:
	nodes: list[TagNode]
	node_to_id: dict[str, int]

@dataclass
class SuggestionResult:
    result: list[str]
    ambiguious_tags: list[str]

def newTagGraph() -> TagGraph:
	return TagGraph(nodes=[TagNode(id=0, name="", parent=-1, children=set())], node_to_id={"": 0})

def add_node(tree: TagGraph, parent: int, name: str) -> int:
	cid = tree.node_to_id.get(name, -1)

	if cid < 0:
		cid = len(tree.nodes)	
		tree.nodes.append(TagNode(id=cid, name=name, parent=parent, children=set()))
		tree.node_to_id[name] = cid
	
	tree.nodes[parent].children.add(cid)
	return cid

def fetch_tags(path: str) -> TagGraph:
    result = newTagGraph()
    path_to_id: dict[str, int] = {path: 0}

    for root, subfolders, _ in os.walk(path):
        current_id = path_to_id[root]

        for folder in subfolders:
            child_id = add_node(result, current_id, folder)
            full_child_path = os.path.join(root, folder)
            path_to_id[full_child_path] = child_id

    return result

def _find_path(
    graph: TagGraph,
    start_id: int,
    target_id: int,
    id_to_node: dict[int, str],
    max_depth: int = 5,
) -> list[list[str]]:
    """the list of all possible paths between 2 point in the TagGraph through BFS."""
    paths: list[list[str]] = []
    
    queue: deque[tuple[int, list[str]]] = deque(
        [(start_id, [id_to_node[start_id]])]
    )

    while queue:
        current_id, path = queue.popleft()

        if current_id == target_id:
            paths.append(path)
            continue

        for child_id in graph.nodes[current_id].children:
            if id_to_node[child_id] not in path:
                queue.append((child_id, path + [id_to_node[child_id]]))

    return paths


def validate_tags(
    tags: TagGraph, sequence: list[str]
) -> list[TagIncoherence]:
    errors: list[TagIncoherence] = []
    id_to_node: dict[int, str] = {v: k for k, v in tags.node_to_id.items()}

    # 1. PASSE 1 : Search unknown tags
    for tag_name in sequence:
        if tag_name not in tags.node_to_id:
            errors.append(
                TagIncoherence(
                    kind=IncoherenceKind.UNKNOWN_TAG,
                    name=tag_name,
                    from_tag="",
                    possible_path=[],
                )
            )

    if errors:
        return errors

    # 2. PASSE 2 : Make sure paths are valid
    current_node_id = 0

    for tag_name in sequence:
        target_node_id = tags.node_to_id[tag_name]
        current_node = tags.nodes[current_node_id]

        if target_node_id not in current_node.children:
            possible_path = _find_path(
                tags, current_node_id, target_node_id, id_to_node
            )

            if possible_path:        
                errors.append(
                    TagIncoherence(
                        kind=IncoherenceKind.INCOMPLETE_PATH,
                        name=tag_name,
                        from_tag="",
                        possible_path=possible_path,
                    )
                )
            else:
                errors.append(
                    TagIncoherence(
                        kind=IncoherenceKind.INEXISTANT_LINK,
                        name=tag_name,
                        from_tag=id_to_node[current_node_id],
                        possible_path=[],
                    )
                )

            break

        current_node_id = target_node_id

    return errors

def get_depth(tags: TagGraph, d: str) -> int: 
    node_id = tags.node_to_id[d]
    res = 0

    while node_id != 0:
        node_id = tags.nodes[node_id].parent
        res += 1

    return res


def sort_tags(tags: TagGraph, data: list[str]):
    data.sort(key = lambda d: get_depth(tags, d))


def get_path_as_name(tags: TagGraph, node_id: int) -> list[str]:
    cid = node_id
    path: list[str] = []

    while cid != 0:
        path.append(tags.nodes[cid].name)
        cid = tags.nodes[cid].parent

    return path

def get_path_as_id(tags: TagGraph, node_id: int) -> list[int]:
    cid = node_id
    path: list[int] = []

    while cid != 0:
        path.append(cid)
        cid = tags.nodes[cid].parent

    return path

def get_path_score(tags: TagGraph, node_id: int, tag_scores: dict[str, float]) -> float:
    cid = node_id
    score = 0.0

    while cid != 0:
        t = tags.nodes[cid].name
        score += tag_scores.get(t, 0.0)
        cid = tags.nodes[cid].parent

    return score
        
def build_suggestion(tags: TagGraph, data: dict[str, float]) -> list[SuggestionResult]:
    # Cumulative branch scores from node to subtree leaves
    best_score: dict[int, float] = {}
    data_tags = list(data.keys())
    max_score = 0.0

    for t in data_tags:
        nid = tags.node_to_id[t]
        node_score = get_path_score(tags, nid, data)
        best_score[nid] = node_score

        if node_score > max_score:
            max_score = node_score

    # If there is no node or no high enough score
    if max_score == 0.0:
        return []

    best_path_ids = [leaf_id for leaf_id in best_score.keys() if best_score[leaf_id] == max_score]
    ambiguous_set: set[str] = set()

    if len(best_path_ids) > 1:
        for leaf_id in best_path_ids:
            path_tags = get_path_as_name(tags, leaf_id)
            for tag in path_tags:
                # Include zero-score tags that create ambiguity between max-scoring paths
                if data.get(tag, 0.0) == 0.0:
                    ambiguous_set.add(tag)

        if len(ambiguous_set) > 0:
            chosen_path = get_path_as_name(tags, best_path_ids[0])
        
            return [SuggestionResult(
                result=chosen_path,
                ambiguious_tags=list(ambiguous_set)
            )]

    # 2. Identify leaf nodes (nodes with no children)
    leaf_ids = [nid for nid in best_path_ids if not tags.nodes[nid].children]
    subtree_ids = [nid for nid in best_path_ids if tags.nodes[nid].children]
    
    # If there is leaf and subtreem we take the subtree since it have an higher ambiguity
    if subtree_ids:
        subtree = subtree_ids[0]

        for nid in tags.nodes[subtree].children:
            ambiguous_set.add(tags.nodes[nid].name)

        return [SuggestionResult(result=get_path_as_name(tags, subtree), ambiguious_tags=list(ambiguous_set))]

    result: list[SuggestionResult] = []
    for leaf_id in leaf_ids:
        result.append(SuggestionResult(result=get_path_as_name(tags, leaf_id), ambiguious_tags=[]))

    return result
