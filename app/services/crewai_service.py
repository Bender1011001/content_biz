# app/services/crewai_service.py

import logging
import os
import spacy
import asyncio
from crewai import Agent, Task, Crew, Process
from sqlalchemy.orm import Session

# Project specific imports
from app.services.crew_service import ContentCrewService
from app.services.delivery_service import send_content_email
from app.db.database import get_db_context # Using context manager for session safety
from app.db.models import Brief, Content

logger = logging.getLogger(__name__)

# --- Configuration & Initialization ---
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.error("Spacy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm'")
    # Depending on requirements, might want to raise an error or exit
    nlp = None # Set to None to handle gracefully later if needed

QUALITY_THRESHOLD = float(os.getenv("QUALITY_THRESHOLD", 0.85)) # Ensure it's matching the default in config.py (0-1 scale vs 0-100)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") # Needed for ContentCrewService

# --- CrewAI Tools ---

def get_brief_data(brief_id: str) -> dict | None:
    """Fetches brief data from the database using the brief ID."""
    logger.info(f"Tool: Fetching brief data for ID: {brief_id}")
    try:
        with get_db_context() as db:
            brief = db.query(Brief).filter(Brief.id == brief_id).first()
            if brief:
                # Convert to dict, handling relationships if necessary
                brief_dict = {c.name: getattr(brief, c.name) for c in brief.__table__.columns}
                logger.info(f"Tool: Found brief data for {brief_id}")
                return brief_dict
            else:
                logger.warning(f"Tool: Brief not found for ID: {brief_id}")
                return None
    except Exception as e:
        logger.error(f"Tool: Error fetching brief {brief_id}: {e}")
        return None

def get_content_text(content_id: str) -> str | None:
    """Fetches the generated text of a specific content record."""
    logger.info(f"Tool: Fetching content text for ID: {content_id}")
    try:
        with get_db_context() as db:
            content = db.query(Content).filter(Content.id == content_id).first()
            if content:
                logger.info(f"Tool: Found content text for {content_id}")
                return content.generated_text
            else:
                logger.warning(f"Tool: Content not found for ID: {content_id}")
                return None
    except Exception as e:
        logger.error(f"Tool: Error fetching content text {content_id}: {e}")
        return None

class ContentGenerationTool:
    """Wrapper tool for ContentCrewService."""
    def __init__(self):
        # Pass API key if needed by the service constructor
        self.service = ContentCrewService(api_key=OPENROUTER_API_KEY)

    def generate(self, brief_data: dict) -> str | None:
        """Runs the content generation crew and saves to DB, returning the content ID."""
        logger.info(f"Tool: Generating content for brief topic: {brief_data.get('topic')}")
        try:
            # Update service's brief data before running
            self.service.brief_data = brief_data
            self.service.brief_id = brief_data.get('id') # Ensure brief_id is set for saving
            content_id = self.service.run_crew(save_to_db=True) # Returns content_id
            if content_id:
                logger.info(f"Tool: Content generated and saved with ID: {content_id}")
                return content_id
            else:
                logger.error("Tool: Content generation failed or did not return ID.")
                return None
        except Exception as e:
            logger.error(f"Tool: Error during content generation: {e}")
            return None

# Instantiate the generation tool once
content_generation_tool = ContentGenerationTool()

def check_content_quality(content_text: str) -> bool:
    """Checks the coherence quality of the generated text using spaCy."""
    if not nlp:
        logger.warning("Tool: spaCy model not loaded, skipping quality check.")
        return True # Assume good quality if model isn't available

    logger.info("Tool: Checking content quality...")
    try:
        doc = nlp(content_text)
        sentences = list(doc.sents)
        if len(sentences) <= 1:
            logger.info("Tool: Quality check skipped (<= 1 sentence).")
            return True # Cannot compare similarity

        similarities = [
            nlp(s1.text).similarity(nlp(s2.text))
            for s1, s2 in zip(sentences[:-1], sentences[1:])
        ]
        # Calculate raw similarity score (0-1 scale)
        score = sum(similarities) / len(similarities) if similarities else 1.0 
        # Compare directly with QUALITY_THRESHOLD (also on 0-1 scale)
        is_good_quality = score >= QUALITY_THRESHOLD
        logger.info(f"Tool: Quality score: {score:.2f} (Threshold: {QUALITY_THRESHOLD}). Pass: {is_good_quality}")
        return is_good_quality
    except Exception as e:
        logger.error(f"Tool: Error during quality check: {e}")
        return False # Assume poor quality on error

def email_content_to_client(client_email: str, content_text: str) -> bool:
    """Uses the delivery service to email the content."""
    logger.info(f"Tool: Attempting to email content to {client_email}")
    try:
        success = send_content_email(email=client_email, content_text=content_text)
        if success:
            logger.info(f"Tool: Email successfully sent to {client_email}")
        else:
            logger.warning(f"Tool: Email sending failed for {client_email}")
        return success
    except Exception as e:
        logger.error(f"Tool: Error calling send_content_email: {e}")
        return False

# --- CrewAI Agents ---

# Create tool objects compatible with CrewAI 0.108.0
# Convert functions to proper tool format
from crewai import Tool

brief_data_tool = Tool(
    name="GetBriefData",
    description="Fetch and validate the client brief data using the provided brief ID.",
    func=get_brief_data
)

