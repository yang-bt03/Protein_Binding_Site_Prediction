# Predicting_Binding_Sites

This project leverages ESM2, a state-of-the-art protein language model developed by Meta AI, to generate residue-level embeddings from raw protein sequences obtained from the database Biolip. These embeddings are then used as input features for machine/deep learning models trained to predict binding sites,residues that interact with ligands or other proteins. The goal is to accurately identify functional regions of proteins using sequence information and 3D structure.

---

### Pipeline

`BioLip DB ---> Data Cleaning ---> ESM-2 Embeddings (960-dim) ---> Deep Learning Model ---> Binding Site Predictions`

---

### `Biolip: The Dataset ` 

Biolip is a protein database and its ligand/protein interaction, semi-manually curated. It contains more than 989,000 sequences that have been extracted from the Protein Data Bank (PDB) and completed with literature reviews.
This database is really useful for our project because

1) It allows obtaining the protein sequence in text as required by our pLM.
2) It allows comparing our obtained results with the real binding site.
3) It contains enough proteins to train machine or deep learning models.

To learn more about the dataset, see data/README.md

---

### `ESM-2: Transforming Aminoacids In Embeddings`

In recent years, the emergence of NLPs (Natural Language Processing) has been a major technological advance. This success has led to attempts to apply these models to language-like structures, and of course, the biology world is exploring the use of NLP in proteins: these specific models are called pLM (Protein Language Models) [1].
One of the first algorithms to appear was BERT and, similarly, ESM-2 was born derived from it [1]. This is a pLM developed by Meta AI in 2022, trained with more than 250 million protein sequences. The interesting thing about this model is that it allows capturing the biological semantics of proteins and, therefore, we believe that by using it, ESM-2 will give similar embeddings to amino acids that are binding sites [2,3]. 
Thus, ESM-2 has been the algorithm we have used to obtain 960 embeddings of each residue of each of the proteins in the Biolip (cleaned) dataset in order to predict a binding site with some confidence.

---

### `Use of Machine Learning and Deep Learning: Reviewing the Literature`

Our project focused on using Machine Learning and Deep Learning algorithms to accurately predict binding sites. This approach was chosen because several tools previously described in the literature, based on ML and DL, had shown promising results [3,4].

---

### `Creating Our Model: model.pth`

First, we applied the filter pipeline described in the ./data folder to obtain a high-quality subset of the dataset. This subset revealed a highly imbalanced class distribution, with a 1:25 ratio of binding to non-binding residues. After exploring several classical Machine Learning approaches, including LightGBM with various balancing strategies, we found that results were inconsistent with low and unreliable precision and recall.

This led us to adopt a deep learning approach, which gived better results across all metrics. Specifically, we use an MLP (Multilayer Perceptron), which is well-suited for high-dimensional inputs like our ESM embeddings. These embeddings encode rich evolutionary and structural information per residue, and the MLP is able to learn the non-linear patterns that separate binding from non-binding residues in that complex space.

To address the class imbalance during training, we use Focal Loss, which automatically down-weights easy examples and forces the model to focus on the hard and ambiguous residues near binding sites.

To ensure reliable and generalizable evaluation, train/test splits are performed at the protein level, grouping all residues from the same PDB structure together. This prevents data leakage, where residues from the same protein could appear in both train and test sets, and ensures the model is evaluated on truly unseen proteins rather than just unseen residues.

Finally, MCC (Matthews Correlation Coefficient)-based threshold tuning is applied to select the optimal decision boundary. Unlike accuracy, MCC accounts for all four classification outcomes and gives a fair and reliable measure of performance under severe class imbalance.

The metrics we've gotten after optimizing the threshold and evaluate the model with the test set was:
| Metric             | Value  |
|--------------------|--------|
| Threshold          | 0.448  |
| MCC                | 0.6232 |
| Balanced Accuracy  | 0.8081 |
| ROC AUC            | 0.9586 |
| F1 (Weighted)      | 0.9720 |
| Precision          | 0.6453 |
| Recall             | 0.6301 |
| Specificity        | 0.9860 |

