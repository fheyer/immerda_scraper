import requests
from bs4 import BeautifulSoup
import pandas as pd
import sys
import numpy as np
import datetime
import json

pd.options.mode.copy_on_write = True


def overview(show_diff=True) -> pd.DataFrame:
    urls = sys.argv[1:]
    all_names = []
    all_labels = []
    for url in urls:
        names, labels = _crawl_url(url)
        all_names.extend(names)
        all_labels.extend(labels)
    return _to_df(all_names, all_labels, show_diff)
    

def _crawl_url(url) -> tuple[list, list]:
    rows = _get_content_rows(url)
    labels = []
    names = []
    for row in rows[2:]:
        if _skip(row):
            continue
        labels.append(_label(row))
        names_in_row = row.find_all("i")
        for name in names_in_row:
            if name.text == '\n':
                names.append([np.nan])
                continue
            tmp_names = []
            for nam in name.string.strip().replace(".","").replace("  ", "").split(","):
                # TODO: store replace options somewhere in a config
                tmp_names.append(nam.upper().replace("FLEXI","").strip())
            names.append(tmp_names)
    return names, labels

def _get_content_rows(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    return soup.find_all("tr")

def _skip(row):
    if "bg-green" in row.text:
        return True
    if "\n\nTitle\nDescription\nBeginning\n\n" in row.text:
        return True
    if "\n0" in row.text:
        return True
    return False

def _label(row):
    # TODO: make flexibel for different labels (maybe in config)
    if "TRY HARD" in row.text:
        return "TRY_HARD"
    elif "FLEXI" in row.text:
        return "FLEXI"
    else:
        return "NORMAL"

def _to_df(names_list, labels, show_diff=True):
    data = [(label, name) for label, sublist in zip(labels, names_list) for name in sublist]
    df = pd.DataFrame(data, columns=["label", "alias"])
    df= pd.crosstab(index=df["alias"], columns=df["label"])
    df = _merge_alias(df, labels)
    if show_diff and {"TRY_HARD", "FLEXI", "NORMAL"}.issubset(df.columns):
        df[f"dTRY_HARD"] = 1 - df["TRY_HARD"]
        df[f"dFLEXI"] = 1 - df["FLEXI"]
        df[f"dNORMAL"] = 2 - df["NORMAL"]
    return df

def _merge_alias(df, labels):
    df = df.reset_index()
    alias_mapping = _load_alias_mapper_registered_to_schichtplan_one_to_one()

    df['name'] = df['alias'].map(alias_mapping).fillna(df['alias'])

    aggregations = {'alias': ' / '.join}
    for label in df.columns:
        aggregations[label] = "sum"

    return df.groupby('name').agg(aggregations).reset_index(drop=False)

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
    df = overview(show_diff=True)
    df.to_csv("data/schichtplan_overview.csv", index=False)
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    with pd.ExcelWriter(f"data/{now}_schichtplan_overview.xlsx", engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
        worksheet = writer.sheets['Sheet1']
        for idx, col in enumerate(df.columns):
            # Set default column width (e.g., 20)
            worksheet.set_column(idx, idx, 20)
