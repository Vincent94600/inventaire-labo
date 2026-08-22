import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Inventaire Physique-Chimie", page_icon="🧪", layout="wide"
)

# Nom de votre fichier Excel (adaptez si besoin)
EXCEL_FILE = "Inventaire du laboratoire de physique-chimie.xlsx"


@st.cache_data
def load_data(file_path):
    xls = pd.ExcelFile(file_path)
    all_data = []

    for sheet in xls.sheet_names:
        if sheet == "Produits chimiques":
            df_sub = pd.read_excel(file_path, sheet_name=sheet, skiprows=5)
            if df_sub.empty or len(df_sub.columns) < 5:
                continue
            df_clean = pd.DataFrame(
                {
                    "Désignation": df_sub.iloc[:, 0],
                    "Salle": "C105 (Chimie)",
                    "Quantité": df_sub.iloc[:, 4],
                    "Rangement / Armoire": df_sub.iloc[:, 10]
                    if len(df_sub.columns) > 10
                    else "",
                    "Discipline / Type": df_sub.iloc[:, 3].fillna("Chimie"),
                    "Commentaires / Détails": df_sub.iloc[:, 1]
                    .fillna("")
                    .astype(str)
                    + " "
                    + df_sub.iloc[:, 2].fillna("").astype(str),
                }
            )
        else:
            df_sub = pd.read_excel(file_path, sheet_name=sheet, skiprows=1)
            if df_sub.empty or len(df_sub.columns) < 2:
                continue
            df_clean = pd.DataFrame(
                {
                    "Désignation": df_sub.iloc[:, 0],
                    "Salle": sheet,
                    "Quantité": df_sub.iloc[:, 1],
                    "Rangement / Armoire": df_sub.iloc[:, 2]
                    if len(df_sub.columns) > 2
                    else "",
                    "Discipline / Type": df_sub.iloc[:, 3]
                    if len(df_sub.columns) > 3
                    else "",
                    "Commentaires / Détails": df_sub.iloc[:, 4]
                    if len(df_sub.columns) > 4
                    else "",
                }
            )

        all_data.append(df_clean)

    full_df = pd.concat(all_data, ignore_index=True)
    full_df.dropna(subset=["Désignation"], inplace=True)
    # Nettoyage des sous-titres d'en-tête
    full_df = full_df[
        ~full_df["Désignation"]
        .astype(str)
        .str.startswith("Désignation du matériel")
    ]
    return full_df


# Chargement des données
try:
    df = load_data(EXCEL_FILE)
except Exception as e:
    st.error(f"❌ Erreur lors du chargement : `{e}`")
    st.info(
        "Vérifiez que le fichier Excel est bien au même endroit que `app.py` et que le nom correspond exactement."
    )
    st.stop()

# --- INTERFACE ---
st.title("🧪 Inventaire du Laboratoire de Physique-Chimie")

# Recherche globale
search_term = st.text_input("🔍 Rechercher un matériel, produit ou armoire...")

# Filtres dans la barre latérale
st.sidebar.header("🎯 Filtres")
salles = ["Toutes"] + list(df["Salle"].unique())
salle_filtre = st.sidebar.selectbox("Salle", salles)

if salle_filtre != "Toutes":
    df = df[df["Salle"] == salle_filtre]

if search_term:
    mask = (
        df["Désignation"]
        .astype(str)
        .str.contains(search_term, case=False, na=False)
        | df["Rangement / Armoire"]
        .astype(str)
        .str.contains(search_term, case=False, na=False)
        | df["Discipline / Type"]
        .astype(str)
        .str.contains(search_term, case=False, na=False)
    )
    df = df[mask]

# Affichage du nombre de résultats
st.write(f"**{len(df)}** élément(s) trouvé(s)")

# Affichage du tableau
st.dataframe(df, use_container_width=True, hide_index=True)
