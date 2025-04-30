import json 
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser,JsonOutputParser
from langgraph.graph import StateGraph, END, START
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
from graph_state import MarketingWorkFlowState, IntentAnalysisState
from prompts import social_media_analyst_Prompt, product_metadata_Prompt, influencer_analysis_Prompt,influencer_match_Prompt, collab_email_Prompt, email_intent_Prompt

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

str_parser = StrOutputParser()


# Use JsonOutputParser for more robustness where JSON is expected
# json_parser = JsonOutputParser()
# For even more robustness with specific models, consider Function Calling parsers

def safe_json_parser(json_string: str, default=None)-> dict:
    """Safely parse a JSON string, potentially stripping markdown."""
    try:
        if json_string.startswith("```json"):
            json_string = json_string[7:]
        if json_string.endswith("```"):
            json_string = json_string[:-3]
        json_string= json_string.strip()
        return json.loads(json_string)
    
    except json.JSONDecodeError:
        print(f"Error parsing JSON: {json_string}")
        return default
    except Exception as e:
        print(f"Waring: An unexpected error occurred: {e}")
        return default
    
# %% Node functions

def analyze_product_node(state: MarketingWorkFlowState):
    """Analyzes product info to extarct tags using product_metadata_Prompt"""
    print("Analyzing product info...")
    product_info = state.product_info
    prompt_template = ChatPromptTemplate.from_template(product_metadata_Prompt)

    chain = prompt_template | llm | JsonOutputParser()

    try:
        parsed_result= chain.invoke({"商品信息JSON对象": json.dumps(product_info,ensure_ascii=False)})

        if parsed_result and isinstance(parsed_result, dict) and "FeatureTags" in parsed_result and \
            "AudienceTags" in parsed_result and "UsageScenarioTags" in parsed_result:
            print("Product analysis successful.")
            return {"product_tags": parsed_result}
        else:
            print("Failed to analyze product info.")
            return {"error_messages":state.error_messages+["Product analysis failed or returned invalid format."]}
    except Exception as e:
        print(f" Error durring prodcut analysis: {e}")
        return {"error_messages":state.error_messages+["Product analysis failed:{e}."]}
    
def analyze_influencers_platforms_node(state: MarketingWorkFlowState):
    """Analyzes each platform for each influencer using social_media_analyst_Prompt"""
    print("Analyzing social media platforms...")
    influencer_data= state.influencer_data
    all_platform_analysis={}
    errors=[]

    social_media_analyst_prompt_template = ChatPromptTemplate.from_template(social_media_analyst_Prompt)
    chain = social_media_analyst_prompt_template | llm | JsonOutputParser()

    for influencer in influencer_data:
        influencer_id = influencer["id"]
        influencer_name = influencer["name"]
        platforms_data = influencer.get("platforms",[])
        print(f" Analyzing platforms for influencer {influencer_name} {influencer_id}...")

        influencer_platform_results=[]

        for platform_name, content_list in platforms_data.items():
            if not content_list:
                print( f"   Skipping {platform_name} for {influencer_name} as no content found.")
                continue
            
            print(f" Analyzing content for platform: {platform_name}...")

            try:
                input_dict={"达人名称": influencer_name, "分析平台": platform_name, "内容列表": content_list}

                parsed_result=chain.invoke(input_dict)

                if parsed_result and isinstance(parsed_result, dict): # Basic check
                    print(f"      Analysis successful for {platform_name}.")
                    influencer_platform_results[platform_name] = parsed_result
                else:
                     print(f"      Analysis failed or invalid format for {platform_name}.")
                     errors.append(f"Platform analysis failed for {influencer_name} - {platform_name}.")
            except Exception as e:
                print(f"      Error analyzing {platform_name} for {influencer_name}: {e}")
                errors.append(f"Platform analysis error for {influencer_name} - {platform_name}: {e}")

        all_platform_analysis[influencer_id] = influencer_platform_results

    return {"platform_analysis": all_platform_analysis, "error_messages": state.error_messages + errors}


