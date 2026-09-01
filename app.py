import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Inventaire Physique-Chimie", page_icon="🧪", layout="wide"
)

EXCEL_FILE = "Inventaire du laboratoire de physique-chimie.xlsx"


@st.cache_data(ttl=60)  # Le cache se rafraîchit automatiquement toutes les 60 secondes
def load_data(file_path):
    xls = pd.ExcelFile(file_path)
    all_data = []

    for sheet in xls.sheet_names:
        df_raw = pd.read_excel(file_path, sheet_name=sheet)
        if df_raw.empty:
            continue

        if sheet == "Produits chimiques":
            df_sub = pd.read_excel(file_path, sheet_name=sheet, skiprows=5)
            if len(df_sub.columns) >= 5:
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
                all_data.append(df_clean)
        else:
            # Détection dynamique de la ligne d'en-tête "Désignation"
            header_idx = None
            for idx, row in df_raw.iterrows():
                row_str = row.astype(str).str.lower().to_string()
                if "désignation" in row_str or "materiel" in row_str:
                    header_idx = idx
                    break

            if header_idx is not None:
                df_sub = pd.read_excel(
                    file_path, sheet_name=sheet, skiprows=header_idx + 1
                )
            else:
                df_sub = df_raw

            if df_sub.empty or len(df_sub.columns) < 1:
                continue

            df_clean = pd.DataFrame(
                {
                    "Désignation": df_sub.iloc[:, 0],
                    "Salle": sheet,
                    "Quantité": df_sub.iloc[:, 1]
                    if len(df_sub.columns) > 1
                    else "",
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

    if not all_data:
        return pd.DataFrame()

    full_df = pd.concat(all_data, ignore_index=True)
    full_df.dropna(subset=["Désignation"], inplace=True)

    # Nettoyage des lignes de titre résiduelles
    full_df = full_df[
        ~full_df["Désignation"]
        .astype(str)
        .str.strip()
        .str.lower()
        .str.startswith("désignation")
    ]
    full_df = full_df[full_df["Désignation"].astype(str).str.strip() != ""]
    return full_df


# Chargement des données
try:
    df = load_data(EXCEL_FILE)
except Exception as e:
    st.error(f"❌ Erreur lors du chargement : `{e}`")
    st.stop()

# --- INTERFACE ---
st.title("🧪 Inventaire du Laboratoire de Physique-Chimie")

# Bouton de rafraîchissement manuel
if st.button("🔄 Actualiser les données"):
    st.cache_data.clear()
    st.rerun()

# Recherche globale
search_term = st.text_input("🔍 Rechercher un matériel, produit ou armoire...")

# Filtres
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

st.write(f"**{len(df)}** élément(s) trouvé(s)")
st.dataframe(df, use_container_width=True, hide_index=True)
