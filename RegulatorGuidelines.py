import openai
import pdfplumber
import re
import os
from dotenv import load_dotenv

# Set OpenAI API key
openai.api_key = os.getenv("OPEN_AI_API_KEY")


# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    return text

#Function to extract text from a .txt file, with error handling for encoding issues
def extract_text_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:  # 'ignore' invalid characters
        text = file.read()
    return text

# Function to split MDL-570 text into sections by titles like "Section 1", "Section 2"
def split_into_sections(text):
    section_pattern = r'(Section \d+: .+?)(?=(Section \d+:|\Z))'
    sections = re.split(section_pattern, text, flags=re.DOTALL)
    
    section_pairs = []
    
    for i in range(1, len(sections), 2):
        section_title = sections[i].strip()  # This is the section title
        section_content = sections[i + 1].strip() if (i + 1) < len(sections) else ""  # This is the section content
        section_pairs.append((section_title, section_content))
    
    return section_pairs

# Function to analyze a segment of text using OpenAI's updated API against a smaller section of MDL-570
def evaluate_compliance(text, mdl_section, section_title):
    messages = [
        {"role": "system", "content": "You are an assistant that evaluates compliance based on insurance regulations."},
        {"role": "user", "content": f"Evaluate the following ad text for compliance with this section of the MDL-570 guidelines.\n\nAd text: {text}\n\nMDL-570 section: {mdl_section}\n\nBased on this MDL-570 section ({section_title}), is the ad text compliant? mention specifically which part is compliant which part is not and the reason why"}
    ]
    
    response = openai.chat.completions.create(
        model="gpt-4o",  # Use GPT-4-turbo or GPT-4
        messages=messages,
        max_tokens=500  # Adjust based on your needs
    )
    
    return response.choices[0].message.content.strip()

# Main function to evaluate ad against multiple sections of MDL-570 guidelines
def evaluate_ad_compliance(ad_pdf_path, mdl_pdf_path):
    # Extract text from both the ad and the MDL-570 PDF
    ad_text = extract_text_from_pdf(ad_pdf_path)
    mdl_guidelines_text = extract_text_from_txt(mdl_pdf_path)
    
    # Split ad text into logical parts for evaluation
    ad_segments = re.split(r'\n\s*\n', ad_text.strip())  # Splits the ad into logical paragraphs

    # Split the MDL-570 text into sections using custom splitting logic (you can modify this)
    mdl_sections = split_into_sections(mdl_guidelines_text)
    
    mdl_section_titles = [f"Section {i+1}" for i in range(len(mdl_sections))]  # Label sections sequentially
    # print((mdl_section_titles))
    compliance_results = []
    
    # Iterate over each ad segment and evaluate it against each section of MDL-570
    for segment in ad_segments:
        for mdl_section, section_title in zip(mdl_sections, mdl_section_titles):
            result = evaluate_compliance(segment, mdl_section, section_title)
            compliance_results.append({
                "Ad Segment": segment[:500] + ".....",
                "MDL Section": section_title,
                "Evaluation": result
            })
    
    return compliance_results

# Helper function to print non-compliant results
def print_non_compliant_results(compliance_results):
    print("Non-Compliant Results:")
    for result in compliance_results:
        print(result['Evaluation'])
        if "Non-Compliant" in result['Evaluation']:
            print(f"\nAd Segment: {result['Ad Segment']}")
            print(f"MDL Section: {result['MDL Section']}")
            print(f"Evaluation: {result['Evaluation']}\n")


def get_regulator_compliance(pdf_path):
  # Usage Example
  BASE_DIR = os.path.dirname(os.path.abspath(__file__))

  # Define the paths relative to BASE_DIR
  ad_pdf_path = pdf_path
  mdl_pdf_path = os.path.join(BASE_DIR, 'MDL-570.txt')

  compliance_results = evaluate_ad_compliance(ad_pdf_path, mdl_pdf_path)
  
  print(compliance_results)

  return compliance_results
