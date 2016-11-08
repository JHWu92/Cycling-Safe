
def find_tree(messy_tree_df, parent_node='root', lv=1):
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
