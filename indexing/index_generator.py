import os
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import time
import re
import pickle

mantid_repo_location = r'C:\Codes\mantid'
index_save_location =  'docs_index.faiss'
documents_save_location = 'docs_paragraphs.pkl'

# Load embedding model
embed_model = SentenceTransformer('all-MiniLM-L6-v2')
paragraph_sep = "#@#@"

def clean_rst(text):
    """Clean RST annotations and markup from text."""

    # remove tables
    text = re.sub(r'(?ms)^(\+[-=+]+\n(?:\|.*\n)+\+[-=+]+)\n?', '', text)

    # Remove directives such as .. contents or .. figure
    text = re.sub(r'(?ms)^\.{2}\s+\w+::.*?(?=\n\S|\Z)', '', text)

    # Remove code blocks
    text = re.sub(r'(?ms)^\.{2}\s*code-block::.*?(?=\n\S|\Z)', '', text)

    # remove hlist sections
    text = re.sub(r'(?ms)^ *\.\. hlist::.*?(?=\n\S|\Z)', '', text)

    # Remove comments/directives starting with '..'
    text = re.sub(r'\.\. .*', '', text)

    # Remove inline roles like :ref:`label` or :class:`ClassName`
    text = re.sub(r':\w+:`[^`]*`', '', text)
    
    # Remove bold/italic markup
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    
    text = re.sub(r'\*([^*]+)\*', r'\1', text)

    # <> around ULRs
    text = re.sub(r'<([^>]+)>', '', text)

    # # Remove headings with =
    text = re.sub(r'=+\n.+\n=+\n', '', text)

    # collapse sub headings with its text
    text = re.sub(r"(?m)^([^\n]+)\n[=#^~`-]{3,}\s*$", r"\1. ", text)
    # Collapse extra blank lines
    text = re.sub(r"\n{2,}", "\n", text)

    # Remove bullet markers
    text = re.sub(r"(?m)^\s*\*\s*", "", text)     # remove '* '
    text = re.sub(r"(?m)^\s*#\.\s*", "", text)    # remove '#. '
    
    # Collapse multiple newlines
    text = re.sub(r'\n{2,}', paragraph_sep, text)

    # flatten any numbered lists
    text = re.sub("^[0-9.]+", " ", text, flags=re.MULTILINE)

    # remove bullet lists
    text = re.sub(r"^- ", " ", text)

    # flatten newlines
    text = re.sub('\n', ' ', text)

    # remove text wrapped with double ``
    text = re.sub(r'`{2}', ' ', text)

    # remove text wrapped with single `
    text = re.sub(r'`{1}', ' ', text)

    # remove residual ' _'
    text = re.sub(r' _', ' ', text, flags=re.MULTILINE)

    # remove residual spaces
    text = re.sub(r" {2,}", ' ', text)

    text = re.sub(paragraph_sep, '\n\n', text, flags=re.MULTILINE)
    return text.strip()


def clean_md(text):
    """Clean Markdown formatting and annotations."""
    # Remove code blocks (```...```)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    
    # Remove inline code (`...`)
    text = re.sub(r'`[^`]+`', '', text)
    
    # Remove images ![alt](url)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    
    # Remove links [text](url), keep only text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove bold/italic (**text** or *text*)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    
    # Remove HTML tags if any
    text = re.sub(r'<[^>]+>', '', text)
    
    # Collapse multiple newlines
    text = re.sub(r'\n{2,}', '\n\n', text)

    # remove tables
    text = re.sub(r'(?sm)^\|.*\|\s*\n^\|(?:\s*[-:]+\s*\|)+\s*\n(?:^\|.*\|\s*\n)*', '', text)

    # remove headers
    text = re.sub(r'(?m)^[^\n]+\n[=-]{3,}\s*$', ' ' , text)

    # remove commented blocks
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # remove front matter block
    text = re.sub("(\A---\s*\n[\s\S]*?\n---\s*)", "", text, flags=re.MULTILINE)

    # Remove headings (#, ##, ### ...)
    text = re.sub(r'^\s*#{1,6}\s+', paragraph_sep, text, flags=re.MULTILINE)

    # remove [text](url) lines
    text = re.sub(r'\[`?.*?`?\]\(.*?\)', '', text)

    # remove Markdown-style reference links
    text = re.sub(r'^\[.*?\]: .*$\n?', '', text, flags=re.MULTILINE)

    # flatten any numbered lists
    text = re.sub("^[0-9.]+", " ", text, flags=re.MULTILINE)

    # remove bullet lists
    text = re.sub(r"^- ", " ", text)

    # flatten newlines whithin paragraphs
    text = re.sub(r"\n", " ", text)

    # remove residual spaces
    text = re.sub(r" {2,}", ' ', text)
    
    text = re.sub(paragraph_sep, '\n\n', text, flags=re.MULTILINE)
    return text.strip()


# Load text files
docs = []
file_paths = []

def process_cleaned_txt(text):
    global paragraphs, file_paths, docs

    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    for i in range(len(paragraphs)-1, -1, -1):
        if len(paragraphs[i].splitlines()) <= 2 and len(paragraphs[i]) < 60:
            del paragraphs[i]

    docs.extend(paragraphs)
    file_paths.extend([file_name]*len(paragraphs))
    

for root, dirs, files in os.walk(mantid_repo_location):
    for file_name in files:
        if file_name.endswith('.rst'):
            with open(os.path.join(root, file_name), 'r', encoding='utf-8') as f:
                text = f.read()
                text = clean_rst(text)
                process_cleaned_txt(text)

        if file_name.endswith('.md'):
            with open(os.path.join(root, file_name), 'r', encoding='utf-8') as f:
                text = f.read()
                text = clean_md(text)
                process_cleaned_txt(text)
             

t1 = time.time()
print("Converting paragraphs to embeddings")

# Convert paragraphs to embeddings
embeddings = embed_model.encode(docs, convert_to_numpy=True)
t2 = time.time()

print(f"It has taken {t2-t1}s to embed all the files")

# Build FAISS index
dimension = embeddings.shape[1]
print(f"Dimensionality of embedding space={dimension}")

index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

print(f"Indexed {len(docs)} paragraphs from {len(set(file_paths))} files.")

print("Saving the index file ..")
faiss.write_index(index, index_save_location)

print("Saving the documents..")
with open(documents_save_location, "wb") as f:
    pickle.dump(docs, f)