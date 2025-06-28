import pandas as pd
import numpy as np
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.api import GLM
from statsmodels.genmod.families import Binomial
import warnings
warnings.filterwarnings('ignore')

# Read the Excel file - all data is in the 'All-omics' sheet
# Data structure: 
# - Row 1: Category headers (Cohort information, Cytokines, Proteins, Metabolites)
# - Row 2: Column headers/variable names
# - Row 3+: Data
data_all = pd.read_excel('Data.xlsx', sheet_name='All-omics', header=[0, 1])

# The file has a multi-level header structure, let's handle it properly
# First, let's read it with a single header and then parse the structure
data_raw = pd.read_excel('Data.xlsx', sheet_name='All-omics')

# Based on our analysis:
# Cohort information: columns 1-4 (index 0-3)
# Cytokines: columns 5-51 (index 4-50) 
# Proteins: columns 52-325 (index 51-324)
# Metabolites: columns 326-960 (index 325-959)

# Extract each section
cohort_info = data_raw.iloc[:, 0:4]  # Cohort information (columns 0-3)
cytokines = data_raw.iloc[:, 4:51]   # Cytokines (columns 4-50)
proteins = data_raw.iloc[:, 51:325]  # Proteins (columns 51-324) 
metabolites = data_raw.iloc[:, 325:] # Metabolites (columns 325 to end)

# Set proper column names (row 1 contains the actual variable names)
cohort_info.columns = data_raw.iloc[0, 0:4].values
cytokines.columns = data_raw.iloc[0, 4:51].values
proteins.columns = data_raw.iloc[0, 51:325].values
metabolites.columns = data_raw.iloc[0, 325:].values

# Remove the header row from the data
cohort_info = cohort_info.iloc[1:].reset_index(drop=True)
cytokines = cytokines.iloc[1:].reset_index(drop=True)
proteins = proteins.iloc[1:].reset_index(drop=True)
metabolites = metabolites.iloc[1:].reset_index(drop=True)

# Now combine the data as in the original approach
n_protein = 0  # Since we're extracting proteins directly, start from beginning
n_metabolite = 0  # Since we're extracting metabolites directly, start from beginning

# Combine cohort info with molecular data
Data = pd.concat([cohort_info, cytokines, proteins, metabolites], axis=1)

# Make ALL column names unique using pandas functionality  
original_cols = Data.columns.tolist()
Data.columns = pd.io.common.dedup_names(original_cols, is_potential_multiindex=False)

print(f"Made {len(original_cols) - len(Data.columns.unique())} column names unique")

desc_cols = list(range(4))
n_first_mol = 4
Data = pd.concat([Data.iloc[:, desc_cols], 
                  Data.iloc[:, n_first_mol:].apply(pd.to_numeric, errors='coerce')], axis=1)

print(np.sum(Data == 0))
Data = Data.replace(0, np.nan)
print(np.sum(Data == 0))

# Define missing value cutoff
missing_value_cut_off = 0.5

# Improved missing value handling
# Work only with molecular data (excluding descriptive columns)
molecular_data = Data.iloc[:, n_first_mol:].copy()

# Calculate missing value percentage for each column
missing_pct = molecular_data.isna().sum() / len(molecular_data)
print(f"Columns with >50% missing: {(missing_pct > 0.5).sum()}")

# Filter columns with less than 50% missing values
filtered_cols = missing_pct < missing_value_cut_off
molecular_data_filtered = molecular_data.loc[:, filtered_cols].copy()

print(f"Molecular data after filtering: {molecular_data_filtered.shape}")
print(f"Missing values before imputation: {molecular_data_filtered.isna().sum().sum()}")

# Impute missing values with column minimum
molecular_data_filtered = molecular_data_filtered.copy()  # Ensure we have a proper copy
# Use vectorized fillna approach instead of loop
molecular_data_filtered = molecular_data_filtered.apply(
    lambda x: x.fillna(x.min() if not pd.isna(x.min()) else 0.001)
)

print(f"Missing values after imputation: {molecular_data_filtered.isna().sum().sum()}")

# Combine descriptive columns with filtered molecular data
cleaned_data = pd.concat([Data.iloc[:, :n_first_mol], molecular_data_filtered], axis=1)

print(f"Final cleaned data shape: {cleaned_data.shape}")
print(f"Zero values in molecular data: {(molecular_data_filtered == 0).sum().sum()}")

# Use the cleaned data for further processing
data_numeric = cleaned_data.iloc[:, n_first_mol:].apply(pd.to_numeric, errors='coerce')
data_log = np.log(data_numeric + 1)
scaler = StandardScaler()
data_normalized = pd.DataFrame(scaler.fit_transform(data_log), 
                               index=data_log.index, 
                               columns=data_log.columns)

pca = PCA()
pca_result = pca.fit_transform(data_normalized)
pca_df = pd.DataFrame(pca_result, index=data_normalized.index)

