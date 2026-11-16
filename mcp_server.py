
from mcp.server.fastmcp import FastMCP
from gene_tools import search_gene, search_ncbi_gene
from pubmed_tools import research_pubmed
import requests

# Step 1: Create MCP server
mcp = FastMCP("GeneDiseaseResearchAssistant")


# Step 2: Register tools
@mcp.tool()
def lookup_gene(gene_name: str) -> dict:
    """Look up a gene in the local sample database."""
    result = search_gene(gene_name)

    if result is None:
        return {"status": "not_found"}

    return {"status": "found", **result}


@mcp.tool()
def lookup_ncbi_gene(gene_name: str) -> dict:
    """Retrieve a human gene record from NCBI."""
    result = search_ncbi_gene(gene_name)
    return {"status": "found", **result} if result else {"status": "not_found"}


@mcp.tool()
def search_pubmed_articles(
    query: str,
    max_results: int = 3
) -> dict:
    """Search PubMed and retrieve scientific abstracts."""
    articles = research_pubmed(query, max_results)

    return {
        "status": "success",
        "article_count": len(articles),
        "articles": articles
    }


# Step 3: Start server LAST
if __name__ == "__main__":
    mcp.run()
