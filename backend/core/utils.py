import PyPDF2
import docx
import re
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
    Calculates score AND extracts the overlapping keywords/skills.
    Returns a dictionary: {"score": float, "matched_keywords": list}
    """
    if not resume_text or not job_text:
        return {"score": 0.0, "matched_keywords": []}

    # 1. Clean the text slightly (remove punctuation to prevent mismatches)
    def clean_text(text):
        return re.sub(r'[^\w\s]', '', text.lower())

    clean_resume = clean_text(resume_text)
    clean_job = clean_text(job_text)
    documents = [clean_resume, clean_job]

    # Vectorize
    vectorizer = TfidfVectorizer(stop_words='english')
    
    try:
        tfidf_matrix = vectorizer.fit_transform(documents)
    except ValueError:
        return {"score": 0.0, "matched_keywords": []}

    #Calculate Cosine Similarity
    similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    percentage = round(similarity_score * 100, 2)

    # EXTRACT MATCHING SKILLS and Get the vocabulary (all unique words)
    feature_names = vectorizer.get_feature_names_out()
    
    # Get the TF-IDF scores for the resume (index 0) and job (index 1)
    resume_vector = tfidf_matrix[0].toarray()[0]
    job_vector = tfidf_matrix[1].toarray()[0]
    
    matched_keywords = []
    for i in range(len(feature_names)):
        # If the word has a score > 0 in BOTH the resume and the job, it's a match!
        if resume_vector[i] > 0 and job_vector[i] > 0:
            # We combine the scores to rank the most important matches
            match_weight = resume_vector[i] + job_vector[i]
            matched_keywords.append((feature_names[i], match_weight))
            
    # Sort matches by highest weight and take the top 10
    matched_keywords = sorted(matched_keywords, key=lambda x: x[1], reverse=True)[:10]
    
    # Capitalize for nice display
    skills_list = [word.capitalize() for word, weight in matched_keywords]

    return {
        "score": percentage,
        "matched_keywords": skills_list
    }