
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():

    # Step 1: Find the MCP server
    server_path = Path(__file__).resolve().parent / "retrieval" / "mcp_server.py"

    print("Server file exists:", server_path.exists(), flush=True)

    # Step 2: Configure the server
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "retrieval.mcp_server"]
    )

    # Step 3: Connect to the MCP server
    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()
            print("Connected to MCP server!")

            # Step 4: Discover available tools
            tools = await session.list_tools()

            print("\nAvailable tools:")
            for tool in tools.tools:
                print("-", tool.name)

            # Step 5: Search NCBI Gene
            print("\nSearching NCBI Gene...", flush=True)

            gene_result = await session.call_tool(
                "lookup_ncbi_gene",
                {"gene_name": "PKD1"}
            )

            print("\nGene lookup result:")

            if gene_result.isError:
                print("Gene lookup tool failed:")

            for content in gene_result.content:
                if content.type == "text":
                    print(content.text)

            # Step 6: Search PubMed
            print("\nSearching PubMed...", flush=True)

            pubmed_result = await session.call_tool(
                "search_pubmed_articles",
                {
                    "query": "PKD1 AND ADPKD",
                    "max_results": 2
                }
            )

            print("\nPubMed research result:")

            if pubmed_result.isError:
                print("PubMed lookup tool failed:")

            for content in pubmed_result.content:
                if content.type == "text":
                    print(content.text)


if __name__ == "__main__":
    asyncio.run(main())
