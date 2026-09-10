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
	children: set[int]

#
@dataclass
class TagGraph:
	nodes: list[TagNode]
	node_to_id: dict[str, int]

def newTagGraph() -> TagGraph:
	return TagGraph(nodes=[TagNode(id=0, children=set())], node_to_id={"": 0})

def add_node(tree: TagGraph, parent: int, name: str) -> int:
	cid = tree.node_to_id.get(name, -1)

	if cid < 0:
		cid = len(tree.nodes)	
		tree.nodes.append(TagNode(id=cid, children=set()))
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
    
    # Queue BFS stocke des tuples : (node_id_actuel, chemin_de_noms_parcouru)
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

    for i, tag_name in enumerate(sequence):
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