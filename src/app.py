import os
import re

import pandas as pd
import streamlit as st


def get_grams(item, unit, quantity, masses, volumes, densities):
    if unit in masses:
        return quantity * masses[unit]
    return quantity * volumes[unit] * densities[item]


def parse(line):
    result = line.lower().strip().split(" - ")
    return (
        float(result[0].replace(" g", "")) if result[0] else None,
        result[1] if len(result) > 1 else None,
        result[2] if len(result) > 2 else None,
    )


def load_recipe(path):
    ingredients = []
    for line in open(path, "r"):
        mass, item, notes = parse(line)
        if mass:
            ingredients.append({"mass (g)": mass, "item": item, "notes": notes})
        else:
            break

    df = pd.DataFrame(ingredients)
    if "item" in df.columns:
        df = df.set_index("item")
    return df


def get_recipes(path):
    return sorted([v.replace(".md", "") for v in os.listdir(path) if v.endswith(".md")])


def main(datadir):
    st.title("Recipe App")
    recipes = get_recipes(datadir)
    recipes = st.multiselect("Recipe", recipes)
    for recipe in recipes:
        st.header(recipe)
        col1, col2 = st.columns([27, 10])
        df_in = load_recipe(os.path.join("data", f"{recipe}.md"))
        with col2:
            scale = st.number_input(
                "Scale", key=f"scale_{recipe}", value=1.0, format="%.2f", step=0.1
            )
        if "mass (g)" in df_in.columns:
            df_in["mass (g)"] = df_in["mass (g)"] * scale
        with col1:
            st.dataframe(
                df_in,
                use_container_width=True,
                column_config={
                    "item": st.column_config.TextColumn("item"),
                    "mass (g)": st.column_config.NumberColumn(
                        "mass (g)", width="small"
                    ),
                    "notes": st.column_config.TextColumn("notes", width="large"),
                },
            )

    # st.write("Hello World!")
    return "done"


if __name__ == "__main__":
    main("data")
