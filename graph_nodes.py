import json 
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional, Union, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END, START
from langchain_openai import AzureChatOpenAI


from graph_state import ( BaseModel, ProductAnalysisState,
    MarketingWorkFlowState, IntentAnalysisState,
    PlatformContentData, PlatformAnalysisResult, InfluencerProfile, ProductTags, MatchResult, GeneratedEmail
)
from prompts import (
    social_media_analyst_Prompt, product_metadata_Prompt, influencer_analysis_Prompt,
    influencer_match_Prompt, collab_email_Prompt, email_intent_Prompt
)

load_dotenv()

# %%
# 设置 Azure OpenAI 服务凭据
api_key = os.getenv("AZURE_API_KEY")
api_version = os.getenv("AZURE_API_VERSION")
azure_endpoint = os.getenv("AZURE_API_BASE")
deployment_name = os.getenv("AZURE_COMPLETION_DEPLOYMENT")

# 初始化 Azure OpenAI 客户端
llm = AzureChatOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=azure_endpoint,
    deployment_name=deployment_name
)


def analyze_product_node(state: ProductAnalysisState) -> dict:
    print("LG Node: Analyzing product info...")
    product_info_original = state.product_info # This could be a Pydantic model or a dict
    current_errors = state.error_message or [] # Ensure current_errors is a list

    if not product_info_original:
        error_msg = "Product analysis error: product_info is missing in state."
        print(f"LG Node: {error_msg}")
        return {"product_tags": None, "error_messages": current_errors + [error_msg]}

    # --- START: Convert product_info_original to a fully serializable dictionary ---
    serializable_product_info_dict: dict
    try:
        if isinstance(product_info_original, BaseModel):
            # If product_info_original is a Pydantic model instance
            print("LG Node: product_info_original is Pydantic model. Converting with model_dump(mode='json').")
            serializable_product_info_dict = product_info_original.model_dump(mode='json')
        elif isinstance(product_info_original, dict):
            # If it's already a dict, ensure any nested complex types are handled
            # by cycling through json.dumps with default=str and then json.loads.
            # This converts HttpUrl to its string form if default=str is used.
            print("LG Node: product_info_original is dict. Ensuring deep serializability.")
            temp_json_str = json.dumps(product_info_original, default=str, ensure_ascii=False)
            serializable_product_info_dict = json.loads(temp_json_str)
            print("LG Node: product_info_original dict successfully made fully serializable.")
        else:
            error_msg = (
                f"Product analysis error: product_info_original is of unexpected type "
                f"{type(product_info_original)}. Expected Pydantic model or dict."
            )
            print(f"LG Node: {error_msg}")
            return {"product_tags": None, "error_messages": current_errors + [error_msg]}
    except Exception as e:
        import traceback
        error_msg = f"Product analysis error: Failed to convert product_info_original to serializable dict: {e}\n{traceback.format_exc()}"
        print(f"LG Node: {error_msg}")
        return {"product_tags": None, "error_messages": current_errors + [error_msg]}
    # --- END: Conversion ---

    # Now, create the JSON string payload for the LLM prompt from the fully serializable dictionary
    try:
        product_data_json_for_llm = json.dumps(serializable_product_info_dict, ensure_ascii=False)
        print(f"LG Node: Successfully created JSON string for LLM: {product_data_json_for_llm[:200]}...") # Log snippet
    except TypeError as e: # This should ideally not happen if the above conversion is correct
        import traceback
        error_msg = f"Product analysis error: Failed to json.dumps serializable_product_info_dict: {e}\n{traceback.format_exc()}"
        print(f"LG Node: {error_msg}")
        return {"product_tags": None, "error_messages": current_errors + [error_msg]}


    # --- LLM Chain Invocation ---
    prompt = ChatPromptTemplate.from_template(product_metadata_Prompt)
    # Ensure 'llm' and 'ProductTags' are correctly defined and available
    chain = prompt | llm | JsonOutputParser(pydantic_object=ProductTags)

    try:
        # The prompt expects product_data_json
        parsed_tags: ProductTags = chain.invoke({"product_data_json": product_data_json_for_llm})
        print("LG Node: Product analysis successful from LLM.")
        # Make sure to return the original error_messages list if no new errors occurred here
        return {"product_tags": parsed_tags, "error_messages": current_errors}
    except Exception as e:
        import traceback
        print(f"LG Node: Error during product analysis LLM chain invocation: {e}\n{traceback.format_exc()}")
        # Add the new error to the existing list of errors
        new_error_message = f"Product analysis LLM/parsing exception: {str(e)}."
        # If it's a parsing error, include part of the LLM output for debugging
        if hasattr(e, 'llm_output') and e.llm_output: # Langchain's OutputParserException often has this
            new_error_message += f" LLM Output preview: {str(e.llm_output)[:200]}"
        elif hasattr(e, 'response') and hasattr(e.response, 'text'): # For requests.exceptions from LLM API
             new_error_message += f" LLM API Response: {e.response.text[:200]}"

        return {"product_tags": None, "error_messages": current_errors + [new_error_message]}
 
