import PyPDF2
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity



def extract_text_from_file(file_path):
    """Extracts text from PDF or DOCX files."""
    text = ""
    
    if file_path.endswith('.pdf'):
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
                    
    elif file_path.endswith('.docx'):
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
            
    return text

def calculate_match_score(resume_text, job_text):
    """
    Uses TF-IDF and Cosine Similarity to calculate how well a resume matches a job.
    Returns a percentage score (0 to 100).
    """
    if not resume_text or not job_text:
        return 0.0

    # 1. Combine the texts into a list
    documents = [resume_text, job_text]

    # 2. Convert text to TF-IDF vectors (ignore common English stop words like "the", "is")
    vectorizer = TfidfVectorizer(stop_words='english')
    
    try:
        tfidf_matrix = vectorizer.fit_transform(documents)
    except ValueError:
        # This happens if the text is completely empty after removing stop words
        return 0.0

    # 3. Calculate cosine similarity between document 0 (resume) and document 1 (job)
    # The result is a matrix, so we extract the [0][1] value
    similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

    # 4. Convert to percentage and round to 2 decimal places
    percentage = round(similarity_score * 100, 2)
    return percentage