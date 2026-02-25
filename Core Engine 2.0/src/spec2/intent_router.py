from typing import Literal

def infer_intent(request: str) -> Literal["search","auth","cart","navigate","generic"]:
    q = (request or "").lower()
    if any(k in q for k in ["search","find","look for"]): return "search"
    if any(k in q for k in ["login","sign in","username","password"]): return "auth"
    if "cart" in q or "wishlist" in q: return "cart"
    if any(k in q for k in ["go to","navigate","open "]): return "navigate"
    return "generic"