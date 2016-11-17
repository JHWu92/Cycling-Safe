
def find_tree_buggy(messy_tree_df, parent_node='root', lv=1):
    """
    the nodes which become parent-less 
    after we remove the top level parent, 
    are the children of the removed parent
    """
    import pandas as pd
    new_tree = []
    all_nodes = set(messy_tree_df.child)
    nodes_have_true_parent = set(messy_tree_df[messy_tree_df.child!=messy_tree_df.parent].child)
    nodes_without_parent = all_nodes - nodes_have_true_parent
    for child in nodes_without_parent:
        new_tree.append((child,parent_node))
    remaining_nodes = messy_tree_df[~messy_tree_df.child.isin(nodes_without_parent)]
    for node in list(nodes_without_parent):
        # remove the inode
        sub_tree = find_tree(remaining_nodes[remaining_nodes.parent!=node],node,lv+1)
        new_tree.extend(sub_tree)
    if lv!=1:
        return new_tree
    return pd.DataFrame(new_tree,columns=['child','parent'])



def find_direct_parent(tree, node, direct_parents):
    if node in direct_parents:
        return direct_parents[node]
    node_parents = tree[tree.node==node].parent.values
    if len(node_parents)==0:
        direct_parents[node]=(node, -1,1)
        return direct_parents[node]
    node_parents_lv = [find_direct_parent(tree, p, direct_parents)[2] for p in node_parents]
    max_lv = max(node_parents_lv)
    direct_parent = node_parents[node_parents_lv.index(max_lv)]
    direct_parents[node] = (node, direct_parent, max_lv+1)
    return (node, direct_parent, max_lv+1)

def find_tree(messy_tree_df):
    import pandas as pd
    direct_parents={}
    all_nodes = set(messy_tree_df.node)
    messy_tree_df = messy_tree_df[messy_tree_df.node!=messy_tree_df.parent].copy()
    new_tree = []
    for node in all_nodes:
        x = find_direct_parent(messy_tree_df, node, direct_parents)
        new_tree.append(x)
    return pd.DataFrame(new_tree,columns=['node','parent','lv']).sort('lv')
