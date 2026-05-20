import pandas as pd
import json


def main() -> pd.DataFrame:
    names_sp_dirty = list(pd.read_csv("./data/schichtplan_overview.csv")["name"])
    names_hzr_dirty = list(pd.read_csv("./data/hzr.csv")["name"].str.upper())
    names_registered = []
    for name_hzr_dirty in names_hzr_dirty:
        names_registered.append(name_hzr_dirty)#.split(' ',1)[0].replace("\xa0", ""))
    names_schichtplan = []
    for name_sp_dirty in names_sp_dirty:
        names_schichtplan.append(name_sp_dirty.split(' /',1)[0].replace("\xa0", "").replace(".","").replace("  ", "").split(",")[0])
    not_registered = set(names_schichtplan) - set(names_registered)
    not_in_schichtplan = set(names_registered) - set(names_schichtplan)
    
    alias_mapping = _load_alias_mapper_registered_to_schichtplan()
    names_to_remove = set()
    for name in not_in_schichtplan:
        if name not in alias_mapping:
            continue
        name_list = alias_mapping[name]
        for name_alias in name_list:
            if name_alias in names_schichtplan:
                names_to_remove.add(name)
    not_in_schichtplan -= names_to_remove
    
    alias_mapping_one_to_one = _load_alias_mapper_registered_to_schichtplan_one_to_one()
    names_to_remove = set()
    for name in not_registered:
        if name not in alias_mapping_one_to_one:
            continue
        registered_name = alias_mapping_one_to_one[name]
        if registered_name in names_registered:
            names_to_remove.add(name)
    not_registered -= names_to_remove
            
    print("Nicht im Schichtplan aber registriert:", sorted(not_in_schichtplan))
    print("Nicht registriert aber im Schichtplan", sorted(not_registered))


def _load_alias_mapper_registered_to_schichtplan():
    with open("config/alias_mapper.json", "r") as f:
        alias_mapping = json.load(f)["registered_to_schichtplan"]
    return alias_mapping

def _load_alias_mapper_registered_to_schichtplan_one_to_one():
    """
    Loads the alias mapping and converts it from dict[str, list[str]] to dict[str, str],
    mapping each registered name to the first schichtplan alias in the list.
    """
    many_to_many = _load_alias_mapper_registered_to_schichtplan()
    one_to_one = {}
    for registered, aliases in many_to_many.items():
        for alias in aliases:
            one_to_one[alias] = registered
    return one_to_one


if __name__ == '__main__':
    main()