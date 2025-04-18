from langchain_community.llms import HuggingFacePipeline
from langchain_community.embeddings import HuggingFaceEmbeddings
from transformers import pipeline
from typing import List, Dict
import requests

# --- Tool Definitions ---

class WebSearchTool:
    def run(self, query: str) -> str:
        return f"Search results for '{query}':\n- Check network configurations\n- Verify firewall settings\n- Test connectivity with ping"

class NetworkIncidentAgent:
    def __init__(self):
        # Load a simple model
        self.llm = HuggingFacePipeline(pipeline=pipeline(
            "text-generation",
            model="openai-community/gpt2",
            max_new_tokens=200,
            temperature=0.7
        ))

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )

        # Tool instances
        self.tools = {
            "Search": WebSearchTool().run,
            "CVE_Search": self.search_cve,
            "Network_Diagnostic": self.analyze_network_issue
        }

    def search_cve(self, query: str) -> str:
        return f"CVE results for '{query}':\n- CVE-2023-1234: Network buffer overflow\n- CVE-2023-5678: Denial of service vulnerability"

    def analyze_network_issue(self, description: str) -> str:
        prompt = f"""
        Analyze this network issue and provide technical diagnosis:
        {description}
        Consider: DNS, routing, firewalls, performance, and bottlenecks.
        """
        return self.llm.predict(prompt)

    def get_solutions(self, title: str, description: str, severity: str) -> Dict:
        # --- PLAN ---
        plan = [
            {"tool": "Search", "input": title},
            {"tool": "CVE_Search", "input": description},
            {"tool": "Network_Diagnostic", "input": description}
        ]

        intermediate_steps = []
        for step in plan:
            tool_name = step["tool"]
            tool_input = step["input"]
            try:
                output = self.tools[tool_name](tool_input)
                intermediate_steps.append((tool_name, output))
            except Exception as e:
                intermediate_steps.append((tool_name, f"Error: {str(e)}"))

        # --- EXECUTE ---
        final_prompt = f"""
Given the incident:
Title: {title}
Description: {description}
Severity: {severity}

Search Info:
{intermediate_steps[0][1]}

CVE Info:
{intermediate_steps[1][1]}

Diagnostic:
{intermediate_steps[2][1]}

Now write:
- Root cause analysis
- Immediate steps to mitigate
- Long-term recommendations
- Related issues to monitor
"""
        final_answer = self.llm.predict(final_prompt)

        return {
            "analysis": final_answer.strip(),
            "confidence_score": self._calculate_confidence(intermediate_steps),
            "suggested_actions": self._extract_actions(final_answer),
            "references": self._extract_references(intermediate_steps)
        }

    def _calculate_confidence(self, steps: List) -> float:
        score = 0.5 + min(0.3, len(steps) * 0.1)
        if any('CVE-' in str(step[1]) for step in steps):
            score += 0.1
        if any('DNS' in str(step[1]) or 'routing' in str(step[1]) for step in steps):
            score += 0.1
        return min(1.0, score)

    def _extract_actions(self, output: str) -> List[str]:
        return [
            "Check firewall configurations",
            "Verify network connectivity",
            "Test DNS resolution",
            "Restart affected services"
        ]

    def _extract_references(self, steps: List) -> List[Dict]:
        refs = []
        for tool_name, output in steps:
            if 'http' in output or 'CVE-' in output:
                refs.append({
                    'type': 'link' if 'http' in output else 'cve',
                    'reference': output
                })
        return refs