def analyze_influencers_platforms_node(state: MarketingWorkFlowState) -> dict:
    print("LG Node: Analyzing social media platforms...")
    influencer_data_list = state.influencer_data # List[Dict]
    all_platform_analysis_results: Dict[str, Dict[str, PlatformAnalysisResult]] = {}
    errors = list(state.error_messages) # Make a copy

    platform_prompt = ChatPromptTemplate.from_template(social_media_analyst_Prompt)
    # For platform analysis, the Pydantic object helps ensure the LLM returns the correct structure.
    platform_chain = platform_prompt | llm | JsonOutputParser(pydantic_object=PlatformAnalysisResult)

    print(f"LG Node: Analyzing platforms for {len(influencer_data_list)} influencers...")
    for influencer_dict in influencer_data_list:
        influencer_id = influencer_dict.get("influencerId", "UnknownId")
        influencer_name = influencer_dict.get("influencerName", "UnknownName")
        # platforms_data is Dict[str, List[PlatformContentData-like-dicts]]
        platforms_input_data = influencer_dict.get("platforms", {})
        print(f"LG Node: Analyzing platforms for influencer {influencer_name} ({influencer_id})...")

        current_influencer_platform_results: Dict[str, PlatformAnalysisResult] = {}
        for platform_name, content_list_dicts in platforms_input_data.items():
            if not content_list_dicts:
                print(f"LG Node:   Skipping {platform_name} for {influencer_name}: no content.")
                continue
            try:
                # Ensure content_list_dicts matches what the prompt expects (JSON string of content)
                # The prompt social_media_analyst_Prompt expects `content_list_json`
                content_list_json_str = json.dumps(content_list_dicts, ensure_ascii=False, indent=2)
                input_dict = {
                    "influencerName": influencer_name,
                    "platform": platform_name,
                    "content_list_json": content_list_json_str
                }
                # The chain now uses pydantic_object for parsing
                parsed_platform_result: PlatformAnalysisResult = platform_chain.invoke(input_dict)
                print(f"LG Node:     Analysis successful for {platform_name}.")
                current_influencer_platform_results[platform_name] = parsed_platform_result
            except Exception as e:
                print(f"LG Node:     Error analyzing {platform_name} for {influencer_name}: {e}")
                errors.append(f"Platform analysis error for {influencer_name} - {platform_name}: {e}")
        
        all_platform_analysis_results[influencer_id] = current_influencer_platform_results
    
    print("LG Node: Social media platform analysis complete.")
    return {"platform_analysis": all_platform_analysis_results, "error_messages": errors}
   
