import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# Google Custom Search API configuration
API_KEY = "AIzaSyB4vIkEsywN13MZ3Cf2bwvZ6sD2Wkx_SF4"
SEARCH_ENGINE_ID = "e601386b9793f4353"
URL = "https://www.googleapis.com/customsearch/v1"

# Gemini API configuration
GEMINI_API_KEY = "AIzaSyDXmYwgu7hu9iQwFwIQcYCQ_G9hmNYdh6g"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def verify_claim_with_gemini(claim, evidence=None):
    """Verify a claim using Gemini API, with or without external evidence."""
    if evidence:
        prompt = (
            f"Given the claim: '{claim}'\n"
            f"And the evidence: '{evidence}'\n"
            "Determine if the evidence supports (ENTAILMENT), contradicts (CONTRADICTION), "
            "or is inconclusive (NEUTRAL) about the claim. Respond with one of these labels: "
            "ENTAILMENT, CONTRADICTION, NEUTRAL, followed by a brief explanation."
        )
    else:
        prompt = (
            f"Given the claim: '{claim}'\n"
            "Based on your knowledge of news events up to March 18, 2025, determine if this claim "
            "is supported (ENTAILMENT), contradicted (CONTRADICTION), or inconclusive (NEUTRAL). "
            "Respond with one of these labels: ENTAILMENT, CONTRADICTION, NEUTRAL, followed by a brief explanation. "
            "If the claim references events after March 17, 2025, assume it’s breaking news from March 17 and evaluate "
            "based on plausible trends or prior context."
        )
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        print(f"Gemini API response: {response_text}")

        if "ENTAILMENT" in response_text.upper():
            verdict = "ENTAILMENT"
            confidence = 0.9
        elif "CONTRADICTION" in response_text.upper():
            verdict = "CONTRADICTION"
            confidence = 0.9
        else:
            verdict = "NEUTRAL"
            confidence = 0.5

        return [(verdict, confidence)], verdict
    except Exception as e:
        print(f"Error with Gemini API: {e}")
        return [("NEUTRAL", 0.0)], "NEUTRAL"

def get_web_evidence(claim, num_results=5, start_index=0):
    """Fetch evidence from the web starting at a given index."""
    query = " ".join(claim.split()[:10])  # First 10 words of the claim
    params = {"q": query, "key": API_KEY, "cx": SEARCH_ENGINE_ID, "num": num_results}
    try:
        response = requests.get(URL, params=params, timeout=10)
        response.raise_for_status()
        results = response.json()

        if "items" not in results or start_index >= len(results["items"]):
            print(f"No search results found or index {start_index} out of range.")
            return None, "No credible evidence found.", results

        link = results["items"][start_index]["link"]
        print(f"Attempting result {start_index + 1}: {link}")
        
        try:
            page_response = requests.get(link, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }, timeout=10)
            page_response.raise_for_status()
            soup = BeautifulSoup(page_response.content, "html.parser")
            paragraphs = soup.find_all("p")
            raw_evidence = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]

            evidence_lines = [line for line in raw_evidence if len(line) > 20]
            evidence = "\n".join(evidence_lines)

            if len(evidence) > 4000:
                evidence = evidence[:4000] + "... [Truncated for Gemini API]"
            print(f"Successfully fetched evidence from result {start_index + 1}: {link}")
            print(f"Evidence token count (approx characters): {len(evidence)}")
            return link, evidence, results
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch result {start_index + 1} ({link}): {e}")
            return None, f"Failed to fetch evidence from {link}: {e}", results
    except requests.exceptions.RequestException as e:
        print(f"Error fetching search results: {e}")
        return None, f"Error fetching search results: {e}", None

# Main execution
if __name__ == "__main__":
    claim = """tamil is a language
    """
    print(f"Claim: {claim}")

    # Step 1: Check with Gemini's internal knowledge
    verdicts, final_verdict = verify_claim_with_gemini(claim)
    print(f"\nInitial verdicts: {[(v, f'{c:.2f}') for v, c in verdicts]}")
    print(f"Initial Verdict: {final_verdict}")

    # Step 2: If NEUTRAL or error, proceed to web search
    if final_verdict == "NEUTRAL":
        print("\nNEUTRAL verdict or error detected, proceeding to web search...")
        index = 0
        num_results = 5

        while index < num_results:
            link, evidence, results = get_web_evidence(claim, num_results=num_results, start_index=index)
            if link:
                print(f"\nEvidence from {link}:\n{evidence[:1000]}... [Truncated for display; full text used for Gemini API]")
                verdicts, final_verdict = verify_claim_with_gemini(claim, evidence)
                print(f"\nVerdicts from result {index + 1}: {[(v, f'{c:.2f}') for v, c in verdicts]}")
                print(f"Verdict from result {index + 1}: {final_verdict}")

                # Stop if True (ENTAILMENT) or False (CONTRADICTION)
                if final_verdict in ["ENTAILMENT", "CONTRADICTION"]:
                    break
            else:
                print(f"Failed to fetch evidence from result {index + 1}.")
            
            index += 1
            if index >= num_results or (results and index >= len(results["items"])):
                print("\nExhausted all search results.")
                break

    # Final conclusion
    if final_verdict == "ENTAILMENT":
        print("Conclusion: The claim is likely TRUE based on the evidence.")
    elif final_verdict == "CONTRADICTION":
        print("Conclusion: The claim is likely FALSE based on the evidence.")
    else:
        print("Conclusion: The claim is UNVERIFIED; evidence is inconclusive.")