from langchain_community.llms import Ollama
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.tools import DuckDuckGoSearchTool
from langchain.tools.render import format_tool_to_openai_function
import requests
from typing import List, Dict
from langchain_community.llms import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from langchain_community.llms import Ollama
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.tools import DuckDuckGoSearchTool
from langchain.tools.render import format_tool_to_openai_function
import requests
from typing import List, Dict

# Load model directly
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("openai-community/gpt2")
model = AutoModelForCausalLM.from_pretrained("openai-community/gpt2")

pipe = pipeline("text-generation", model="openai-community/gpt2")

class NetworkIncidentAgent:
    def __init__(self):
        self.llm = HuggingFacePipeline(pipeline=pipe)

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Define tools
        self.tools = [
            Tool(
                name="Search",
                func=DuckDuckGoSearchTool().run,
                description="Useful for searching current information about network issues, security vulnerabilities, and technical solutions"
            ),
            Tool(
                name="CVE_Search",
                func=self.search_cve,
                description="Search for CVE (Common Vulnerabilities and Exposures) information"
            ),
            Tool(
                name="Network_Diagnostic",
                func=self.analyze_network_issue,
                description="Analyze network-related issues and suggest solutions"
            )
        ]

        self.prompt = PromptTemplate.from_template("""
        You are an expert IT incident response agent. Your task is to analyze incidents and provide solutions.
        
        Given the incident:
        Title: {title}
        Description: {description}
        Severity: {severity}
        
        Use the available tools to:
        1. Understand the issue
        2. Search for similar problems and solutions
        3. Check if there are any related security vulnerabilities
        4. Provide a detailed response with:
           - Root cause analysis
           - Immediate steps to mitigate
           - Long-term recommendations
           - Related issues to watch for
        
        Tools available: {tools}
        
        Response should be clear and actionable.
        
        Question: What is the analysis and solution for this incident?
        
        {agent_scratchpad}
        """)

        # Create the agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )

    def search_cve(self, query: str) -> str:
        """Search for CVE information using the NVD API"""
        try:
            base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
            params = {
                "keywordSearch": query,
                "resultsPerPage": 5
            }
            response = requests.get(base_url, params=params)
            data = response.json()
            
            if 'vulnerabilities' in data:
                results = []
                for vuln in data['vulnerabilities'][:3]:  # Get top 3 results
                    cve = vuln['cve']
                    results.append({
                        'id': cve['id'],
                        'description': cve['descriptions'][0]['value'],
                        'severity': cve.get('metrics', {}).get('cvssMetricV31', [{}])[0].get('cvssData', {}).get('baseScore', 'N/A')
                    })
                return str(results)
            return "No CVE information found"
        except Exception as e:
            return f"Error searching CVE: {str(e)}"

    def analyze_network_issue(self, description: str) -> str:
        # Use the LLM to analyze network issues
        analysis_prompt = f"""
        Analyze this network issue and provide technical diagnosis:
        {description}
        
        Consider:
        1. Common network problems (DNS, routing, firewall, etc.)
        2. Performance metrics
        3. Infrastructure components
        4. Potential bottlenecks
        
        Provide a technical analysis with specific recommendations.
        """
        
        return self.llm.predict(analysis_prompt)

    async def get_solutions(self, title: str, description: str, severity: str) -> Dict:
        try:
            response = await self.agent_executor.ainvoke({
                "title": title,
                "description": description,
                "severity": severity
            })
            
            # Structure the response
            return {
                "analysis": response['output'],
                "confidence_score": self._calculate_confidence(response),
                "suggested_actions": self._extract_actions(response['output']),
                "references": self._extract_references(response)
            }
        except Exception as e:
            return {
                "analysis": f"Error generating solution: {str(e)}",
                "confidence_score": 0,
                "suggested_actions": [],
                "references": []
            }

    def _calculate_confidence(self, response: Dict) -> float:
        score = 0.5  # Base score
        
        if 'intermediate_steps' in response:
            tools_used = len(response['intermediate_steps'])
            score += min(0.3, tools_used * 0.1)  # Up to 0.3 for tool usage
            
            # Check if CVE information was found
            if any('CVE-' in str(step) for step in response['intermediate_steps']):
                score += 0.1
                
            # Check if network analysis was performed
            if any('Network_Diagnostic' in str(step) for step in response['intermediate_steps']):
                score += 0.1
                
        return min(1.0, score)

    def _extract_actions(self, output: str) -> List[str]:
        """Extract suggested actions from the response"""
        # Use the LLM to extract and structure the actions
        prompt = f"""
        Extract the specific actions suggested in this response:
        {output}
        
        Return only the list of actions, one per line.
        """
        
        actions_text = self.llm.predict(prompt)
        return [action.strip() for action in actions_text.split('\n') if action.strip()]

    def _extract_references(self, response: Dict) -> List[Dict]:
        """Extract references and sources from the response"""
        references = []
        
        if 'intermediate_steps' in response:
            for step in response['intermediate_steps']:
                if isinstance(step[1], str) and ('http' in step[1] or 'CVE-' in step[1]):
                    references.append({
                        'type': 'link' if 'http' in step[1] else 'cve',
                        'reference': step[1]
                    })
        
        return references