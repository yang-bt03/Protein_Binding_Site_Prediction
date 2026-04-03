import os
import pandas as pd

class PDBparser:
    
    def __init__(self, pdbPath):
        self.__pdbPath = pdbPath

    def get_residues(self):
        with open(self.__pdbPath, 'r') as file:
            pdb_id = os.path.splitext(os.path.basename(self.__pdbPath))[0]
            aa_map = {
                'ALA': 'A', 'ARG': 'R', 'ASN': 'N', 'ASP': 'D',
                'CYS': 'C', 'GLN': 'Q', 'GLU': 'E', 'GLY': 'G',
                'HIS': 'H', 'ILE': 'I', 'LEU': 'L', 'LYS': 'K',
                'MET': 'M', 'PHE': 'F', 'PRO': 'P', 'SER': 'S',
                'THR': 'T', 'TRP': 'W', 'TYR': 'Y', 'VAL': 'V'}
            
            seen_residues = {}

            for line in file:
                line = line.strip()

                if line.startswith('ATOM'):
                    res_name = line[17:20]
                    chain = line[21]
                    res_num = int(line[22:26])

                    if chain not in seen_residues:
                        seen_residues[chain] = {}

                    if res_num not in seen_residues[chain]:
                        seen_residues[chain][res_num] = aa_map.get(res_name, 'err')
            
            sequences = {}
            res_nums = {}

            for chain, residues in seen_residues.items():
                sorted_nums = sorted(residues)
                sequences[chain] = "".join(residues[num] for num in sorted_nums)
                res_nums[chain] = sorted_nums  
            
            df = pd.DataFrame(list(sequences.items()), columns=['chain', 'sequence'])
            df.insert(0, 'pdb_id', pdb_id)
            df['res_nums'] = df['chain'].map(res_nums)  
            return df