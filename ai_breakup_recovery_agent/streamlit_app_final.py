from agno.agent import Agent
from agno.models.groq import Groq
from agno.media import Image as AgnoImage
import streamlit as st
from typing import List, Optional
import logging
from pathlib import Path
import tempfile
import os
import random
import time

# Configure logging for errors only
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Set page config and UI elements
st.set_page_config(
    page_title="Your Breakup Recovery",
    page_icon="💔",
    layout="wide"
)

if 'agents_initialized' not in st.session_state:
    st.session_state.agents_initialized = False
    st.session_state.therapist_agent = None
    st.session_state.closure_agent = None
    st.session_state.routine_planner_agent = None
    st.session_state.brutal_honesty_agent = None
    st.session_state.api_key_input = None

# For LOCAL development: Load from .streamlit/secrets.toml
# For DEPLOYED app: Load from Streamlit Cloud secrets
def get_api_keys():
    try:
        """Get API keys from secrets (works both locally and in cloud)"""
        groq_key = st.secrets["GROQ_API_KEY"]
        return groq_key
    except:
        # Fallback to environment variables for local testing
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            return groq_key
        return None

def initialize_agents(api_key: str) -> tuple[Agent, Agent, Agent, Agent]:
    try:
        groq_model = Groq(
            id="llama-3.3-70b-versatile",  # Best for general conversation
            api_key=groq_key  # Pass your Groq API key
        )

        time.sleep(1)
        
        st.session_state.groq_model = groq_model
        
        therapist_agent = Agent(
            model=groq_model,
            name="Therapist Agent",
            instructions=[
                "You are an empathetic therapist that:",
                "1. Listens with empathy and validates feelings",
                "2. Uses gentle humor to lighten the mood",
                "3. Shares relatable breakup experiences",
                "4. Offers comforting words and encouragement",
                "5. Analyzes both text and image inputs for emotional context",
                "Be supportive and understanding in your responses"
            ],
            markdown=True
        )

        time.sleep(1)


        closure_agent = Agent(
            model=groq_model,
            name="Closure Agent",
            instructions=[
                "You are a closure specialist that:",
                "1. Creates emotional messages for unsent feelings",
                "2. Helps express raw, honest emotions",
                "3. Formats messages clearly with headers",
                "4. Ensures tone is heartfelt and authentic",
                "Focus on emotional release and closure"
            ],
            markdown=True

        )
        time.sleep(1)


        routine_planner_agent = Agent(
            model=groq_model,
            name="Routine Planner Agent",
            instructions=[
                "You are a recovery routine planner that:",
                "1. Designs 7-day recovery challenges",
                "2. Includes fun activities and self-care tasks",
                "3. Suggests social media detox strategies",
                "4. Creates empowering playlists",
                "Focus on practical recovery steps"
            ],
            markdown=True
        )
        time.sleep(1)


        brutal_honesty_agent = Agent(
            model=groq_model,
            name="Brutal Honesty Agent",
            instructions=[
                "You are a direct feedback specialist that:",
                "1. Gives raw, objective feedback about breakups",
                "2. Explains relationship failures clearly",
                "3. Uses blunt, factual language",
                "4. Provides reasons to move forward",
                "Focus on honest insights without sugar-coating"
            ],
            markdown=True
        )
        time.sleep(1)

        if not all([therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent]):
            raise Exception("One or more agents failed to initialize")
     
        return therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent
    except Exception as e:
        st.error(f"Error initializing agents: {str(e)}")
        return None, None, None, None