The high ROC AUC indicates strong discriminative ability between binding and non-binding residues. The model achieves excellent specificity, meaning it rarely misclassifies non-binding residues as binding. The MCC of 0.6232 provides the most honest overall summary, as it accounts for all four classification outcomes and is robust to the imbalance dataset.

<img width="673" height="468" alt="image" src="https://github.com/user-attachments/assets/16297f43-d0ca-4971-9e6d-028ae2049939" />

---

### `Looking For Small Improvements`

Since we wanted to get the most out of our model and were aware of its limitations, we decided that after obtaining the predicted amino acids, they would go through a more restrictive filter to remove false positives. This approach works as a "patch" to successfully work around potential model failures, even though we consider it to perform well overall (as shown in the previous section). We added an extra filtering step to our pipeline based on distance and neighborhood relationships between amino acids, increasing the likelihood of finding the actual binding site and allowing us to discard amino acids that were predicted as positive but were not near any other predicted binding site residue.

---

### `Final Remarks`

To see exactly what we used to build our model, we recommend visiting data/README.md and the two jupyter notebooks in data/ and model/. It should be noted that we filtered the BioLiP dataset to obtain a high-quality 
subset, which also helped reduce resource consumption. Working with high-dimensional dataframes is computationally demanding, and given our hardware limitations, managing memory and processing power was a significant constraint throughout the project.

---

> [1] Ofer, D., Brandes, N., & Linial, M. (2021). The language of proteins: NLP, machine learning & protein sequences.
> Computational and structural biotechnology journal, 19, 1750–1758. https://doi.org/10.1016/j.csbj.2021.03.022

> [2] ESM-2 - BioNEMO Framework. (s. f.). https://docs.nvidia.com/bionemo-framework/2.0/models/esm2/

> [3] Wu, S., Xu, J., & Guo, J. (2024). Accurate prediction of nucleic acid binding proteins using protein language model.
> Bioinformatics Advances, 5(1), vbaf008. https://doi.org/10.1093/bioadv/vbaf008

> [4] Vural, O., & Jololian, L. (2025). Machine learning approaches for predicting protein-ligand binding sites from 
> sequence data. Frontiers In Bioinformatics, 5, 1520382. https://doi.org/10.3389/fbinf.2025.1520382

---
---

### General Tutorial (With and Without Package Install)

#### Running the Script Without Installing the Package

1. Clone the repo and create a conda environment.
```bash
    git clone "repo link"
    conda create -n env_name
```
2. Activate the environment and install dependencies.
```bash
    conda activate env_name
    pip install -r requirements.txt
```
3. Run the script with the command:
```bash
    python main.py pdb_filepath
```

#### With the Package Installed
```bash
pbs pdb_filepath
```
---

#### Function Documentation
```python
help(main)
```

**Arguments:**

| Argument | Type | Description |
|---|---|---|
| `pdb_filepath` | `str` | Path to the input `.pdb` file (e.g., `data/1HSG.pdb`) |

**Output:**

A PyMOL script named `<PDB_id>_binding.pml` saved to the current directory.

**Example:**
```bash
python ./script/main.py ./test/test1/1HSG.pdb
```
```bash
pbs ./test/test1/1HSG.pdb
```

The script outputs a `.pml` file that can be opened in a text editor to inspect predicted binding site residues, or loaded directly into PyMOL for visual confirmation.
   
### How to install the package
1. From the root of the repository (where `pyproject.toml` is located), install the package:
```bash
    pip install -e .
```

2. Verify the installation:
```bash
    pip show predicting-binding-sites
```
#### In the test folder, you can see:

> Pymol File for 1HSG
```python
load 1HSG.pdb, protein
select binding_A, chain A and resi 25+27+28+29+84
show sticks, binding_A
show dots, binding_A
color red, binding_A
select binding_site, binding_A
zoom binding_site
```
> which can be used for visualization in pymol

---
---