def generate_influencer_profiles_node(state: MarketingWorkFlowState) -> dict:
    print("LG Node: --- Generating Influencer Profiles ---")
    platform_analysis_map = state.platform_analysis
    influencer_data_list = state.influencer_data
    all_generated_profiles: Dict[str, InfluencerProfile] = {}
    errors = list(state.error_messages)

    if not platform_analysis_map:
        errors.append("Cannot generate profiles: No platform analysis data available.")
        return {"influencer_profiles": {}, "error_messages": errors}

    profile_prompt = ChatPromptTemplate.from_template(influencer_analysis_Prompt)
    profile_chain = profile_prompt | llm | JsonOutputParser(pydantic_object=InfluencerProfile)

    influencer_id_to_name_map = {inf.get("influencerId", "UnknownId"): inf.get("influencerName", "UnknownName") for inf in influencer_data_list}

    for influencer_id, platform_details_for_influencer in platform_analysis_map.items():
        influencer_name = influencer_id_to_name_map.get(influencer_id, f"Unknown ID: {influencer_id}")
        print(f"LG Node:   Generating profile for: {influencer_name} ({influencer_id})")

        if not platform_details_for_influencer:
            print(f"LG Node:     Skipping profile for {influencer_name}: No platform analysis data.")
            errors.append(f"No platform data to generate profile for {influencer_name}.")
            continue

        # Prepare input for profile_prompt: expects a LIST of platform detail dicts
        platform_details_list_for_prompt = [
            details.model_dump() for details in platform_details_for_influencer.values()
        ]
        
        try:
            platform_details_json_str = json.dumps(platform_details_list_for_prompt, ensure_ascii=False, indent=2)
            input_dict = {
                "influencerId": influencer_id,
                "influencerName": influencer_name,
                "platform_details_list_json": platform_details_json_str
            }
            parsed_profile: InfluencerProfile = profile_chain.invoke(input_dict)
            print(f"LG Node:     Profile generated successfully for {influencer_name}.")
            all_generated_profiles[influencer_id] = parsed_profile
        except Exception as e:
            print(f"LG Node:     Error generating profile for {influencer_name}: {e}")
            errors.append(f"Profile generation error for {influencer_name}: {e}")
    
    return {"influencer_profiles": all_generated_profiles, "error_messages": errors}



def match_influencers_node(state: MarketingWorkFlowState) -> dict:
    print("LG Node: --- Matching Influencers to Product ---")
    product_tags_obj = state.product_tags
    influencer_profiles_map = state.influencer_profiles
    product_info_dict = state.product_info
    errors = list(state.error_messages)
    matched_results_list: List[MatchResult] = []

    if not product_tags_obj:
        errors.append("Cannot match: Product tags missing.")
        return {"match_results": [], "error_messages": errors}
    if not influencer_profiles_map:
        errors.append("Cannot match: Influencer profiles missing.")
        return {"match_results": [], "error_messages": errors}

    matcher_prompt = ChatPromptTemplate.from_template(influencer_match_Prompt)
    # The prompt returns a list of dicts, so JsonOutputParser is fine here.
    # If you want each item in the list to be a MatchResult Pydantic object directly,
    # you'd need a custom parser or parse after the LLM call.
    matcher_chain = matcher_prompt | llm | JsonOutputParser() # Expects list of MatchResult-like dicts

    product_input_for_prompt = product_info_dict.copy()
    product_input_for_prompt.update(product_tags_obj.model_dump()) # Add generated tags

    # influencer_profiles_map is Dict[str, InfluencerProfile]
    # The prompt expects a list of influencer profile dicts
    influencers_to_match_list_for_prompt = []
    for inf_id, profile_obj in influencer_profiles_map.items():
        profile_dict = profile_obj.model_dump()
        # Ensure influencerId and influencerName are in the dict for the prompt
        # (though profile_obj from generate_influencer_profiles_node might not have them directly)
        # The prompt for matching takes a list of profiles, so we need to find the name.
        # This requires access to the original influencer_data or a map.
        # Let's assume `generate_influencer_profiles_node` stores profiles keyed by ID
        # and `influencer_data` in state can be used to get names.
        # A better approach might be for InfluencerProfile to include id and name.
        name_from_data = "UnknownName"
        for inf_data in state.influencer_data:
            if inf_data.get("influencerId") == inf_id:
                name_from_data = inf_data.get("influencerName", "UnknownName")
                break
        profile_dict['influencerId'] = inf_id # Explicitly add for the prompt
        profile_dict['influencerName'] = name_from_data
        influencers_to_match_list_for_prompt.append(profile_dict)


    if not influencers_to_match_list_for_prompt:
        print("LG Node:   No influencer profiles to match.")
        return {"match_results": [], "error_messages": errors}

    try:
        input_dict = {
            "product_info": json.dumps(product_input_for_prompt, ensure_ascii=False, indent=2),
            "influencers_to_match": json.dumps(influencers_to_match_list_for_prompt, ensure_ascii=False, indent=2)
        }
        # LLM is expected to return a list of dicts
        parsed_match_list_dicts = matcher_chain.invoke(input_dict)

        if parsed_match_list_dicts and isinstance(parsed_match_list_dicts, list):
            print(f"LG Node:   Matching completed. Found {len(parsed_match_list_dicts)} results.")
            for item_dict in parsed_match_list_dicts:
                try:
                    # Validate and convert to MatchResult Pydantic model
                    match_obj = MatchResult(**item_dict)
                    matched_results_list.append(match_obj)
                except Exception as val_err:
                    print(f"LG Node:   Warning: Invalid match result format from LLM: {item_dict}, Error: {val_err}")
                    errors.append(f"Matcher returned an item with invalid format: {item_dict}")
        else:
            print("LG Node:   Matching failed or returned invalid format (expected a list).")
            errors.append("Matcher did not return a valid list.")
            
    except Exception as e:
        print(f"LG Node:   Error during matching: {e}")
        errors.append(f"Matcher error: {e}")

    return {"match_results": matched_results_list, "error_messages": errors}