def call_with_rate_limit(agent, prompt, images=None, max_retries=3):
    """Call an agent with exponential backoff retry logic"""
    for attempt in range(max_retries):
        try:
            # Add jitter to avoid synchronized retries
            time.sleep(random.uniform(0.5, 1.5))
            
            response = agent.run(prompt, images=images)
            return response
            
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                # Rate limit hit - wait exponentially longer
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                st.warning(f"Rate limit hit, waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
            else:
                raise e



# Sidebar for API key input
with st.sidebar:
    st.header("🔑 API Configuration")


    # Option 1: Use keys from secrets (pre-configured)
    use_default_keys = st.checkbox("Use app's default API keys (recommended)", value=False)

    if use_default_keys:
        groq_key = get_api_keys()
        if not groq_key:
            st.error("App not configured with default keys. Please contact admin.")
            st.stop()
    else:
        # Option 2: Users bring their own keys
        groq_key = st.text_input("Groq API Key:", type="password")

   
    if groq_key:
        st.session_state.groq_key = groq_key
        st.success("✅ API key set! Ready to use.")
    

    if use_default_keys:
        st.session_state.active_groq_key = groq_key
    else:
        st.session_state.active_groq_key = groq_key
    
        
    st.markdown("---")
    
    # Feature status
    st.subheader("📱 Features")
    st.markdown("""
    ✅ **Available now:**
    - 🤗 Emotional support 
    - 💌 Closure messages
    - 📅 Recovery planning
    - 💪 Honest feedback
    
    🚀 **Coming soon:**
    - 📸 Screenshot analysis
    - 🎵 Music recommendations
    - 📞 Crisis resource links
    """)
    
    st.markdown("---")
    
    # About section
    st.markdown("**About this app**")
    st.markdown("""
    Four AI agents work together to support you through difficult times.  
    Built with Groq's lightning-fast Llama 3.3 model.
    """)


if st.session_state.get('active_groq_key') and not st.session_state.get('agents_initialized', False):
    try:
        with st.spinner("🔄 Initializing AI agents with Groq..."):
            therapist, closure, routine, brutal = initialize_agents(st.session_state.active_groq_key)
            
            if all([therapist, closure, routine, brutal]):
                st.session_state.therapist_agent = therapist
                st.session_state.closure_agent = closure
                st.session_state.routine_planner_agent = routine
                st.session_state.brutal_honesty_agent = brutal
                st.session_state.agents_initialized = True
                success_msg = st.success("✅ Agents ready with Groq! (Free tier: 1000 requests/day)")
                st.balloons()
                
                time.sleep(2)
                success_msg.empty()
                st.rerun()



                
    except Exception as e:
        st.error(f"Failed to initialize agents: {e}")
        st.session_state.agents_initialized = False    

# Main content
st.title("💔 Breakup Recovery")
st.markdown("""
    ### Your AI-powered breakup recovery agent is here to help!
    Share your feelings ~~and chat screenshots~~ **(coming soon)**, and we'll help you navigate through this tough time.
""")

# User Input section
col1, col2 = st.columns(2)

with col1:
    st.subheader("Share Your Feelings")
    user_input = st.text_area(
        "How are you feeling? What happened?",
        height=150,
        placeholder="Tell us your story..."
    )
    
with col2:
    st.subheader("Upload Chat Screenshots")
    uploaded_files = st.file_uploader(
        "Upload screenshots of your chats (optional)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key="screenshots"
    )
    
    if uploaded_files:
        for file in uploaded_files:
            st.image(file, caption=file.name, use_container_width=True)

# Process button and API key check
if st.button("Start your Healing", type="primary"):
    if not st.session_state.get('agents_initialized', False):
        st.warning("Agents not ready yet. Please wait for initialization in the sidebar.")
    else:
        therapist_agent = st.session_state.therapist_agent
        closure_agent = st.session_state.closure_agent
        routine_planner_agent = st.session_state.routine_planner_agent
        brutal_honesty_agent = st.session_state.brutal_honesty_agent
        
        if all([therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent]):
            if user_input or uploaded_files:
                try:
                    st.header("Your Personalized Recovery Plan")
                    
                    def process_images(files):
                        processed_images = []
                        for file in files:
                            try:
                                temp_dir = tempfile.gettempdir()
                                temp_path = os.path.join(temp_dir, f"temp_{file.name}")
                                
                                with open(temp_path, "wb") as f:
                                    f.write(file.getvalue())
                                
                                agno_image = AgnoImage(filepath=Path(temp_path))
                                processed_images.append(agno_image)
                                
                            except Exception as e:
                                logger.error(f"Error processing image {file.name}: {str(e)}")
                                continue
                        return processed_images
                    
                    all_images = process_images(uploaded_files) if uploaded_files else []
                    
                    # Therapist Analysis
                    with st.spinner("🤗 Getting empathetic support..."):
                        therapist_prompt = f"""
                        Analyze the emotional state and provide empathetic support based on:
                        User's message: {user_input}
                        
                        Please provide a compassionate response with:
                        1. Validation of feelings
                        2. Gentle words of comfort
                        3. Relatable experiences
                        4. Words of encouragement
                        """
                        time.sleep(1)
                        response = call_with_rate_limit(
                            therapist_agent,
                            therapist_prompt,
                            images=all_images
                        )
                        
                        st.subheader("🤗 Emotional Support")
                        st.markdown(response.content)

                        time.sleep(2) 
                    
                    # Closure Messages
                    with st.spinner("✍️ Crafting closure messages..."):
                        closure_prompt = f"""
                        Help create emotional closure based on:
                        User's feelings: {user_input}
                        
                        Please provide:
                        1. Template for unsent messages
                        2. Emotional release exercises
                        3. Closure rituals
                        4. Moving forward strategies
                        """
                        time.sleep(1)
                        
                        response = call_with_rate_limit(
                            closure_agent,
                            closure_prompt,
                            images=all_images
                        )
                        
                        st.subheader("✍️ Finding Closure")
                        st.markdown(response.content)

                        time.sleep(2) 
                    
                    # Recovery Plan
                    with st.spinner("📅 Creating your recovery plan..."):
                        routine_prompt = f"""
                        Design a 7-day recovery plan based on:
                        Current state: {user_input}
                        
                        Include:
                        1. Daily activities and challenges
                        2. Self-care routines
                        3. Social media guidelines
                        4. Mood-lifting music suggestions
                        """
                        time.sleep(1)
                        
                        response = call_with_rate_limit(
                            routine_planner_agent,
                            routine_prompt,
                            images=all_images
                        )
                        
                        st.subheader("📅 Your Recovery Plan")
                        st.markdown(response.content)

                        time.sleep(2) 
                    
                    # Honest Feedback
                    with st.spinner("💪 Getting honest perspective..."):
                        honesty_prompt = f"""
                        Provide honest, constructive feedback about:
                        Situation: {user_input}
                        
                        Include:
                        1. Objective analysis
                        2. Growth opportunities
                        3. Future outlook
                        4. Actionable steps
                        """
                        time.sleep(1)
                        response = call_with_rate_limit(
                            brutal_honesty_agent,
                            honesty_prompt,
                            images=all_images
                        )
                        
                        st.subheader("💪 Honest Perspective")
                        st.markdown(response.content)

                        time.sleep(2) 
                            
                except Exception as e:
                    logger.error(f"Error during analysis: {str(e)}")
                    st.error("An error occurred during analysis. Please check the logs for details.")
            else:
                st.warning("Please share your feelings or upload screenshots to get help.")
        else:
            st.error("Failed to initialize agents. Please check your API key.")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Made with ❤️ by <i> <a href=https://github.com/AchiugoTrust>Trust</a> </i></p>
    </div>
""", unsafe_allow_html=True)