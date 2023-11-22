import copy
import os
from math import floor, log10

import pandas as pd
import plotly.express as px
import streamlit as st


def round_to_3(x):
    return round(x, -int(floor(log10(abs(x))) - 2)) if x else x


def get_grams(item, unit, quantity, masses, volumes, densities):
    if unit in masses:
        return quantity * masses[unit]
    return quantity * volumes[unit] * densities[item]


def parse(line):
    result = line.lower().strip().split(" - ")
    return (
        float(result[0].replace(" g", "").strip()) if result[0] else None,
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
    df["ingredient_name"] = df["item"]
    if "item" in df.columns:
        df = df.set_index("item")
    return df


def get_nutrition(path):
    ingredients = sorted(
        [v.replace(".md", "") for v in os.listdir(path) if v.endswith(".md")]
    )
    result = {}
    for ingredient in ingredients:
        with open(os.path.join(path, f"{ingredient}.md"), "r") as f_:
            mass = float(f_.readline().strip().replace(" g", ""))
            calories = float(f_.readline().strip().replace(" cal", ""))
            d = {"mass": mass, "calories": calories}
            for item in f_:
                if not item.strip():
                    continue
                item_mass = float(item.split(" - ")[0].replace(" g", ""))
                item_name = item.split(" - ")[1].strip().lower()
                d[item_name] = item_mass
        result[ingredient.lower()] = d
    return result


def get_recipes(path):
    return sorted([v.replace(".md", "") for v in os.listdir(path) if v.endswith(".md")])


def get_nutrient_df(nutrient, ingredients, nutrition, nutrition_facts):
    nutrition_fractions = {"nutrient": [], "item": []}
    for ingredient in ingredients:
        ingredient_name = ingredient["ingredient_name"]

        if ingredient_name in nutrition:
            scale = ingredient["mass (g)"] / nutrition[ingredient_name]["mass"]
            for item in nutrition[ingredient_name]:
                if item == "mass":
                    continue
                nutrition_facts[item] = (
                    nutrition_facts.get(item, 0)
                    + scale * nutrition[ingredient_name][item]
                )
                if item == nutrient and nutrition[ingredient_name][item]:
                    nutrition_fractions["nutrient"].append(
                        scale * nutrition[ingredient_name][item]
                    )
                    nutrition_fractions["item"].append(ingredient_name)

    return pd.DataFrame.from_dict(nutrition_fractions)


def main(datadir):
    st.title("Recipe App")

    params = st.experimental_get_query_params()
    recipes = get_recipes(datadir)
    default_recipes = [v for v in params.get("recipes", []) if v in recipes]
    nutrition = get_nutrition(os.path.join(datadir, "Nutrition"))

    recipes = st.multiselect(
        label="Recipe",
        options=recipes,
        default=default_recipes
        if "recipes" not in st.session_state
        else st.session_state["recipes"],
        key="recipes",
    )

    st.experimental_set_query_params(recipes=recipes)
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
        st.write(f"Total mass: {df_in['mass (g)'].sum()}")
        st.subheader(f"Nutrition {recipe}")
        ingredients = df_in.to_dict(orient="records")
        nutrition_facts = {}
        nutrients = set()

        for ingredient in ingredients:
            nutrition_facts["mass"] = (
                nutrition_facts.get("mass", 0) + ingredient["mass (g)"]
            )
            ingredient_name = ingredient["ingredient_name"]

            if ingredient_name in nutrition:
                scale = ingredient["mass (g)"] / nutrition[ingredient_name]["mass"]
                for item in nutrition[ingredient_name]:
                    if item == "mass":
                        continue
                    nutrition_facts[item] = (
                        nutrition_facts.get(item, 0)
                        + scale * nutrition[ingredient_name][item]
                    )
                    if nutrition[ingredient_name][item]:
                        nutrients.add(item)

        col3, col4 = st.columns([10, 27])
        with col4:
            portion = st.number_input(
                "portion (g)",
                key=f"portion_{recipe}",
                value=100,
                step=10,
            )
            nutrition_facts_copy = copy.deepcopy(nutrition_facts)
            nutrition_facts_mass = nutrition_facts_copy["mass"]
            for key in nutrition_facts_copy:
                nutrition_facts_copy[key] = round_to_3(
                    nutrition_facts_copy[key] * portion / nutrition_facts_mass
                )

            nutrients_list = sorted(nutrients)
            nutrients_index = (
                nutrients_list.index("calories") if "calories" in nutrients_list else 0
            )
            nutrient = st.selectbox("nutrient", nutrients_list, index=nutrients_index)
            nutrient_df = get_nutrient_df(
                nutrient=nutrient,
                ingredients=ingredients,
                nutrition=nutrition,
                nutrition_facts=nutrition_facts,
            )
            fig = px.pie(
                nutrient_df,
                values="nutrient",
                names="item",
                title=f"fractions of {nutrient}",
            )
            st.plotly_chart(fig, use_container_width=True)
        with col3:
            st.dataframe(nutrition_facts_copy)

    # st.write("Hello World!")
    return "done"


if __name__ == "__main__":
    main("data")