def filter_matches_node(state: MarketingWorkFlowState) -> dict:
    print("LG Node: --- Filtering Matches ---")
    match_results_list = state.match_results # List[MatchResult]
    threshold = state.match_threshold # e.g., 75.0 for 75%
    selected: List[MatchResult] = []
    errors = list(state.error_messages)

    if not match_results_list:
        print("LG Node:   No match results to filter.")
        return {"selected_influencers": [], "error_messages": errors}

    for result_obj in match_results_list:
        try:
            score_str = result_obj.match_score # e.g., "88%"
            score_value = float(score_str.replace("%", "")) # Convert "88%" to 88.0
            if score_value >= threshold:
                selected.append(result_obj)
        except (ValueError, TypeError) as e:
            print(f"LG Node:   Warning: Could not parse match score: {result_obj.match_score}. Error: {e}")
            errors.append(f"Invalid match score format for influencer {result_obj.influencerId}: {result_obj.match_score}")
            continue
    
    print(f"LG Node:   Selected {len(selected)} influencers meeting threshold >= {threshold}%.")
    return {"selected_influencers": selected, "error_messages": errors}

def generate_emails_node(state: MarketingWorkFlowState) -> dict:
    print("LG Node: --- Generating Outreach Emails ---")
    selected_influencers_list = state.selected_influencers # List[MatchResult]
    product_info_dict = state.product_info
    product_tags_obj = state.product_tags
    influencer_profiles_map = state.influencer_profiles # Dict[str, InfluencerProfile]
    errors = list(state.error_messages)
    generated_emails_list: List[GeneratedEmail] = []

    if not selected_influencers_list:
        print("LG Node:   No selected influencers to generate emails for.")
        return {"generated_emails": [], "error_messages": errors}

    email_prompt = ChatPromptTemplate.from_template(collab_email_Prompt)
    # The prompt output should be a dict for a single email.
    # JsonOutputParser can try to parse to GeneratedEmail if the LLM output keys match.
    # However, GeneratedEmail in graph_state.py includes influencerId and Name, which the prompt might not return.
    # Let's parse to a dict first, then construct GeneratedEmail.
    email_chain = email_prompt | llm | JsonOutputParser()

    product_input_for_prompt = product_info_dict.copy()
    if product_tags_obj:
        product_input_for_prompt.update(product_tags_obj.model_dump())

    for influencer_match_obj in selected_influencers_list:
        influencer_id = influencer_match_obj.influencerId
        influencer_name = influencer_match_obj.influencerName
        print(f"LG Node:   Generating email for: {influencer_name} ({influencer_id})")

        profile_obj = influencer_profiles_map.get(influencer_id)
        if not profile_obj:
            print(f"LG Node:     Warning: Profile not found for {influencer_name}. Cannot generate email.")
            errors.append(f"Profile missing for selected influencer {influencer_name}.")
            continue
        
        profile_dict_for_prompt = profile_obj.model_dump()
        # Ensure prompt has access to name if it uses {influencerName} in the template for personalization
        profile_dict_for_prompt['influencerName'] = influencer_name 
        profile_dict_for_prompt['influencerId'] = influencer_id

        try:
            input_dict = {
                "product_info": json.dumps(product_input_for_prompt, ensure_ascii=False, indent=2),
                "influencer_profile": json.dumps(profile_dict_for_prompt, ensure_ascii=False, indent=2)
            }
            # LLM returns a dict like {"email_subject": "...", "email_body": "..."}
            parsed_email_dict = email_chain.invoke(input_dict)

            if parsed_email_dict and isinstance(parsed_email_dict, dict) and \
               "email_subject" in parsed_email_dict and "email_body" in parsed_email_dict:
                print(f"LG Node:     Email generated successfully for {influencer_name}.")
                # Construct GeneratedEmail Pydantic model
                email_obj = GeneratedEmail(
                    influencerId=influencer_id,
                    influencerName=influencer_name,
                    email_subject=parsed_email_dict["email_subject"],
                    email_body=parsed_email_dict["email_body"]
                )
                generated_emails_list.append(email_obj)
            else:
                print(f"LG Node:     Email generation failed or invalid format for {influencer_name}.")
                errors.append(f"Email generation failed for {influencer_name}.")
        except Exception as e:
            print(f"LG Node:     Error generating email for {influencer_name}: {e}")
            errors.append(f"Email generation error for {influencer_name}: {e}")
    
    return {"generated_emails": generated_emails_list, "error_messages": errors}


