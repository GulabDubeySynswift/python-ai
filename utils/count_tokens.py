import tiktoken

enc = tiktoken.get_encoding("cl100k_base")

def count_tokens(text):
    return len(enc.encode(text))


def validate_tokens(documents, MAX_TOKENS =8000):
    for doc in documents:
        tokens = count_tokens(doc.text)
        print("tokens: ", tokens)
        if tokens > MAX_TOKENS:
            raise Exception("Too large, need chunking")