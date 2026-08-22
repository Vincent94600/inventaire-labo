import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Inventaire Physique-Chimie", page_icon="🧪", layout="wide"
)


@st.cache_data
def load_data(file_path):
    xls = pd.ExcelFile(file_path)
    all_data = []

    for sheet in xls.sheet_names:
        if sheet == "Produits chimiques":
            df = pd.read_excel(file_path, sheet_name=sheet, skiprows=5)
            # Nettoyage des sous-en-têtes superflus
            if df.shape[0] > 0 and pd.isna(df.iloc[0, 0]):
                df = df.iloc[1:].reset_index(drop=True)

            df_clean = pd.DataFrame(
                {
                    "Désignation": df.iloc[:, 0],
                    "Salle": "C105 (Chimie)",
                    "Quantité": df["Quantité en service"],
                    "Rangement / Armoire": df.iloc[:, 10],  # Localisation
                    "Discipline / Type": df["Famille chimique"].fillna(
                        "Chimie"
                    ),
                    "Commentaires / Détails": df["Etat physique"].fillna("")
                    + " "
                    + df["Caractéristique"].fillna(""),
                }
            )
        else:
            df = pd.read_excel(file_path, sheet_name=sheet, skiprows=1)
            df_clean = pd.DataFrame(
                {
                    "Désignation": df["Désignation du matériel"],
                    "Salle": sheet,
                    "Quantité": df["Quantité"],
                    "Rangement / Armoire": df["Lieu de rangement"],
                    "Discipline / Type": df["Discipline / Type de matériel"],
                    "Commentaires / Détails": df["Commentaires"],
                }
            )

        all_data.append(df_clean)

    full_df = pd.concat(all_data, ignore_index=True)
    full_df.dropna(subset=["Désignation"], inplace=True)
    return full_df


# Chargement du fichier
EXCEL_FILE = "Inventaire du laboratoire de physique-chimie.xlsx"

try:
    df = load_data(EXCEL_FILE)
except Exception as e:
    st.error(
        f"Erreur lors du chargement de **{EXCEL_FILE}**. Vérifiez le nom du fichier."
    )
    st.stop()

# --- INTERFACE PRINCIPALE ---
st.title("🧪 Inventaire Labo Physique-Chimie")
st.markdown("Recherche rapide et localisation du matériel et des produits.")

# Barre de recherche globale
search_term = st.text_input(
    "🔍 Recherche rapide (nom du produit, matériel, armoire...)", ""
)

# Filtres latéraux
st.sidebar.header("🎯 Filtres")
salles_dispo = ["Toutes"] + list(df["Salle"].unique())
salle_selected = st.sidebar.selectbox("Salle", salles_dispo)

types_dispo = ["Tous"] + [
    x for x in df["Discipline / Type"].dropna().unique() if str(x).strip() != ""
]
type_selected = st.sidebar.selectbox("Discipline / Famille", types_dispo)

# Filtrage des données
filtered_df = df.copy()

if search_term:
    mask = (
        filtered_df["Désignation"]
        .astype(str)
        .str.contains(search_term, case=False, na=False)
        | filtered_df["Rangement / Armoire"]
        .astype(str)
        .str.contains(search_term, case=False, na=False)
        | filtered_df["Commentaires / Détails"]
        .astype(str)
        .str.contains(search_term, case=False, na=False)
    )
    filtered_df = filtered_df[mask]

if salle_selected != "Toutes":
    filtered_df = filtered_df[filtered_df["Salle"] == salle_selected]

if type_selected != "Tous":
    filtered_df = filtered_df[
        filtered_df["Discipline / Type"] == type_selected
    ]

# Métriques
col1, col2 = st.columns(2)
col1.metric("Références trouvées", len(filtered_df))
col2.metric("Total articles répertoriés", len(df))

# Tableau des résultats
st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Désignation": st.column_config.TextColumn("Désignation", width="large"),
        "Salle": st.column_config.TextColumn("Salle", width="small"),
        "Quantité": st.column_config.TextColumn("Quantité", width="small"),
        "Rangement / Armoire": st.column_config.TextColumn(
            "Emplacement", width="medium"
        ),
    },
)

# Bouton d'export des résultats filtrés
csv = filtered_df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="📥 Télécharger la vue actuelle en CSV",
    data=csv,
    file_name="inventaire_filtre.csv",
    mime="text/csv",
)
