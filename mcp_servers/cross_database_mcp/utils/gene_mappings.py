# cross_database_mcp/utils/gene_mappings.py - Verified gene symbols
from typing import Dict, List

class GeneSymbolMapper:
    """Handles verified gene symbols and aliases"""
    
    def __init__(self):
        # VERIFIED gene symbol mappings (corrected based on Firecrawl verification)
        self.verified_aliases = {
            "TH": ["tyrosine hydroxylase", "tyrosine 3-monooxygenase"],
            "SLC6A3": ["DAT", "DAT1", "dopamine transporter"],
            "SLC18A2": ["VMAT2", "vesicular monoamine transporter 2"],
            "DDC": ["DOPA decarboxylase", "aromatic L-amino acid decarboxylase"],
            "PRKN": ["parkin", "PARK2 gene", "parkin RBR E3 ubiquitin protein ligase"],
            "SNCA": ["alpha-synuclein", "α-synuclein", "NACP", "PARK1", "PARK4"],
            "DRD1": ["dopamine receptor D1", "D1DR", "DRD1A"],
            "DRD2": ["dopamine receptor D2", "D2DR"],
            "DRD3": ["dopamine receptor D3", "D3DR"],
            "DRD4": ["dopamine receptor D4", "D4DR"],
            "DRD5": ["dopamine receptor D5", "D5DR", "DRD1B"],
            "LRRK2": ["leucine rich repeat kinase 2", "PARK8"],
            "PINK1": ["PTEN induced kinase 1", "PARK6"],
            "COMT": ["catechol-O-methyltransferase"],
            "MAOA": ["monoamine oxidase A", "MAO-A"],
            "MAOB": ["monoamine oxidase B", "MAO-B"]
        }
        
        self.alias_to_gene = {
            "DAT": "SLC6A3", "DAT1": "SLC6A3", "VMAT2": "SLC18A2",
            "PARK2": "PRKN", "PARKIN": "PRKN", "ALPHA-SYNUCLEIN": "SNCA",
            "MAO": "MAOA"
        }
    
    def get_aliases(self, identifier: str) -> List[str]:
        """Get verified aliases for a gene identifier"""
        identifier_upper = identifier.upper()
        
        if identifier_upper in self.verified_aliases:
            return [identifier] + self.verified_aliases[identifier_upper]
        elif identifier_upper in self.alias_to_gene:
            canonical_gene = self.alias_to_gene[identifier_upper]
            return [identifier, canonical_gene] + self.verified_aliases.get(canonical_gene, [])
        else:
            return [identifier]
    
    def get_canonical_symbol(self, identifier: str) -> str:
        """Get the canonical gene symbol for any identifier"""
        identifier_upper = identifier.upper()
        return self.alias_to_gene.get(identifier_upper, identifier_upper)

# Global instance
gene_mapper = GeneSymbolMapper()