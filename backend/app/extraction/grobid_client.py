import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from app.core.config import settings


def parse_grobid_header(pdf_path: str) -> Optional[Dict[str, Any]]:
    """Sends PDF to Grobid server to extract structured TEI metadata header."""
    url = f"{settings.GROBID_URL}/api/processHeaderDocument"
    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
            
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="input"; filename="paper.pdf"\r\n'
            f"Content-Type: application/pdf\r\n\r\n"
        ).encode('utf-8') + pdf_bytes + f"\r\n--{boundary}--\r\n".encode('utf-8')
        
        req = urllib.request.Request(
            url, 
            data=body, 
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml_content = resp.read().decode('utf-8')
            
        root = ET.fromstring(xml_content)
        title_node = root.find(".//{http://www.tei-c.org/ns/1.0}titleStmt/{http://www.tei-c.org/ns/1.0}title")
        title = title_node.text if title_node is not None and title_node.text else ""
        
        authors = []
        for author in root.findall(".//{http://www.tei-c.org/ns/1.0}author"):
            name = author.find(".//{http://www.tei-c.org/ns/1.0}persName")
            if name is not None:
                parts = [p.text for p in name if p.text]
                if parts:
                    authors.append(" ".join(parts))
                    
        return {"title": title, "authors": authors}
    except Exception as e:
        print(f"[GROBID WARN] Grobid header parsing bypassed ({e}).")
        return None
