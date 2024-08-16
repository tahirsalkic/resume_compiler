import json
import tiktoken

def load_prompts():
    with open('resume_compiler/ai/prompts.json', 'r') as f:
        return json.load(f)
    
def fit_prompts(system_prompt: str, user_prompt: str, encoding_name, max_tokens=128000):
    encoding = tiktoken.encoding_for_model(encoding_name)
    tokens1 = encoding.encode(system_prompt)
    tokens2 = encoding.encode(user_prompt)
    total_tokens = len(tokens1) + len(tokens2)
    if total_tokens > max_tokens:
        tokens_to_remove = total_tokens - max_tokens
        if len(tokens2) > tokens_to_remove:
            tokens2 = tokens2[:len(tokens2) - tokens_to_remove]
        else:
            tokens2 = []
        user_prompt = encoding.decode(tokens2)
    return system_prompt, user_prompt
