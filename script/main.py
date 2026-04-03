import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from class_files.ESM import ESM
from class_files.PDBparser import PDBparser
from class_files.Model_and_Pymol import predict_binding_site

def main():
    """
    Parses a PDB file, extracts its residues, computes ESM embeddings, and runs
    the binding site prediction model.

    Pipeline:
        1. PDBparser  : Parse the PDB file into a residue-level DataFrame.
        2. Deduplicate: Remove duplicate chains by sequence to avoid redundant
                        computation, since predictions for identical sequences
                        would be the same. To retain all chains, comment out:
                            # residues_df = residues_df.drop_duplicates(subset=['sequence'])
        3. ESM        : Generate a per-residue ESM embeddings DataFrame.
        4. Predict    : Run predict_binding_site() with the trained MLP model.

    Args:
        pdb_path (str): Path to a valid .pdb structure file, passed as a
                        command-line argument.

    Returns:
        predicted_sites: DataFrame containing the predicted binding site residues.

    Output:
        Saves a PyMOL script (<pdb_id>_binding.pml) that visualizes the predicted
        residues. Open it in PyMOL or in a text editor to inspect the results.

    Raises:
        SystemExit: On invalid arguments, missing file, wrong file extension,
                    or any runtime error during prediction.
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) < 2:
        print('You need to pass a PDB file')
        sys.exit(1)
        

    pdb_path = sys.argv[1]

    if not os.path.exists(pdb_path):
        print(f"Error: file not found -> {pdb_path}")
        sys.exit(1)
    
    if not pdb_path.endswith(".pdb"):
        print("Error: input file must be a .pdb file")
        sys.exit(1)
            
    model_path = os.path.join(BASE_DIR, '../model/model.pth')
    pdb_id = os.path.splitext(os.path.basename(pdb_path))[0]

    try:
        pdb_file = PDBparser(pdb_path)
        residues_df = pdb_file.get_residues()
        residues_df = residues_df.drop_duplicates(subset=['sequence'])

        embeddings = ESM(residues_df)
        embeddings_df = embeddings.get_embeddings()

        predicted_sites = predict_binding_site(
            df=embeddings_df,
            pdb_path=pdb_path,
            model_path=model_path,
            threshold=0.448,
            radius=8.0,
            min_neighbors=1,
            save_pymol_script=f'{pdb_id}_binding.pml'
        )
        
        return predicted_sites

    except Exception as e:
        print(f'Error during predition: {e}')

if __name__ == "__main__":
    main()