def generate_influencer_profiles_node(state: MarketingWorkFlowState):
    """Generates overall profiles using influencer_analysis_Prompt based on platform analysis."""
    print("--- Generating Influencer Profiles ---")
    platform_analysis = state.platform_analysis
    influencer_data = state.influencer_data# Need name and ID
    all_profiles = {}
    errors = []

    analysis_prompt_template = ChatPromptTemplate.from_template(influencer_analysis_Prompt)
    # Note: Ideally use JsonOutputParser here
    # analysis_chain = analysis_prompt_template | llm | safe_json_parser

    influencer_map = {inf['id']: inf['name'] for inf in influencer_data}

    for influencer_id, platform_details_map in platform_analysis.items():
        influencer_name = influencer_map.get(influencer_id, f"Unknown ID: {influencer_id}")
        print(f"  Generating profile for: {influencer_name} ({influencer_id})")

        if not platform_details_map:
             print(f"    Skipping profile generation for {influencer_name}: No platform analysis data.")
             errors.append(f"No platform data to generate profile for {influencer_name}.")
             continue

        # Prepare input for analysisPromt - expects a LIST of platform details
        platform_details_list = []
        for platform, details in platform_details_map.items():
            # Add platform name and other key metrics if available/needed by the prompt
            details_with_platform = details.copy()
            details_with_platform['platform'] = platform
            # Add other known metrics if needed (e.g., follower count if available in influencer_data)
            platform_details_list.append(details_with_platform)

        # Format the prompt - replace placeholders
        formatted_analysis_prompt =analysis_prompt_template.replace("[请在此处插入达人ID]", influencer_id)\
                                                  .replace("[请在此处插入为该达人选择的主要名称]", influencer_name)
        analysis_prompt_template_filled = ChatPromptTemplate.from_template(formatted_analysis_prompt)
        analysis_chain_filled = analysis_prompt_template_filled | llm | safe_json_parser

        try:
            # Input expects '平台账号详情数据列表'
            input_dict = {"平台账号详情数据列表": json.dumps(platform_details_list, ensure_ascii=False, indent=2)}
            parsed_result= analysis_chain_filled.invoke(input_dict)

            if parsed_result and isinstance(parsed_result, dict): # Basic check
                print(f"    Profile generated successfully for {influencer_name}.")
                all_profiles[influencer_id] = parsed_result
            else:
                print(f"    Profile generation failed or invalid format for {influencer_name}.")
                errors.append(f"Profile generation failed for {influencer_name}.")
        except Exception as e:
            print(f"    Error generating profile for {influencer_name}: {e}")
            errors.append(f"Profile generation error for {influencer_name}: {e}")

    return {"influencer_profiles": all_profiles, "error_messages": state.error_messages + errors}


def match_influencers_node(state: MarketingWorkFlowState):
    """Matches product against generated influencer profiles using influencer_match_Prompt."""
    print("--- Matching Influencers to Product ---")
    product_tags = state.product_tags
    influencer_profiles = state.influencer_profiles
    product_info = state.product_info
    influencer_data = state.influencer_data
    errors = []

    if not product_tags:
        print("  Skipping matching: Product tags not available.")
        return {"error_messages": state.error_messages + ["Cannot match: Product tags missing."]}
    if not influencer_profiles:
        print("  Skipping matching: Influencer profiles not available.")
        return {"error_messages": state.error_messages + ["Cannot match: Influencer profiles missing."]}

    matcher_prompt_template = ChatPromptTemplate.from_template(influencer_match_Prompt)
    # Note: Ideally use JsonOutputParser here, expecting a LIST of results
    matcher_chain = matcher_prompt_template | llm | safe_json_parser

    # Prepare the list of influencer profiles for the prompt
    influencers_to_match_list = []
    influencer_map = {inf['id']: inf['name'] for inf in influencer_data}
    for inf_id, profile in influencer_profiles.items():
        profile_with_id = profile.copy()
        profile_with_id['达人ID'] = inf_id
        profile_with_id['达人名称'] = influencer_map.get(inf_id, f"Unknown ID: {inf_id}")
        # Add other fields if your 'matcherPromt' expects them (e.g., follower scale)
        influencers_to_match_list.append(profile_with_id)

    if not influencers_to_match_list:
        print("  No influencer profiles to match.")
        return {"match_results": []}

    # Combine product info and tags for the prompt context
    product_input_data = product_info.copy()
    product_input_data.update(product_tags) # Add generated tags

    try:
        # Input expects 'product_info' and 'influencers_to_match'
        input_dict = {
            "product_info": json.dumps(product_input_data, ensure_ascii=False, indent=2),
            "influencers_to_match": json.dumps(influencers_to_match_list, ensure_ascii=False, indent=2)
        }
        parsed_result= matcher_chain.invoke(input_dict)
        # Expecting a JSON list string

        if parsed_result and isinstance(parsed_result, list):
            print(f"  Matching completed. Found {len(parsed_result)} results.")
             # Optional: Validate structure of each item in the list
            valid_results = []
            for item in parsed_result:
                if isinstance(item, dict) and "influencer_id" in item and "match_score" in item and "match_rationale" in item:
                    valid_results.append(item)
                else:
                    print(f"  Warning: Invalid match result format found: {item}")
                    errors.append("Matcher returned an item with invalid format.")
            return {"match_results": valid_results, "error_messages": state["error_messages"] + errors}
        else:
            print("  Matching failed or returned invalid format (expected a list).")
            errors.append("Matcher did not return a valid list.")
            return {"match_results": [], "error_messages": state["error_messages"] + errors}
    except Exception as e:
        print(f"  Error during matching: {e}")
        errors.append(f"Matcher error: {e}")
        return {"match_results": [], "error_messages": state["error_messages"] + errors}

