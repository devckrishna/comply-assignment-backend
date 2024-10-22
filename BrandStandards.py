import openai
import requests
from pdf2image import convert_from_path
import io
import os
from dotenv import load_dotenv

# Set OpenAI API key
openai.api_key = os.getenv("OPEN_AI_API_KEY")

# Set your OpenAI API key and OCR.space API key here
ocr_space_api_key = os.getenv("OCR_API_KEY")

def extract_text_from_pdf(pdf_file_path):
    """Extracts text from the given PDF file."""
    from PyPDF2 import PdfReader
    with open(pdf_file_path, 'rb') as pdf_file:
        reader = PdfReader(pdf_file)
        text = ""
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
    return text

def extract_text_from_image_with_ocr_space(image):
    """Extract text from an image using OCR.space API."""
    # Convert image to bytes
    image_content = io.BytesIO()
    image.save(image_content, format='JPEG')
    image_content.seek(0)

    # Send image to OCR.space API for text extraction, specifying filetype
    response = requests.post(
        'https://api.ocr.space/parse/image',
        files={'filename': ('image.jpg', image_content, 'image/jpeg')},
        data={
            'apikey': ocr_space_api_key,
            'language': 'eng',  # OCR language
        }
    )

    # Handle API response
    result = response.json()
    if result.get("IsErroredOnProcessing"):
        raise Exception(f"OCR.space error: {result.get('ErrorMessage')}")
    
    extracted_text = result.get("ParsedResults")[0].get("ParsedText", "")
    return extracted_text

def extract_images_from_pdf(pdf_file_path):
    """Extracts images from the PDF file and returns their text descriptions using OCR.space API."""
    images = convert_from_path(pdf_file_path)
    image_texts = []
    
    for img_num, image in enumerate(images):
        # Extract text from the image using OCR.space API
        text_from_image = extract_text_from_image_with_ocr_space(image)
        image_texts.append(f"Image {img_num + 1} text: {text_from_image.strip()}")
        
    return image_texts