# --- Conditional Edge Logic ---
def should_generate_emails(state: MarketingWorkFlowState) -> str:
    print("LG Node: --- Checking if emails should be generated ---")
    if state.selected_influencers and len(state.selected_influencers) > 0:
        print("LG Node:   Condition met: Found selected influencers. Proceeding to email generation.")
        return "generate_emails_node" # Node name string
    else:
        print("LG Node:   Condition not met: No selected influencers. Ending workflow.")
        return END # LangGraph's END constant



# --- product analysis workflow ---
product_analysis_builder=StateGraph(ProductAnalysisState)
product_analysis_builder.add_node("analyze_product_node", analyze_product_node)
product_analysis_builder.add_edge(START, "analyze_product_node")
product_analysis_builder.add_edge("analyze_product_node", END)

product_analysis_app = product_analysis_builder.compile()
print("product analysis compiled successfully!")



influcencer_analysis_builder= StateGraph(MarketingWorkFlowState)
influcencer_analysis_builder.add_node("analyze_influencers_platforms_node", analyze_influencers_platforms_node)
influcencer_analysis_builder.add_node("generate_influencer_profiles_node", generate_influencer_profiles_node)
influcencer_analysis_builder.add_edge(START, "analyze_influencers_platforms_node")

influcencer_analysis_builder.add_edge("generate_influencer_profiles_node", END)
influencer_app= influcencer_analysis_builder.compile()
print("Influencer analysis app compiled successfully!")

# --- Compile Marketing Workflow ---
workflow_builder = StateGraph(MarketingWorkFlowState)

