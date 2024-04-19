import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 
import fitz
import pytesseract
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv


load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))



# Function to extract text from a PDF file
def extract_text_from_pdf(uploaded_file):
    reader=PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += str(page.extract_text())    
    return text



def extract_images_and_text_from_pdf(pdf_file):
    extracted_text_list = []

    pdf_data = pdf_file.read()
    pdf_document = fitz.open(stream=BytesIO(pdf_data))

    for page_number in range(pdf_document.page_count):
        page = pdf_document.load_page(page_number)

        images = page.get_images(full=True)

        for img_index, img in enumerate(images):
            xref = img[0]  # Image XREF identifier
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(BytesIO(image_bytes))

            image_text = pytesseract.image_to_string(image)
            extracted_text_list.append(image_text)

    pdf_document.close()

    return " ".join(extracted_text_list)



# response 
def model_response(raw_text, jd):
    model = genai.GenerativeModel("gemini-pro")

    promt_for_row_text = (f"I will provide raw text extracted from a candidate's resume PDF using PyPDF2. Candidates may write resumes in either columnar or row structure, resulting in improperly sequenced information. Your task is to analyze all text, properly structure it like grouping skills together, experiences together, and all relevant information with each other. Note: You will not add any extra text apart from spelling correction. In response, return the formatted text; no extra text from you should be added, and no text should be deleted."
        f"Here is the resume text: {raw_text}"
        )
    formated_text = model.generate_content(promt_for_row_text).text

    prompt = (
        f"Imagine you're a skilled or highly experienced ATS (Application Tracking System) with a deep understanding of various tech fields. Please analyze the following resume text and compare it with the provided job description."
        f"Note: The resume text has been formatted using a function; try to match it with the job description."
        f"Note: When determining the percentage match, consider the following criteria: (1) relevant field experience: 50% weight, (2) relevant skills: 30%, and (3) soft skills, certifications, and others: 20%."
        f"Strictly provide the following three details for further processing: 1) The percentage match this candidate has with the provided job description according to the given conditions, 2) Extracted skills from the job description that are not present in the resume text, and 3) A short summary in 30 words about the candidate's relevant experience or education (degree/PhD/masters).\n\n"
        f"Resume text:\n{formated_text}\n\n"
        f"Job Description:\n{jd}\n\n"
        f"Provide the output in the following format: Percentage Match: Calculated percentage, Missing Skills: Skills missing in this candidate's resume text but present in the job description, Summary: A concise 30-word summary of the candidate's profile based on the job description."
        f"Result: Determine whether the candidate is a good choice for consideration (if the score is >= 70%) or not (if the score is < 70%)."
    )

    response = model.generate_content(prompt)
    return response


# front end 
st.title("Resume Analyzer")
st.text("Minimize Time to find a perfect candidate")
job_dis = st.text_area("Job discription")
uploaded_files = st.file_uploader("Upload resume", type="pdf", help="Please upload resume in pdf format only", accept_multiple_files=True)   
submit = st.button("Submit")

# if submit and uploaded_files is not None:


if submit:
    if uploaded_files is not None:
        for resume in uploaded_files:
            text = extract_text_from_pdf(resume)
            if len(text) < 50:
                text = extract_images_and_text_from_pdf(resume)    
            response = model_response(text, job_dis)
            st.subheader(resume.name)       
            st.write(response.text)