def filter_matches_node(state: MarketingWorkFlowState):
    """Filters match results based on the threshold."""
    print("--- Filtering Matches ---")
    match_results = state.match_results
    threshold = state.match_threshold
    selected = []

    if not match_results:
        print("  No match results to filter.")
        return {"selected_influencers": []}

    for result in match_results:
        try:
            # Extract number from score string like "88%" -> 88.0
            score_str = result.get("match_score", "0%").strip('% ')
            score = float(score_str)
            if score >= threshold:
                selected.append(result)
        except (ValueError, TypeError):
            print(f"  Warning: Could not parse match score: {result.get('match_score')}")
            continue # Skip if score is invalid

    print(f"  Selected {len(selected)} influencers meeting threshold >= {threshold}%.")
    return {"selected_influencers": selected}

def generate_emails_node(state: MarketingWorkFlowState):
    """Generates outreach emails for selected influencers using collab_email_Prompt."""
    print("--- Generating Outreach Emails ---")
    selected_influencers = state.selected_influencers
    product_info = state.product_info
    product_tags = state.product_tags
    influencer_profiles = state.influencer_profiles
    errors = []
    generated_emails = []

    if not selected_influencers:
        print("  No selected influencers to generate emails for.")
        return {"generated_emails": []}

    # email_prompt_template = ChatPromptTemplate.from_template(collab_email_Prompt)
    # Note: Ideally use JsonOutputParser here
    # email_chain = email_prompt_template | llm | safe_json_parser

    # Combine product info and tags
    product_input_data = product_info.copy()
    if product_tags: # Add tags if available
        product_input_data.update(product_tags)

    for influencer_match in selected_influencers:
        influencer_id = influencer_match['influencer_id']
        influencer_name = influencer_match['influencer_name']
        print(f"  Generating email for: {influencer_name} ({influencer_id})")

        # Get the full profile for this influencer
        profile = influencer_profiles.get(influencer_id)
        if not profile:
            print(f"    Warning: Profile not found for {influencer_name}. Cannot generate email.")
            errors.append(f"Profile missing for selected influencer {influencer_name}.")
            continue

        # Prepare input for EmailPromt
        # Need to fill placeholders like {达人ID}, {达人名称} etc.
        # Assuming EmailPromt needs product_info and the single influencer's profile
        profile_with_id = profile.copy()
        profile_with_id['达人ID'] = influencer_id
        profile_with_id['达人名称'] = influencer_name
        # Add other fields like 主语言, 地区 if available and needed by prompt

        # Format the prompt (replace placeholders if any - though EmailPromt looks like it takes dicts directly)
        email_prompt_template_filled = ChatPromptTemplate.from_template(collab_email_Prompt) # Re-create if needed
        email_chain_filled = email_prompt_template_filled | llm | safe_json_parser

        try:
            # Input expects 'product_info' and '达人账号总表信息'
            input_dict = {
                "product_info": json.dumps(product_input_data, ensure_ascii=False, indent=2),
                "达人账号总表信息": json.dumps(profile_with_id, ensure_ascii=False, indent=2)
            }
            parsed_result= email_chain_filled.invoke(input_dict)

            if parsed_result and isinstance(parsed_result, dict) and \
               "email_subject" in parsed_result and "email_body" in parsed_result:
                print(f"    Email generated successfully for {influencer_name}.")
                 # Add back IDs for tracking
                parsed_result['influencer_id'] = influencer_id
                parsed_result['influencer_name'] = influencer_name
                generated_emails.append(parsed_result)
            else:
                print(f"    Email generation failed or invalid format for {influencer_name}.")
                errors.append(f"Email generation failed for {influencer_name}.")
        except Exception as e:
            print(f"    Error generating email for {influencer_name}: {e}")
            errors.append(f"Email generation error for {influencer_name}: {e}")

    return {"generated_emails": generated_emails, "error_messages": state["error_messages"] + errors}

