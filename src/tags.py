  # ###################################################################################################################################################################### # 
 # ############################################################################ TAGS GENERATOR ########################################################################## #
# ###################################################################################################################################################################### #

from dataclasses import dataclass
import os

#
@dataclass
class TagNode:
	id: int = -1
	children: set[int]

#
@dataclass
class TagGraph:
	nodes: list[TagNode] = [TagNode(id=0, children={})]
	node_to_id: dict[str, int] = {"": 0}

def add_node(tree: TagGraph, parent: int, name: str):
	cid = tree.getOrDefault(name, -1)

	if cid < 0:
		cid = len(tree.nodes)	
		tree.nodes.append(TagNode(id=cid, children={}))
	
	tree.nodes[parent].children.add(cid)

def fetch_tags(path: str) -> TagGraph:
	result = TagGraph()

	for root, subfolder, files in os.walk(path):
		parent = result.get(root, -1)

		for folder in subfolder:
			add_node(result, parent, folder)



	