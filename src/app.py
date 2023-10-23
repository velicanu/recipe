import os
import re

import pandas as pd
import streamlit as st


def get_grams(item, unit, quantity, masses, volumes, densities):
    if unit in masses:
        return quantity * masses[unit]
    return quantity * volumes[unit] * densities[item]


def parse(line):
    result = re.search(r"([\d]*) g - ([\w]*)", line)
    if not result:
        return None, None
    return result.group(1), result.group(2)


def load_recipe(path):
    ingredients = []
    ingredients_flag = True
    for line in open(path, "r"):
        mass, item = parse(line)
        if mass and item and ingredients_flag:
            ingredients.append({"mass (g)": mass, "item": item})
        if not mass:
            ingredients_flag = False

    df = pd.DataFrame(ingredients)
    if "item" in df.columns:
        df = df.set_index("item")
    return df


def get_recipes(path):
    return sorted([v.replace(".md", "") for v in os.listdir(path) if v.endswith(".md")])


def main():
    st.title("Recipe App")
    recipes = get_recipes("data")
    recipes = st.multiselect("Recipe", recipes)
    for recipe in recipes:
        st.header(recipe)
        col1, col2 = st.columns(2)
        df_in = load_recipe(os.path.join("data", f"{recipe}.md"))
        with col2:
            scale = st.number_input(
                "Scale", key=f"scale_{recipe}", value=1.0, format="%.2f"
            )
        if "mass (g)" in df_in.columns:
            df_in["mass (g)"] = df_in["mass (g)"].astype(float) * scale
        with col1:
            st.write(df_in)

    # st.write("Hello World!")
    return "done"


if __name__ == "__main__":
    main()