def check_compliance_with_guidelines(pdf_text, image_texts):
    """Checks if the ad content complies with the brand guidelines using OpenAI."""
    guidelines_summary = """
    1. Logo Usage
Colors: Use the official Mutual of Omaha logo in the preferred blue color (Pantone PMS 654). Black (Positive) and white (Reverse) versions are acceptable when appropriate.

Proportions and Alterations: Do not alter, distort, or recolor the logo. The logo's dimensions and design elements must remain consistent.

Spacing ("Mutual-space"): Maintain a minimum clear space around the logo equal to the height of the "M" in "Mutual." No other graphics or text should invade this space.

Backgrounds: Ensure sufficient contrast between the logo and the background. Avoid placing the logo on backgrounds that make it difficult to read, such as red, pink, or orange.

Common Mistakes to Avoid:

Do not invert the colors improperly.
Do not modify the typeface or separate the symbol from the text.
Do not use the lion symbol alone without approval.
Do not stretch or compress the logo disproportionately.
2. Typography
Fonts: Use the specified brand fonts:

Primary Font: Gotham (for headings and prominent text).
Secondary Font: Archer (for subheadings and body text).
Hierarchy: Establish a clear typographic hierarchy using size, weight, and style to guide the reader through the content.

Consistency: Apply fonts uniformly across all materials to maintain brand cohesion.

Legibility: Ensure that font sizes are readable across different formats and devices.

3. Color Palette
Primary Colors:

Omaha Blue: Pantone PMS 654 (used for logos, headings, and key elements).
White and Gray Tones: For backgrounds and supporting elements.
Usage:

Stick to the approved colors for all design elements.
Ensure text has sufficient contrast against backgrounds for readability.
Avoid:

Introducing unapproved colors.
Using colors that clash or dilute the brand identity.
4. Photography
Style:

Tone: Natural, personal, warm, and optimistic.
Setting: Authentic, journalistic, and unstaged environments.
People: Subjects should appear confident, comfortable, approachable, and diverse.
Guidelines:

Use candid shots of real people in genuine moments.
Ensure images tell a story and resonate emotionally.
Photos should be well-lit with natural color correction.
Avoid:

Staged or posed photographs.
Generic or cliché images.
Overuse of filters or artificial effects.
5. Voice & Tone
Overall Tone: Communicate like a trusted friend—honest, devoted, approachable, and optimistic.

Language:

Use conversational and warm language without being overly casual.
Incorporate contractions (e.g., "you're," "we'll") for a friendly tone.
Write in first and second person ("we," "you") to engage the reader directly.
Clarity:

Use short, simple sentences and common words.
Be concise while ensuring the message is clear.
Avoid:

Insurance jargon and technical terms.
Formal or stiff language.
Overly promotional or exaggerated statements.
6. Layout & Design
Consistency: Follow established design patterns for structure and flow.

Whitespace:

Use adequate spacing around elements to prevent clutter.
Ensure text and images have breathing room for better readability.
Alignment:

Align text and graphics in a way that guides the reader's eye naturally through the content.
Imagery Integration:

Integrate photos and illustrations seamlessly with the text.
Ensure visuals support and enhance the message.
7. Illustrations
Style:

Illustrations should be approachable, light, and consistent with the brand's visual identity.
Use simple lines and shapes with the approved color palette.
Usage:

Spot Illustrations: Typically placed within a gray circle background (#e9e9e9) and used to complement specific sections.
Detailed Illustrations: Used as hero images or to separate content sections, primarily in digital formats.
Creation:

Any new illustrations should adhere to the brand's guidelines.
Consult with the brand team or creative services manager for approval and assistance.
8. Technical Guidelines
Accessibility:

Include alt text for images that convey important information.
Ensure text over images is readable and meets accessibility standards.
Image Optimization:

Optimize images for web use to minimize load times.
Use appropriate file sizes and formats for different devices and screen resolutions.
Legal Considerations:

Only use images and fonts that Mutual of Omaha has the rights to use.
Avoid any copyrighted material without proper permission.
9. Common Mistakes to Avoid
Logo Misuse:

Do not alter the logo's color, orientation, or components.
Avoid using the logo on incompatible backgrounds.
Typography Errors:

Do not substitute unapproved fonts.
Avoid inconsistent font sizes and styles.
Photography Missteps:

Do not use images that appear posed, artificial, or heavily edited.
Avoid clichés and overused stock photos.
Voice Misalignment:

Avoid formal or bureaucratic language.
Do not use third-person references that distance the reader.
    """

    # Prepare image descriptions
    image_description = "\n".join(image_texts)

    prompt = f"""
    The following is a PDF content extracted from an ad:

    {pdf_text}

    The ad also contains the following images:

    {image_description}

    Evaluate the ad based on the following brand guidelines:

    {guidelines_summary}

    Provide a detailed evaluation of which sections of the ad comply with the guidelines and which do not. clearly highlight the section which is non-compliant Include reasons for non-compliance. give concrete answers and assume things if neccesary
    """

    # Call the OpenAI API to analyze the content
    messages = [
        {"role": "system", "content": "You are an assistant that evaluates compliance based on insurance regulations."},
        {"role": "user", "content": prompt}
    ]
    
    response = openai.chat.completions.create(
        model="gpt-4o",  # Use GPT-4-turbo or GPT-4
        messages=messages,
        max_tokens=500  # Adjust based on your needs
    )

    return response.choices[0].message.content.strip()

def analyze_pdf_for_compliance(pdf_file_path):
    """Main function to analyze the PDF and provide a compliance report."""
    # Step 1: Extract text from PDF
    pdf_text = extract_text_from_pdf(pdf_file_path)
    
    # Step 2: Extract images and their descriptions using OCR.space API
    image_texts = extract_images_from_pdf(pdf_file_path)

    # Step 3: Check compliance using OpenAI API
    compliance_report = check_compliance_with_guidelines(pdf_text, image_texts)

    # Step 4: Return or print the report
    return compliance_report

# Example Usage:
def get_brand_standards(pdf_file_path):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Define the path relative to BASE_DIR
    pdf_path = pdf_file_path
    compliance_report = analyze_pdf_for_compliance(pdf_path)
    return compliance_report
