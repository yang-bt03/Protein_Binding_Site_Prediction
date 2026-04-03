import torch
import torch.nn as nn
import pandas as pd
import os
import numpy as np
from Bio.PDB import PDBParser as BioPDBParser
from itertools import groupby
from esm.models.esmc import ESMC
from esm.sdk.api import ESMProtein, LogitsConfig

class MLP(nn.Module):
    def __init__(self, input_dim=960):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )

    def forward(self, x):
        return self.network(x).squeeze(1)

def df_to_embeddings_dict(df: pd.DataFrame) -> tuple:

    metadata_columns = {"pdb_id", "chain_id", "position", "residue"}
    feature_cols = [c for c in df.columns if c not in metadata_columns]
    embeddings_per_chain = {}
    positions_per_chain = {}

    for chain_id, group in df.groupby("chain_id", sort=False):
        embeddings_per_chain[chain_id] = group[feature_cols].values.astype(np.float32)
        positions_per_chain[chain_id] = group["position"].tolist()

    return embeddings_per_chain, positions_per_chain

def predict_binding_residues(
    embeddings_per_chain: dict,
    positions_per_chain: dict,
    model_path: str,
    threshold: float = 0.448,
    input_dim: int = 960,
) -> dict:

    model = MLP(input_dim=input_dim)
    model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu")))
    model.eval()

    preds_per_chain = {}
    with torch.no_grad():
        for chain_id, emb in embeddings_per_chain.items():
            x_tensor = torch.tensor(emb, dtype=torch.float32)
            logits = model(x_tensor)
            probs = torch.sigmoid(logits)
            binding_mask = (probs > threshold)
            positions = positions_per_chain[chain_id]
            preds_per_chain[chain_id] = [
                positions[i] for i, is_binding in enumerate(binding_mask) if is_binding
            ]

    return preds_per_chain

def get_ca_coordinates(pdb_path: str) -> dict:
    parser = BioPDBParser(QUIET=True)
    structure = parser.get_structure("protein", pdb_path)

    coords = {}
    for model in structure:
        for chain in model:
            for residue in chain:
                if "CA" in residue:
                    coords[(chain.id, residue.get_id()[1])] = (
                        residue["CA"].get_vector().get_array()
                    )
        break 

    return coords

def filter_by_proximity(
    preds_per_chain: dict,
    coords: dict,
    radius: float = 8.0,
    min_neighbors: int = 2,
) -> list:

    all_predicted = [
        (chain_id, res)
        for chain_id, positions in preds_per_chain.items()
        for res in positions
    ]

    filtered = []
    for key in all_predicted:
        if key not in coords:
            continue
        neighbors = sum(
            1
            for other in all_predicted
            if other != key
            and other in coords
            and np.linalg.norm(coords[key] - coords[other]) <= radius
        )
        if neighbors >= min_neighbors:
            filtered.append(key)

    removed = sorted(set(all_predicted) - set(filtered))
    
    return filtered

def generate_pymol_script(
    filtered: list,
    pdb_path: str = None,
    color: str = "red",
    representation: str = "sticks",
) -> str:

    lines = []

    if pdb_path:
        lines.append(f"load {pdb_path}, protein")

    chain_ids_present = sorted({c for c, _ in filtered})

    for chain_id, group in groupby(sorted(filtered), key=lambda x: x[0]):
        resi_str = "+".join(str(r) for _, r in group)
        lines.append(f"select binding_{chain_id}, chain {chain_id} and resi {resi_str}")
        lines.append(f"show {representation}, binding_{chain_id}")
        lines.append(f"show dots, binding_{chain_id}")
        lines.append(f"color {color}, binding_{chain_id}")

    all_selections = " or ".join(f"binding_{c}" for c in chain_ids_present)
    lines.append(f"select binding_site, {all_selections}")
    lines.append("zoom binding_site")

    return "\n".join(lines)

def predict_binding_site(
    df: pd.DataFrame,
    pdb_path: str,
    model_path: str = "model.pth",
    threshold: float = 0.448,
    radius: float = 8.0,
    min_neighbors: int = 2,
    pymol_color: str = "red",
    pymol_representation: str = "sticks",
    save_pymol_script: str = None,
) -> list:
    
    embeddings_per_chain, positions_per_chain = df_to_embeddings_dict(df)
    for chain_id, emb in embeddings_per_chain.items():
        print(f"  Chain {chain_id}: {emb.shape[0]} residues, {emb.shape[1]} dimensions")

    preds_per_chain = predict_binding_residues(
        embeddings_per_chain, positions_per_chain, model_path, threshold
    )
    for chain_id, positions in preds_per_chain.items():
        print(f"  Chain {chain_id}: {len(positions)} residues predicted as binding")


    coords = get_ca_coordinates(pdb_path)
    filtered = filter_by_proximity(preds_per_chain, coords, radius, min_neighbors)

    pymol_script = generate_pymol_script(
        filtered,
        pdb_path=pdb_path,
        color=pymol_color,
        representation=pymol_representation,
    )

    if save_pymol_script:
        with open(save_pymol_script, "w") as f:
            f.write(pymol_script)
        print(f"\nScript saved in: {save_pymol_script}")

    return filtered