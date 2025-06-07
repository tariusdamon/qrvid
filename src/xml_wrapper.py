"""
XML wrapper module for QR code payloads.
"""
import xml.etree.ElementTree as ET
import logging


class XMLWrapper:
    def __init__(self, config):
        self.config = config
        self.template = config.get("xml_template", 
            '<doc page="{page_num}" x="@tariusdamon" file="{filename}" chunk="{chunk_id}" total="{total_chunks}">{content}</doc>')
    
    def create_xml_payload(self, content, page_num, filename, chunk_id, total_chunks):
        """Create XML wrapper for content."""
        xml_content = self.template.format(
            page_num=page_num,
            filename=filename,
            chunk_id=chunk_id,
            total_chunks=total_chunks,
            content=content
        )
        
        # Ensure we don't exceed chunk size
        max_size = self.config.get("max_chunk_size", 2048)
        if len(xml_content) > max_size:
            # Reduce content size to fit
            max_content_size = max_size - len(xml_content) + len(content)
            if max_content_size > 0:
                content = content[:max_content_size]
                xml_content = self.template.format(
                    page_num=page_num,
                    filename=filename,
                    chunk_id=chunk_id,
                    total_chunks=total_chunks,
                    content=content
                )
            else:
                logging.error(f"XML overhead too large for chunk size {max_size}")
                return None
                
        return xml_content
    
    def parse_xml_payload(self, xml_data):
        """Parse XML payload to extract metadata and content."""
        try:
            root = ET.fromstring(xml_data)
            
            return {
                "page": int(root.get("page")),
                "x": root.get("x"),
                "file": root.get("file"),
                "chunk": int(root.get("chunk")),
                "total": int(root.get("total")),
                "content": root.text if root.text else ""
            }
            
        except ET.ParseError as e:
            logging.error(f"XML parsing error: {e}")
            return None
        except (ValueError, TypeError) as e:
            logging.error(f"Error parsing XML attributes: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error parsing XML: {e}")
            return None
    
    def validate_xml_structure(self, xml_data):
        """Validate XML structure and required attributes."""
        parsed = self.parse_xml_payload(xml_data)
        if not parsed:
            return False
        
        required_attrs = ["page", "x", "file", "chunk", "total"]
        for attr in required_attrs:
            if attr not in parsed or parsed[attr] is None:
                logging.error(f"Missing required attribute: {attr}")
                return False
        
        # Validate x attribute
        if parsed["x"] != "@tariusdamon":
            logging.warning(f"Unexpected x attribute value: {parsed['x']}")
        
        return True
