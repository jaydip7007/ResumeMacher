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

    promt_for_row_text = f"I will provide a raw text which is extracted from a candidates resume pdf using PyPDF2, now candidate might wirten resume in coloumn structure or in a row structure, so the extracted text might not have proper information in sequential mennar, your task is to analyse all text, structe all this text proparlly like put skills togather , experience togather and all the relavent information with each other togather, Note: you will not do any creativity, you will not add any extra text appart from spelling correction, in response just retutn the formated text , no extra text from you should be added, no text should be deleted from you,  here is the resume text: {raw_text}"
    formated_text = model.generate_content(promt_for_row_text).text

    prompt = (
        f"Act Like you are a skilled or very experience ATS(Application Tracking System)with a deep understanding of almost all tech field. Please analyze the following resume text and compare it with the job description provided"
        f"Note: resume text is formated using function try to match it job discription"
        f"Note: For counting how many percentage this profile matches with candidate keep following points in considreation (1)relavent field experience : 50% weight (2) relavent skill : 30% (3) soft-skills, certifications and other : 20%"
        f"strictly provide following 3 details 1) how many percetage this candidate matche with job description 2)Missing skills of candidate according to job discription, title in header-3 3)a short summury in 30 to 40 words about candidates rillevent experience or schooing\n\n, title in header-3"
        f"Resume text:\n{formated_text}\n\n"
        f"Job Description:\n{jd}\n\n"
        f"provide the output as shown in example bellow format Percentage Match: 74%, Missing Skills:Backend, AWS, JIRA, Web Designing, Summary: 30 word summary about profile in basis of job discription, Candidate is good choice to take into considration(if score is >= 70%) or Candidate might not be good choice to take into considration(if score is <70%)"
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
            if len(text) < 100:
                text = extract_images_and_text_from_pdf(resume)    
            response = model_response(text, job_dis)
            st.subheader(resume.name)       
            st.write(response.text)