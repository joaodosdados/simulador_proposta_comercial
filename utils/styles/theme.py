import streamlit as st
from pathlib import Path


def apply_theme(theme_name="carbon"):
    """Aplica o tema especificado à página"""
    themes = {
        "carbon": {
            "css": Path(__file__).parent.parent.parent
            / "static"
            / "css"
            / "carbon_theme.css",
            "fonts": "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap",
        }
        # Pode adicionar outros temas depois
    }

    theme = themes.get(theme_name, themes["carbon"])

    # Carrega fontes
    st.markdown(
        f"""
    <link href="{theme['fonts']}" rel="stylesheet">
    """,
        unsafe_allow_html=True,
    )

    # Carrega CSS
    with open(theme["css"], "r") as f:
        css = f.read()
        st.markdown(
            f"""
        <style>
        {css}
        </style>
        """,
            unsafe_allow_html=True,
        )
