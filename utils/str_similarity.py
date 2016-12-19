def make_type_consistent(s1, s2):
    """If both objects aren't either both string or unicode instances force them to unicode"""
    if isinstance(s1, str) and isinstance(s2, str): return s1, s2
    elif isinstance(s1, unicode) and isinstance(s2, unicode): return s1, s2
    else: return unicode(s1), unicode(s2)

import difflib
def similarity(a,b):
    if len(a)==0 or len(b)==0:
        return -1.0
    a,b = make_type_consistent(a,b)
    a,b = a.lower(), b.lower()
    match_size = sum([m.size for m in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_matching_blocks()])*1.0
    longer_size, shorter_size = (len(b),len(a)) if len(a)<len(b) else ((len(a),len(b)))
    longer_size = shorter_size if (longer_size/1.5)<=shorter_size else longer_size/1.5
#     return match_size/(longer_size+shorter_size)*2
    return match_size/shorter_size