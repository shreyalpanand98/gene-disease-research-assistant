
from gene_tools import search_ncbi_gene

gene = input("Enter a gene symbol: ")

try:
    result = search_ncbi_gene(gene)

    if result is not None:
        print("\nGene found!")
        print("Gene ID:", result["gene_id"])
        print("Symbol:", result["symbol"])
        print("Description:", result["description"])
        print("Summary:", result["summary"])
        print("Source:", result["source"])
    else:
        print("No exact match found in the returned NCBI records.")

except Exception as error:
    print("NCBI request failed:", error)
