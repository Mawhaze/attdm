import fitz  # PyMuPDF
import logging
import requests

class PDFProcessor:
    def __init__(self):
        self.keys = {
            "49.46,": "name",
            "272.72, 77.16, 524.02, 88.15": "species",
            "272.72, 51.12": "class_level",
            "43.36, 627.18, 58.48, 642.12": "passive_perception",
            "43.54, 688.03, 58.65, 702.97": "passive_investigation",
            "43.37, 657.18, 58.48, 672.12": "passive_insight",
            "114.18": "inventory",
            "351.5": "inventory",
        }

    def get_pdf_from_url(self, character_id):
        url = f"https://www.dndbeyond.com/sheet-pdfs/{character_id}.pdf"
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            if 'application/pdf' not in response.headers.get('Content-Type', '').lower():
                print("Warning: The URL does not point to a PDF file.")
                return None
            return response.content
        except requests.exceptions.RequestException as e:
            print(f"Error downloading PDF: {e}")
            return None

    def convert_pdf_to_json(self, pdf_data):
        data = {"pages": []}
        try:
            with fitz.open(stream=pdf_data, filetype="pdf") as pdf:
                for page_number in range(len(pdf)):
                    page = pdf[page_number]
                    text = page.get_text("text")
                    blocks = page.get_text("blocks")
                    structured_data = page.get_text("dict")
                    structured_data = self._clean_dict(structured_data)
                    page_data = {
                        "page_number": page_number + 1,
                        "text": text.strip() if text else "",
                        "blocks": blocks,
                        "structured_data": structured_data,
                    }
                    data["pages"].append(page_data)
            return data
        except Exception as e:
            print(f"Error during conversion: {e}")
            return None

    def _clean_dict(self, d):
        if isinstance(d, dict):
            return {k: self._clean_dict(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [self._clean_dict(v) for v in d]
        elif isinstance(d, bytes):
            return d.decode("utf-8", errors="ignore")
        else:
            return d

    def process_json_document(self, json_data):
        processed_data = {}
        for page in json_data.get('pages', []):
            blocks = page.get('blocks', [])
            for block in blocks:
                if len(block) >= 5:
                    field_location_list = [round(coord, 2) for coord in block[:4]]
                    field_location = ', '.join(map(str, field_location_list))
                    field_value = block[4].strip().split("\n")[0]
                    # # Enable for debugging
                    # # Add data to debug lists regardless of keys filter
                    debug_info = {
                        "location_value_pairs": []
                    }
                    # debug_info["all_field_locations"].append(field_location)
                    # debug_info["all_field_values"].append(field_value)
                    debug_info["location_value_pairs"].append({
                        "location": field_location,
                        "value": field_value
                    })
                    logging.debug(f"PDF debug info: {debug_info}")
                    for key_prefix, desired_key in self.keys.items():
                        if field_location.startswith(key_prefix):
                            if desired_key == "inventory":
                                if "inventory" not in processed_data:
                                    processed_data["inventory"] = []
                                processed_data["inventory"].append(field_value)
                            else:
                                processed_data[desired_key] = field_value
                            break
        return processed_data

    def process_character_sheet(self, character_id):
        pdf_data = self.get_pdf_from_url(character_id)
        if pdf_data:
            json_data = self.convert_pdf_to_json(pdf_data)
            if json_data:
                return self.process_json_document(json_data)
        return None
