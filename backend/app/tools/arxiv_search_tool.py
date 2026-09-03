import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from app.tools.base_tool import BaseTool


class ArxivSearchTool(BaseTool):
    name = "search_arxiv_papers"
    description = "Queries the official ArXiv API for research papers, preprints, and academic baseline implementations."

    def execute(self, query: str) -> str:
        if not query:
            return "No search query provided."
            
        clean_q = query[:80].strip()
        encoded = urllib.parse.quote(clean_q)
        url = f"http://export.arxiv.org/api/query?search_query=all:{encoded}&start=0&max_results=3"
        
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Synthexis/2.0 Research Platform"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                xml_data = resp.read().decode('utf-8')
                
            root = ET.fromstring(xml_data)
            # Namespace for Atom feed
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('atom:entry', ns)
            
            if not entries:
                return f"No ArXiv paper entries found for query '{clean_q}'."
                
            results = []
            for entry in entries:
                title = entry.find('atom:title', ns)
                title_text = title.text.strip().replace('\n', ' ') if title is not None and title.text else "Untitled"
                
                published = entry.find('atom:published', ns)
                pub_date = published.text[:10] if published is not None and published.text else "N/A"
                
                summary = entry.find('atom:summary', ns)
                summary_text = summary.text.strip().replace('\n', ' ')[:250] if summary is not None and summary.text else "N/A"
                
                pdf_url = "N/A"
                for link in entry.findall('atom:link', ns):
                    if link.attrib.get('title') == 'pdf':
                        pdf_url = link.attrib.get('href', 'N/A')
                        break
                        
                results.append(f"• **{title_text}** ({pub_date})\n  Summary: {summary_text}...\n  PDF: {pdf_url}")
                
            return "\n\n".join(results)
        except Exception as e:
            return f"ArXiv Search notice: Bypassed ArXiv search for '{clean_q}' ({str(e)})."