plt.figure(figsize=(10, 8))
plt.scatter(pca_df.iloc[:, 0], pca_df.iloc[:, 1])
plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%})')
plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%})')
plt.title('PCA Score Plot')
plt.savefig('pca_score2d_0_.png', dpi=300)
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(range(1, min(21, len(pca.explained_variance_ratio_)+1)), 
         pca.explained_variance_ratio_[:20], 'bo-')
plt.xlabel('Principal Component')
plt.ylabel('Explained Variance Ratio')
plt.title('PCA Scree Plot')
plt.savefig('pca_scree_0_.png', dpi=72)
plt.show()

Fold_change_cut_off = 1.5
P_Value_cut_off = 0.05

group1 = data_normalized.iloc[:len(data_normalized)//2]
group2 = data_normalized.iloc[len(data_normalized)//2:]

fold_changes = []
p_values = []

for col in data_normalized.columns:
    mean1 = group1[col].mean()
    mean2 = group2[col].mean() 
    fc = mean2 - mean1
    _, p_val = stats.ttest_ind(group1[col], group2[col])
    
    # Ensure scalar values
    fold_changes.append(float(fc))
    p_values.append(float(p_val))

# Create volcano plot dataframe with robust handling
volcano_df = pd.DataFrame({
    'fold_change': fold_changes,
    'p_value': p_values
})

# Calculate neg_log_p safely using numpy maximum for element-wise operation
volcano_df['neg_log_p'] = -np.log10(np.maximum(volcano_df['p_value'], 1e-300))

# Clean the volcano plot data to remove any infinite or NaN values
volcano_df = volcano_df.replace([np.inf, -np.inf], np.nan).dropna()

print(f"Volcano plot data shape after cleaning: {volcano_df.shape}")
print(f"Fold change range: {volcano_df['fold_change'].min():.3f} to {volcano_df['fold_change'].max():.3f}")
print(f"Neg log p range: {volcano_df['neg_log_p'].min():.3f} to {volcano_df['neg_log_p'].max():.3f}")

plt.figure(figsize=(10, 8))
plt.scatter(volcano_df['fold_change'], volcano_df['neg_log_p'], alpha=0.6)
plt.axhline(y=-np.log10(P_Value_cut_off), color='r', linestyle='--')
plt.axvline(x=np.log2(Fold_change_cut_off), color='r', linestyle='--')
plt.axvline(x=-np.log2(Fold_change_cut_off), color='r', linestyle='--')
plt.xlabel('Log2 Fold Change')
plt.ylabel('-Log10 P-value')
plt.title('Volcano Plot')
plt.savefig('volcano_0_.png', dpi=300)
plt.show()

top_mol = 100
top_features = data_normalized.iloc[:, :top_mol]

plt.figure(figsize=(12, 8))
sns.clustermap(top_features.T, method='ward', metric='euclidean', 
               cmap='RdBu_r', center=0, figsize=(12, 8))
plt.savefig('heatmap_1_.png', dpi=300)
plt.show()

clinical_variables = pd.read_csv("Data.csv")

n_o_clinical_variables = 20
n_of_differentially_changed_molecules = 219
A = n_o_clinical_variables + n_of_differentially_changed_molecules
ncol_adjustment_var = 240
n__adjustment_var = 7
B = list(range(ncol_adjustment_var, ncol_adjustment_var + n__adjustment_var + 1))

Coefficients = pd.DataFrame(index=clinical_variables.columns[n_of_differentially_changed_molecules:A],
                           columns=clinical_variables.columns[:n_of_differentially_changed_molecules])

pvalue = pd.DataFrame(index=Coefficients.index, columns=Coefficients.columns)

for i in range(n_of_differentially_changed_molecules):
    for j in range(n_of_differentially_changed_molecules, A):
        try:
            y = clinical_variables.iloc[:, j]
            X = pd.concat([clinical_variables.iloc[:, i]] + 
                         [clinical_variables.iloc[:, b] for b in B], axis=1)
            
            model = GLM(y, X, family=Binomial())
            result = model.fit()
            
            pvalue.iloc[j-n_of_differentially_changed_molecules, i] = result.pvalues.iloc[0]
            Coefficients.iloc[j-n_of_differentially_changed_molecules, i] = np.exp(result.params.iloc[0])
        except:
            continue

n_pval = pvalue.T
v = []
for i in range(len(n_pval)):
    v.append(np.sum(n_pval.iloc[i] < 0.05))

n_pval['n_of_sig'] = v

P_Value_cut_off = 3
n_pval_filtered = n_pval[n_pval['n_of_sig'] >= P_Value_cut_off]
n_pval_filtered = n_pval_filtered.drop('n_of_sig', axis=1)

odds_filtered = Coefficients[n_pval_filtered.index].T

plt.figure(figsize=(12, 8))
mask = n_pval_filtered < 0.05
sns.heatmap(odds_filtered, annot=mask, fmt='', cmap='RdBu_r', center=1,
            cbar_kws={'label': 'Odds Ratio'})
plt.title('Odds Ratio Heatmap')
plt.tight_layout()
plt.show()
