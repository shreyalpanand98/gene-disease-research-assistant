from gene_tools import search_gene

print("Welcome to the Gene-disease Research Assistant!")

gene = input("Enter gene name: ").strip().upper()

result = search_gene(gene)

if result is not None:
    print("\nGene:", gene)
    print("Associated disease:", result["disease"])
    print("Protein:", result["protein"])
else:
    print("Gene not found in database")