workflow_builder.add_node("analyze_product_node", analyze_product_node)
workflow_builder.add_node("analyze_influencers_platforms_node", analyze_influencers_platforms_node)
workflow_builder.add_node("generate_influencer_profiles_node", generate_influencer_profiles_node)
workflow_builder.add_node("match_influencers_node", match_influencers_node)
workflow_builder.add_node("filter_matches_node", filter_matches_node)
workflow_builder.add_node("generate_emails_node", generate_emails_node)

workflow_builder.add_edge(START, "analyze_product_node")
workflow_builder.add_edge("analyze_product_node", "analyze_influencers_platforms_node")
workflow_builder.add_edge("analyze_influencers_platforms_node", "generate_influencer_profiles_node")
workflow_builder.add_edge("generate_influencer_profiles_node", "match_influencers_node")
workflow_builder.add_edge("match_influencers_node", "filter_matches_node")

workflow_builder.add_conditional_edges(
    "filter_matches_node",
    should_generate_emails,
    {
        "generate_emails_node": "generate_emails_node",
        END: END
    }
)

workflow_builder.add_edge("generate_emails_node", END)

workflow_app = workflow_builder.compile()
print("Marketing workflow compiled successfully!")



# %%
def intent_analysis_node(state: IntentAnalysisState) -> Dict[str, Any]: # Return type is a dict of fields to update
    print("LG Node: --- Analyzing Reply Intent (Pydantic State) ---")
    
    # Access fields as attributes from the Pydantic state model
    subject = state.email_subject
    body = state.email_body

    if not body: # Empty string "" is falsy
        print("LG Node: Email body is empty.")
        # Return a dictionary of the fields to update in the Pydantic state
        return {"analysis_result": None, "error_message": "Email body is empty."}

    intent_prompt = ChatPromptTemplate.from_template(email_intent_Prompt)
    # If you had a Pydantic model for the output of email_intent_Prompt (e.g., EmailIntentLLMOutput):
    # intent_chain = intent_prompt | llm | JsonOutputParser(pydantic_object=EmailIntentLLMOutput)
    # Then analysis_result could be typed as Optional[EmailIntentLLMOutput] in IntentAnalysisState
    intent_chain = intent_prompt | llm | JsonOutputParser() # Returns a dict

    try:
        input_dict = {
            "email_subject": subject if subject else "N/A",
            "email_body": body
        }
        # The result from the LLM chain (after JsonOutputParser) is a dictionary
        parsed_result_dict: Optional[Dict[str, Any]] = intent_chain.invoke(input_dict)

        if parsed_result_dict and isinstance(parsed_result_dict, dict) and "cooperation_intent" in parsed_result_dict:
            print("LG Node:   Intent analysis successful.")
            return {"analysis_result": parsed_result_dict, "error_message": None}
        else:
            error_msg = "Intent analysis returned invalid or incomplete format."
            if parsed_result_dict:
                error_msg += f" Got: {str(parsed_result_dict)[:200]}"
            print(f"LG Node:   {error_msg}")
            return {"analysis_result": None, "error_message": error_msg}
            
    except Exception as e: # Catches OutputParserException and others
        error_msg = f"Intent analysis LLM chain exception: {str(e)}"
        if hasattr(e, 'llm_output') and e.llm_output: # For OutputParserException
            error_msg += f". LLM Output: '{e.llm_output[:300]}...'"
        print(f"LG Node:   {error_msg}\n{traceback.format_exc()}")
        return {"analysis_result": None, "error_message": error_msg}
# --- Compile Intent Analysis Workflow ---
intent_workflow_builder = StateGraph(IntentAnalysisState)
intent_workflow_builder.add_node("analyze_reply_intent_node", intent_analysis_node)
intent_workflow_builder.add_edge(START, "analyze_reply_intent_node")
intent_workflow_builder.add_edge("analyze_reply_intent_node", END)

intent_app = intent_workflow_builder.compile()
print("Intent analysis workflow compiled successfully!")


# %%
