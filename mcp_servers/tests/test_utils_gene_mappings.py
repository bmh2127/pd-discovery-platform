# tests/test_utils_gene_mappings.py
import pytest
from mcp_servers.cross_database_mcp.utils.gene_mappings import GeneSymbolMapper

class TestGeneSymbolMapper:
    """Test suite for GeneSymbolMapper"""

    def setup_method(self):
        """Setup fresh gene mapper for each test"""
        self.gene_mapper = GeneSymbolMapper()

    def test_mapper_initialization(self):
        """Test gene mapper initializes with correct data structures"""
        assert hasattr(self.gene_mapper, 'verified_aliases')
        assert hasattr(self.gene_mapper, 'alias_to_gene')
        assert isinstance(self.gene_mapper.verified_aliases, dict)
        assert isinstance(self.gene_mapper.alias_to_gene, dict)

    def test_verified_dopaminergic_gene_aliases(self):
        """Test aliases for verified dopaminergic genes"""
        # Test TH (tyrosine hydroxylase)
        th_aliases = self.gene_mapper.get_aliases("TH")
        assert "TH" in th_aliases
        assert "tyrosine hydroxylase" in th_aliases
        assert "tyrosine 3-monooxygenase" in th_aliases

        # Test SLC6A3 (dopamine transporter)
        slc6a3_aliases = self.gene_mapper.get_aliases("SLC6A3")
        assert "SLC6A3" in slc6a3_aliases
        assert "DAT" in slc6a3_aliases
        assert "DAT1" in slc6a3_aliases
        assert "dopamine transporter" in slc6a3_aliases

        # Test DRD2 (dopamine receptor D2)
        drd2_aliases = self.gene_mapper.get_aliases("DRD2")
        assert "DRD2" in drd2_aliases
        assert "dopamine receptor D2" in drd2_aliases
        assert "D2DR" in drd2_aliases

    def test_parkinson_disease_gene_aliases(self):
        """Test aliases for Parkinson's disease genes"""
        # Test SNCA (alpha-synuclein) - PARK1/PARK4
        snca_aliases = self.gene_mapper.get_aliases("SNCA")
        assert "SNCA" in snca_aliases
        assert "alpha-synuclein" in snca_aliases
        assert "α-synuclein" in snca_aliases
        assert "NACP" in snca_aliases
        assert "PARK1" in snca_aliases
        assert "PARK4" in snca_aliases

        # Test PRKN (parkin) - corrected from PARK2
        prkn_aliases = self.gene_mapper.get_aliases("PRKN")
        assert "PRKN" in prkn_aliases
        assert "parkin" in prkn_aliases
        assert "PARK2 gene" in prkn_aliases
        assert "parkin RBR E3 ubiquitin protein ligase" in prkn_aliases

        # Test LRRK2 - PARK8
        lrrk2_aliases = self.gene_mapper.get_aliases("LRRK2")
        assert "LRRK2" in lrrk2_aliases
        assert "leucine rich repeat kinase 2" in lrrk2_aliases
        assert "PARK8" in lrrk2_aliases

    def test_alias_to_canonical_mapping(self):
        """Test mapping from aliases to canonical gene symbols"""
        # Test dopamine transporter aliases
        assert self.gene_mapper.get_canonical_symbol("DAT") == "SLC6A3"
        assert self.gene_mapper.get_canonical_symbol("DAT1") == "SLC6A3"
        assert self.gene_mapper.get_canonical_symbol("dat") == "SLC6A3"  # case insensitive

        # Test VMAT2 alias
        assert self.gene_mapper.get_canonical_symbol("VMAT2") == "SLC18A2"
        assert self.gene_mapper.get_canonical_symbol("vmat2") == "SLC18A2"

        # Test PARK2/PARKIN -> PRKN mapping (corrected)
        assert self.gene_mapper.get_canonical_symbol("PARK2") == "PRKN"
        assert self.gene_mapper.get_canonical_symbol("PARKIN") == "PRKN"
        assert self.gene_mapper.get_canonical_symbol("parkin") == "PRKN"

        # Test alpha-synuclein alias
        assert self.gene_mapper.get_canonical_symbol("ALPHA-SYNUCLEIN") == "SNCA"

    def test_dopamine_receptor_family(self):
        """Test complete dopamine receptor family"""
        dopamine_receptors = ["DRD1", "DRD2", "DRD3", "DRD4", "DRD5"]
        
        for receptor in dopamine_receptors:
            aliases = self.gene_mapper.get_aliases(receptor)
            assert receptor in aliases
            assert f"dopamine receptor D{receptor[-1]}" in aliases

        # Test specific receptor aliases
        drd1_aliases = self.gene_mapper.get_aliases("DRD1")
        assert "D1DR" in drd1_aliases
        assert "DRD1A" in drd1_aliases

        drd5_aliases = self.gene_mapper.get_aliases("DRD5")
        assert "DRD1B" in drd5_aliases  # Historical alias

    def test_monoamine_oxidase_genes(self):
        """Test MAO gene family"""
        # Test MAOA
        maoa_aliases = self.gene_mapper.get_aliases("MAOA")
        assert "MAOA" in maoa_aliases
        assert "monoamine oxidase A" in maoa_aliases
        assert "MAO-A" in maoa_aliases

        # Test MAOB
        maob_aliases = self.gene_mapper.get_aliases("MAOB")
        assert "MAOB" in maob_aliases
        assert "monoamine oxidase B" in maob_aliases
        assert "MAO-B" in maob_aliases

        # Test MAO general alias maps to MAOA by default
        assert self.gene_mapper.get_canonical_symbol("MAO") == "MAOA"

    def test_case_insensitive_handling(self):
        """Test that gene mapping is case insensitive"""
        test_cases = [
            ("snca", "SNCA"),
            ("SNCA", "SNCA"),
            ("Snca", "SNCA"),
            ("th", "TH"),
            ("TH", "TH"),
            ("dat", "SLC6A3"),
            ("DAT", "SLC6A3"),
            ("DaT", "SLC6A3")
        ]

        for input_gene, expected_canonical in test_cases:
            # Test canonical symbol mapping
            canonical = self.gene_mapper.get_canonical_symbol(input_gene)
            assert canonical == expected_canonical

            # Test aliases retrieval
            aliases = self.gene_mapper.get_aliases(input_gene)
            assert len(aliases) > 0
            assert input_gene in aliases

    def test_unknown_gene_handling(self):
        """Test handling of unknown genes"""
        unknown_genes = ["UNKNOWN_GENE", "FAKE_PROTEIN", "NOT_A_GENE"]

        for unknown_gene in unknown_genes:
            # Should return the input as canonical symbol
            canonical = self.gene_mapper.get_canonical_symbol(unknown_gene)
            assert canonical == unknown_gene.upper()

            # Should return just the input as aliases
            aliases = self.gene_mapper.get_aliases(unknown_gene)
            assert aliases == [unknown_gene]

    def test_complete_dopaminergic_pathway_coverage(self):
        """Test that all key dopaminergic pathway genes are covered"""
        key_dopaminergic_genes = [
            "TH",      # synthesis
            "DDC",     # synthesis  
            "SLC6A3",  # transport (DAT)
            "SLC18A2", # storage (VMAT2)
            "DRD1", "DRD2", "DRD3", "DRD4", "DRD5",  # receptors
            "COMT",    # metabolism
            "MAOA", "MAOB"  # metabolism
        ]

        for gene in key_dopaminergic_genes:
            aliases = self.gene_mapper.get_aliases(gene)
            assert len(aliases) > 1  # Should have at least the gene symbol plus aliases
            assert gene in aliases

    def test_parkinson_disease_gene_coverage(self):
        """Test coverage of major Parkinson's disease genes"""
        pd_genes = [
            "SNCA",   # PARK1/PARK4
            "PRKN",   # PARK2 (corrected gene symbol)
            "LRRK2",  # PARK8
            "PINK1",  # PARK6
        ]

        for gene in pd_genes:
            aliases = self.gene_mapper.get_aliases(gene)
            assert len(aliases) > 1
            assert gene in aliases

            # Each should have descriptive aliases
            assert any("PARK" in alias for alias in aliases if "PARK" in alias)

    def test_gene_symbol_corrections(self):
        """Test that gene symbol corrections are properly implemented"""
        # Test PARK2 -> PRKN correction (disease name vs gene symbol)
        park2_aliases = self.gene_mapper.get_aliases("PARK2")
        assert "PRKN" in park2_aliases
        assert "parkin" in park2_aliases

        # Test that PRKN is the canonical symbol, not PARK2
        assert self.gene_mapper.get_canonical_symbol("PARK2") == "PRKN"
        assert self.gene_mapper.get_canonical_symbol("PARKIN") == "PRKN"

    def test_enzyme_gene_coverage(self):
        """Test coverage of key enzymes in dopamine metabolism"""
        enzyme_genes = {
            "TH": ["tyrosine hydroxylase", "tyrosine 3-monooxygenase"],
            "DDC": ["DOPA decarboxylase", "aromatic L-amino acid decarboxylase"],
            "COMT": ["catechol-O-methyltransferase"]
        }

        for gene, expected_descriptions in enzyme_genes.items():
            aliases = self.gene_mapper.get_aliases(gene)
            for description in expected_descriptions:
                assert description in aliases

    def test_transporter_gene_coverage(self):
        """Test coverage of dopamine transport genes"""
        transporter_genes = {
            "SLC6A3": ["DAT", "DAT1", "dopamine transporter"],
            "SLC18A2": ["VMAT2", "vesicular monoamine transporter 2"]
        }

        for gene, expected_aliases in transporter_genes.items():
            aliases = self.gene_mapper.get_aliases(gene)
            for alias in expected_aliases:
                assert alias in aliases

    def test_bidirectional_mapping_consistency(self):
        """Test that alias-to-gene and gene-to-alias mappings are consistent"""
        # Test known alias mappings
        alias_mappings = [
            ("DAT", "SLC6A3"),
            ("VMAT2", "SLC18A2"),
            ("PARK2", "PRKN"),
            ("PARKIN", "PRKN"),
            ("ALPHA-SYNUCLEIN", "SNCA")
        ]

        for alias, expected_gene in alias_mappings:
            # Alias should map to canonical gene
            canonical = self.gene_mapper.get_canonical_symbol(alias)
            assert canonical == expected_gene

            # Check that the mapping is logically consistent
            # When we ask for aliases of the alias, we should get the canonical gene
            alias_aliases = self.gene_mapper.get_aliases(alias)
            assert expected_gene in alias_aliases, f"Expected {expected_gene} in aliases for {alias}: {alias_aliases}"
            
            # When we ask for aliases of the canonical gene, we should get meaningful aliases
            gene_aliases = self.gene_mapper.get_aliases(expected_gene)
            assert len(gene_aliases) > 1, f"Expected multiple aliases for {expected_gene}, got: {gene_aliases}"
            assert expected_gene in gene_aliases, f"Expected {expected_gene} in its own aliases: {gene_aliases}" 