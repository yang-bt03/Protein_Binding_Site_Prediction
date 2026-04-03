from esm.models.esmc import ESMC
from esm.sdk.api import ESMProtein, LogitsConfig
import pandas as pd
import numpy as np
import torch

class ESM:

    def __init__(self, pdb_df):
        self.pdb_df = pdb_df

    def get_embeddings(self):
        client = ESMC.from_pretrained("esmc_300m")

        all_rows = []

        for _, row in self.pdb_df.iterrows():
            pdb_id = row['pdb_id']
            chain_id = row["chain"]
            res_nums = row['res_nums'] 
            residue_list = list(str(row['sequence']))

            protein = ESMProtein(sequence=str(row['sequence']))
            protein_tensor = client.encode(protein)
            with torch.no_grad():
                output = client.logits(
                    protein_tensor,
                    LogitsConfig(sequence=True, return_embeddings=True)
                )

            
            embeddings = output.embeddings.squeeze(0).cpu().numpy()[1:-1, :]

            if embeddings.shape[0] != len(residue_list):
                raise ValueError(
                    f"Mismatch for chain {chain_id}: "
                    f"{embeddings.shape[0]} embeddings vs {len(residue_list)} residues"
                )

            emb_cols = [f"emb_{i}" for i in range(embeddings.shape[1])]
            chain_df = pd.DataFrame(embeddings, columns=emb_cols)

            chain_df.insert(0, "residue", residue_list)
            chain_df.insert(0, "position", res_nums) 
            chain_df.insert(0, "chain_id", chain_id)
            chain_df.insert(0, "pdb_id", pdb_id)

            all_rows.append(chain_df)

        final_df = pd.concat(all_rows, ignore_index=True)
        return final_df