brief_processor = Agent(
    role="Brief Processor",
    goal="Fetch and validate the client brief data using the provided brief ID.",
    backstory="You are an efficient administrator responsible for retrieving and preparing client request details.",
    tools=[brief_data_tool],
    verbose=True,
    allow_delegation=False
)

# Convert the content generation tool
content_generation_tool_obj = Tool(
    name="GenerateContent",
    description="Generate high-quality written content based on the client's brief specifications and save it to the database.",
    func=content_generation_tool.generate
)

# Convert the get_content_text function
content_text_tool = Tool(
    name="GetContentText",
    description="Fetch the generated text of a specific content record using its ID.",
    func=get_content_text
)

# Convert the email_content_to_client function
email_tool = Tool(
    name="EmailContentToClient",
    description="Email the generated content to the client using their email address.",
    func=email_content_to_client
)

content_generator = Agent(
    role="Content Generator",
    goal="Generate high-quality written content based on the client's brief specifications. Return the ID of the generated content.",
    backstory="You are a skilled AI writing assistant, capable of creating engaging content tailored to specific needs.",
    tools=[content_generation_tool_obj],
    verbose=True,
    allow_delegation=False
)

delivery_agent = Agent(
    role="Content Delivery Specialist",
    goal="Retrieve the generated content using its ID, fetch the client's email using the brief ID, and email the content to the client.",
    backstory="You are responsible for the final step: ensuring the client receives their requested content promptly.",
    tools=[brief_data_tool, content_text_tool, email_tool],
    verbose=True,
    allow_delegation=False # Keep it simple for now
)

# --- CrewAI Tasks ---

# Task 1: Process the Brief
task_process_brief = Task(
    description=(
        "Fetch the complete brief data for the brief with ID: '{brief_id}'. "
        "Ensure all necessary details like topic, tone, and client email are retrieved."
    ),
    expected_output="A dictionary containing the full brief data.",
    agent=brief_processor
)

# Task 2: Generate Content
task_generate_content = Task(
    description=(
        "Using the brief data provided in the context, generate the required content. "
        "Save the content to the database and return the unique content ID."
    ),
    expected_output="The unique ID (string) of the newly generated content record.",
    agent=content_generator,
    context=[task_process_brief] # Depends on brief data from task 1
)

# Task 3: Deliver Content
task_deliver_content = Task(
    description=(
        "1. Retrieve the generated content text using the content ID from the previous task. "
        "2. Retrieve the client's email address using the brief ID '{brief_id}'. "
        "3. Email the retrieved content text to the client's email address."
    ),
    expected_output="Confirmation that the email has been sent successfully (True or False).",
    agent=delivery_agent,
    context=[task_process_brief, task_generate_content] # Depends on brief_id and content_id
)


# --- Main Orchestration Function ---

async def run_content_crew(brief_id: str):
    """
    Runs the full CrewAI workflow for a given brief ID.
    Includes post-crew quality check and DB update.
    """
    logger.info(f"Starting CrewAI workflow for brief_id: {brief_id}")

    # Define the crew
    content_crew = Crew(
        agents=[brief_processor, content_generator, delivery_agent],
        tasks=[task_process_brief, task_generate_content, task_deliver_content],
        process=Process.sequential,
        verbose=2 # Log crew activity
    )

    # Input data for the first task
    inputs = {'brief_id': brief_id}

    try:
        # Kick off the crew
        # Running kickoff in a separate thread to avoid blocking asyncio event loop
        # Note: CrewAI's kickoff might be blocking depending on its implementation
        loop = asyncio.get_running_loop()
        crew_result = await loop.run_in_executor(None, content_crew.kickoff, inputs)
        # If kickoff is async, use: crew_result = await content_crew.kickoff_async(inputs=inputs)

        logger.info(f"Crew finished for brief_id: {brief_id}. Result: {crew_result}")

        # --- Post-Crew Quality Check & DB Update ---
        logger.info(f"Performing post-crew quality check for brief_id: {brief_id}")
        content_record = None
        try:
            with get_db_context() as db:
                # Fetch the *latest* content associated with the brief
                content_record = db.query(Content)\
                                   .filter(Content.brief_id == brief_id)\
                                   .order_by(Content.created_at.desc())\
                                   .first()

                if content_record and content_record.generated_text:
                    is_good = check_content_quality(content_record.generated_text)
                    if not is_good:
                        logger.warning(f"Content {content_record.id} failed quality check. Marking for review.")
                        content_record.needs_review = True
                        db.commit()
                        logger.info(f"Content {content_record.id} marked needs_review=True.")
                    else:
                         # Explicitly mark as not needing review if it passes (optional, depends on default)
                         if content_record.needs_review: # Only update if it was True before
                             content_record.needs_review = False
                             db.commit()
                             logger.info(f"Content {content_record.id} passed quality check. Marked needs_review=False.")

                elif not content_record:
                    logger.error(f"Could not find content record for brief {brief_id} after crew run.")
                else:
                     logger.warning(f"Content record {content_record.id} has no text for quality check.")

        except Exception as db_error:
            logger.error(f"Error during post-crew DB update/quality check for brief {brief_id}: {db_error}")
            # Decide if this should affect the overall result

        return {"status": "success", "crew_output": crew_result, "brief_id": brief_id}

    except Exception as e:
        logger.error(f"CrewAI workflow failed for brief_id: {brief_id}. Error: {e}")
        # Capture traceback for better debugging if possible
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e), "brief_id": brief_id}