# --- Conditional Edge Logic ---

def should_generate_emails(state: MarketingWorkFlowState):
    """Determines whether to proceed to email generation or end."""
    print("--- Checking if emails should be generated ---")
    selected_influencers = state.selected_influencers
    if selected_influencers and len(selected_influencers) > 0:
        print("  Condition met: Found selected influencers. Proceeding to email generation.")
        return "generate_emails"
    else:
        print("  Condition not met: No selected influencers. Ending workflow.")
        return END # Use END directly here

    


workflow= StateGraph(MarketingWorkFlowState)

workflow.add_node("analyze_product", analyze_product_node)
workflow.add_node("analyze_platforms", analyze_influencers_platforms_node)
workflow.add_node("generate_profiles",generate_influencer_profiles_node)
workflow.add_node("match_influences", match_influencers_node)
workflow.add_node("filter_matches", filter_matches_node)
workflow.add_node("generate_emails", generate_emails_node)

# %%
workflow.add_edge(START,"analyze_product")
workflow.add_edge("analyze_product","analyze_platforms")
workflow.add_edge("analyze_platforms","generate_profiles")
workflow.add_edge("generate_profiles","match_influences")
workflow.add_edge("match_influences","filter_matches")

workflow.add_conditional_edges("filter_matches", should_generate_emails,{"generate_emails":"generate_emails",END:END})

workflow.add_edge("generate_emails",END)

workflow_app=workflow.compile()

print("Marketing workflow compiled successfully!")


def intent_analysis_node(state: IntentAnalysisState):
    # ... (Copy the intent_analysis_node function here) ...
    print("--- Node: Analyzing Reply Intent ---")
    subject = state.email_subject
    body = state.email_body
    error_msg = None # Initialize error message

    if not body:
        return {"analysis_result": None, "error_message": "Email body is empty."}

    # Use the corrected variable name
    intent_prompt_template = ChatPromptTemplate.from_template(email_intent_Prompt)
    intent_chain = intent_prompt_template | llm | JsonOutputParser()

    try:
        input_dict = {
            "email_subject": subject if subject else "N/A",
            "email_body": body
        }
        parsed_result= intent_chain.invoke(input_dict)

        # More specific validation based on intent prompt's output keys
        required_keys = ["cooperation_intent", "key_points", "suggested_next_step",
                         "sentiment", "is_urgent", "notification_summary"]
        if parsed_result and isinstance(parsed_result, dict) and all(key in parsed_result for key in required_keys):
            print("  Intent analysis successful in node.")
            return {"analysis_result": parsed_result, "error_message": None}
        else:
            print("  Intent analysis failed or invalid format in node.")
            error_msg = "Intent analysis failed or returned invalid format."
            return {"analysis_result": None, "error_message": error_msg}
    except Exception as e:
        print(f"  Error during intent analysis node: {e}")
        return {"analysis_result": None, "error_message": f"Intent analysis error: {e}"}
    
    
intent_workflow= StateGraph(IntentAnalysisState)

intent_workflow.add_node("analyze_reply_intent", intent_analysis_node)

intent_workflow.add_edge(START,"analyze_reply_intent")
intent_workflow.add_edge("analyze_reply_intent",END)

intent_app=intent_workflow.compile()

print("Intent analysis workflow compiled successfully!")