import pytest
from extract_save import Node, extract_schemes, extract_secrets, extract_relations, extract_dynasties, extract_artifacts, _character_summary

def make_node(kind, name=None, value=None):
    n = Node(kind)
    if value is not None:
        n.value = value
    n.children = {} if kind == "block" else ([] if kind == "list" else None)
    return n

def test_schemes_defaults():
    root = make_node("block")
    schemes = make_node("block")
    active = make_node("block")
    root.children["schemes"] = schemes
    schemes.children["active"] = active
    
    s1 = make_node("block")
    s1.children["type"] = make_node("scalar", value="murder")
    s1.children["owner"] = make_node("scalar", value=100)
    active.children["s1"] = s1
    
    res = extract_schemes(root, [100])
    s1_res = res["schemes"][0]
    assert s1_res["progress"] is None
    assert s1_res["secrecy"] is None

def test_schemes_missing_type_global():
    root = make_node("block")
    schemes = make_node("block")
    active = make_node("block")
    root.children["schemes"] = schemes
    schemes.children["active"] = active
    
    s1 = make_node("block")
    s1.children["owner"] = make_node("scalar", value=999) # Not related!
    active.children["s1"] = s1
    
    res = extract_schemes(root, [100])
    assert res["missing_type"] == 1

def test_relations_nested():
    root = make_node("block")
    rel = make_node("block")
    act = make_node("list")
    root.children["relations"] = rel
    rel.children["active_relations"] = act
    
    r1 = make_node("block")
    r1.children["first"] = make_node("scalar", value=100)
    r1.children["second"] = make_node("scalar", value=200)
    
    alliances = make_node("list")
    ablock = make_node("block")
    ablock.children["allied_through_0"] = make_node("scalar", value=100)
    ablock.children["allied_through_1"] = make_node("scalar", value=300)
    alliances.children.append(ablock)
    r1.children["alliances"] = alliances
    
    hook = make_node("block")
    hook.children["type"] = make_node("scalar", value="favor_hook")
    hook.children["expiration_date"] = make_node("scalar", value="949.5.14")
    r1.children["active_hook_1"] = hook
    
    act.children.append(r1)
    
    res = extract_relations(root, [100])
    assert res["total"] == 1
    assert len(res["relations"]) == 1
    r = res["relations"][0]
    assert 100 in r["alliances"]
    assert r["hooks"][0]["type"] == "favor_hook"
    assert r["hooks"][0]["expiration_date"] == "949.5.14"

def test_dynasties_list_perks():
    root = make_node("block")
    dyn = make_node("block")
    dd = make_node("block")
    root.children["dynasties"] = dyn
    dyn.children["dynasties"] = dd
    
    d1 = make_node("block")
    perk = make_node("list")
    perk.children.append(make_node("scalar", value="blood_1"))
    perk.children.append(make_node("scalar", value="blood_2"))
    d1.children["perk"] = perk
    dd.children["200"] = d1
    
    res = extract_dynasties(root, 200)
    assert res["dynasty"]["perks"] == ["blood_1", "blood_2"]

def test_secrets_participants_list():
    root = make_node("block")
    secrets_node = make_node("block")
    root.children["secrets"] = secrets_node
    
    s = make_node("list")
    secrets_node.children["secrets"] = s
    
    # Secret with participant
    sec = make_node("block")
    sec.children["type"] = make_node("scalar", value="secret_lover")
    parts = make_node("block")
    parts.children["0"] = make_node("scalar", value=100)
    parts.children["1"] = make_node("scalar", value=200)
    sec.children["participants"] = parts
    
    s.children.append(sec)
    
    res = extract_secrets(root, [100])
    assert len(res["secrets"]) == 1
    assert 100 in res["secrets"][0]["participants"]
    assert 200 in res["secrets"][0]["participants"]

def test_artifacts_no_character_dep():
    root = make_node("block")
    arts = make_node("block")
    aa = make_node("block")
    root.children["artifacts"] = arts
    arts.children["artifacts"] = aa
    
    a1 = make_node("block")
    a1.children["durability"] = make_node("scalar", value=100)
    a1.children["owner"] = make_node("scalar", value=100)
    aa.children["300"] = a1
    
    res = extract_artifacts(root, [100])
    assert res["total"] == 1
    assert len(res["artifacts"]) == 1
    assert res["artifacts"][0]["is_equipped"] == "missing"
