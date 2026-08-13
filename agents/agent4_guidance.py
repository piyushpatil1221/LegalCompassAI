import os
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from groq import Groq

class GuidanceAgent:
    def __init__(self, bail_model_path="./models/bail_model/"):
        self.bail_model_path = bail_model_path
        self.tokenizer = None
        self.model = None
        self.groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
        
        self._load_bail_model()

    def _load_bail_model(self):
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.bail_model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.bail_model_path)
            self.model.eval()
            print("Guidance Agent: Bail model loaded successfully.")
        except Exception as e:
            print(f"Guidance Agent: Error loading bail model: {e}")

    def predict_bail_outcome(self, case_facts: str):
        if not self.model or not self.tokenizer:
            return None, 0.0

        inputs = self.tokenizer(case_facts, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=-1)
        pred_id = torch.argmax(probs, dim=-1).item()
        
        confidence = probs[0][pred_id].item()
        label = self.model.config.id2label.get(pred_id, str(pred_id))
        
        return label, confidence

    def generate_explanation(self, case_representation):
        raw_input = case_representation.get("raw_user_input", "")
        crimes = case_representation.get("crime_types", [])
        role = case_representation.get("role", "")
        statutes = case_representation.get("retrieved_statutes", [])
        precedents = case_representation.get("retrieved_precedents", [])
        
        crime_list = ", ".join([c["crime"] for c in crimes])
        
        # Build prompt
        prompt = f"The user is a {role} involved in a situation relating to {crime_list}.\n"
        prompt += f"Their situation: {raw_input}\n\n"
        
        prompt += "Relevant General Law / Statutes:\n"
        for s in statutes:
            prompt += f"- {s}\n"
            
        prompt += "\nRelevant Similar Past Cases (Precedent):\n"
        for p in precedents:
            prompt += f"- Case: {p['case_name']} (Outcome: {p['outcome']})\n  Facts: {p['facts_summary']}\n"
            
        prompt += """\nBased on the above, provide:
1. A clear, plain-language legal explanation of their situation and the relevant statutes.
   - **CRITICAL INSTRUCTION:** The Indian Penal Code (IPC) and Code of Criminal Procedure (CrPC) were REPEALED in July 2024. You MUST translate and map any IPC references to the new Bhartiya Nyaya Sanhita (BNS) and any CrPC references to the Bhartiya Nagarik Suraksha Sanhita (BNSS). If the user specifically asks about the IPC, correct them gently and provide the new BNS equivalent. NEVER advise the user using the repealed IPC or CrPC.
2. A distinct section titled "Similar Past Cases" where you explicitly describe the retrieved past cases, their outcomes, and how they relate to the user's situation. STRICT RULE: Ground any statement about these past cases strictly in the retrieved text. Do not invent outcomes or reasoning.
"""

        try:
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating explanation: {e}"

    def process_case(self, case_representation: dict):
        explanation = self.generate_explanation(case_representation)
        
        prediction = None
        confidence = None
        
        role = case_representation.get("role", "")
        if role == "accused":
            prediction, confidence = self.predict_bail_outcome(case_representation.get("raw_user_input", ""))
        
        return {
            "explanation": explanation,
            "bail_prediction": prediction,
            "bail_confidence": confidence
        }
