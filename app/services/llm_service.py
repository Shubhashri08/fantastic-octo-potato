import json
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from app.config import settings

logger = logging.getLogger(__name__)

# Pydantic schema for structured intent response from Gemini
class ExtractedIntent(BaseModel):
    operation: str = Field(
        ..., 
        description="The identified operation. Must be exactly one of: "
                    "GET_ENTITY_HISTORY, GET_EVENT_TIMELINE, GET_NEARBY_INCIDENTS, "
                    "GET_EVENT_ENTITIES, GET_CAMERA_HISTORY, GET_HISTORICAL_PATTERN, "
                    "GET_LOCATION_CONTEXT"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value arguments extracted for the operation. E.g.: "
                    "entity_id, event_id, camera_id, latitude, longitude, radius_meters. "
                    "All keys must match these parameter names."
    )

class LlmService:
    def __init__(self):
        # Initialize Gemini Client using google-genai SDK
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        
        # If API key is a mock key, we don't initialize the real client to avoid startup errors
        if self.api_key and self.api_key != "mock_key_for_testing":
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    async def extract_intent(self, user_question: str) -> ExtractedIntent:
        """
        Calls Gemini to parse the user's natural language request into a structured intent operation.
        """
        # If we are in test mode or client is not initialized, return a default mock/fallback to be overridden in tests
        if not self.client:
            logger.warning("LLM client not initialized (mock key detected). Returning empty intent.")
            return ExtractedIntent(operation="GET_ENTITY_HISTORY", parameters={"entity_id": "mock_entity"})

        prompt = f"""
        Analyze the following user security/incident query and extract the structured intent.
        
        You MUST select exactly one operation from these allowed operations:
        - GET_ENTITY_HISTORY: used when searching for where a vehicle, person, or object went, or its movements. (Expected param: entity_id)
        - GET_EVENT_TIMELINE: used when querying history/details of a specific event ID. (Expected param: event_id)
        - GET_NEARBY_INCIDENTS: used when searching for incidents close to a coordinate point within a radius. (Expected params: latitude, longitude, radius_meters)
        - GET_EVENT_ENTITIES: used when retrieving entities associated with a specific event ID. (Expected param: event_id)
        - GET_CAMERA_HISTORY: used when viewing what a camera recorded. (Expected param: camera_id)
        - GET_HISTORICAL_PATTERN: used when querying patterns or risk history for coordinates. (Expected params: latitude, longitude)
        - GET_LOCATION_CONTEXT: used when viewing GIS context or hotspot details of a location. (Expected params: latitude, longitude)

        Return the parsed JSON conforming to the requested schema.

        User Question: "{user_question}"
        """

        try:
            # We run in a thread executor or synchronous call, google-genai is synchronous
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExtractedIntent,
                    temperature=0.0
                )
            )
            
            # The returned text is expected to be valid JSON matching ExtractedIntent schema
            result_json = json.loads(response.text)
            return ExtractedIntent.model_validate(result_json)
        except Exception as e:
            logger.error(f"Gemini intent extraction failed: {str(e)}")
            # Raise exception so caller handles it
            raise RuntimeError(f"Gemini intent extraction failed: {str(e)}")

    async def generate_answer(self, user_question: str, verified_data: Dict[str, Any]) -> str:
        """
        Feeds the user question and the verified upstream query snapshot back to Gemini to synthesize
        a clean, user-friendly, evidence-based Markdown response.
        """
        if not self.client:
            logger.warning("LLM client not initialized (mock key detected). Returning static mock response.")
            return f"Mock answer for: '{user_question}' using data: {json.dumps(verified_data)}"

        prompt = f"""
        You are the VIGRAH AI Investigation Assistant.
        You are answering a user question based STRICTLY on the verified real-time database snapshot provided below.
        
        Guidelines:
        1. Rely ONLY on the provided verified data. Do not make assumptions or invent details.
        2. If the data is empty, state clearly that no records were found.
        3. Format your response in clean markdown.
        
        User Question: "{user_question}"
        
        Verified Upstream Data Snapshot:
        {json.dumps(verified_data, indent=2, default=str)}
        """

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini answer generation failed: {str(e)}")
            raise RuntimeError(f"Gemini answer generation failed: {str(e)}")
