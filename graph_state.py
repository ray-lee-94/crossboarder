# %%
from typing import List, Optional, Dict, Any
from pydantic import BaseModel,Field 


# --- Supporting Data Structures for State ---
class PlatformContentData(BaseModel):
    content_title: Optional[str] = None
    promo_category: Optional[str] = None # Assuming single category per content for simplicity in prompt
    enhanced_tag: Optional[str] = None   # Assuming single tag per content
    cover_image_url: Optional[str] = None
    content_url: Optional[str] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    publish_date: Optional[str] = None # Consider datetime for consistency if possible

class PlatformAnalysisResult(BaseModel):
    # Matches output of social_media_analyst_Prompt
    audienceGender: str # 受众性别
    audienceAge: str # 受众年龄
    regionCountry: str # 地区国家
    language: str # 语言
    contentFormat: List[str] # 内容格式
    recentContentSummary: str
    videoStyle: str
    contentTone: str
    categoryDepth: str
    promotionAbility: str
    brandRepetitionRate: str
    contentScene: List[str]
    platform: str # To confirm which platform this analysis is for

class InfluencerProfile(BaseModel):
    # Matches the output structure of influencer_analysis_Prompt
    coreContentDirection: List[str]
    overallPersonaAndStyle: str
    mainAudience: str
    commercialDegree: str
    crossPlatformConsist: str
    potentialBrandType: List[str]
    influencerEval: str
    goodsCarryRating: str


class ProductTags(BaseModel):
    FeatureTags: List[str] = Field(default_factory=list)
    AudienceTags: List[str] = Field(default_factory=list)
    UsageScenarioTags: List[str] = Field(default_factory=list)
    coreContentDirection: Optional[List[str]] = Field(default_factory=list, description="基于产品特性推断的，适合展示该产品的内容创作方向") # New
    overallPersonaAndStyle: Optional[str] = Field(None, description="基于产品特性和定位，拟人化的产品调性和风格") # New (string, as per prompt example) - or List[str] if multiple styles are possible
    mainAudience: Optional[str] = Field(None, description="对产品核心目标用户的画像描述") # New (string, as per prompt example)


class InfluencerRecommendationRequest(BaseModel):
    product_info: Dict[str, Any] # Product information as a dictionary
    product_tags: ProductTags # Product tags are essential for matching
    influencer_profiles_input: Dict[str, InfluencerProfile] 
    match_threshold: Optional[float] = Field(75.0, ge=0, le=100) # Default 75%, range 0-100

class MatchResult(BaseModel):
    # Matches the output structure of influencer_match_Prompt
    influencerId: str
    influencerName: str
    match_score: str # e.g., "88%"
    match_rationale: str
class GeneratedEmail(BaseModel):
    # Matches the output structure of collab_email_Prompt
    # Adding influencerId and Name here if your node adds them for tracking
    influencerId: str
    influencerName: str
    email_subject: str
    email_body: str

# --- Main WorkFlow State ---
class MarketingWorkFlowState(BaseModel):
    # Input Data (Should be provided when invoking the graph)
    product_info: Optional[Dict[str, Any]] = Field(..., description="Detailed product information as a dictionary.")
    influencer_data: Optional[List[Dict[str, Any]]] = Field(..., description="List of influencer data. Each dict should contain 'influencerId', 'influencerName', and 'platforms'. Platforms is Dict[str, List[PlatformContentData]].")

    # Intermediate & Output Data (Managed by the graph)
    product_tags: Optional[ProductTags] = None
    platform_analysis: Optional[Dict[str, Dict[str, PlatformAnalysisResult]]] = None # {"influencer_id": {"platform_name": PlatformAnalysisResult}}
    influencer_profiles: Optional[Dict[str, InfluencerProfile]] = None # {"influencer_id": InfluencerProfile}
    match_results: Optional[List[MatchResult]] = None
    selected_influencers: Optional[List[MatchResult]] = None # Influencers passing the match threshold
    generated_emails: Optional[List[GeneratedEmail]] = None # Generated emails for the selected influencers
    error_messages: List[str] = Field(default_factory=list) # To collect error messages
    match_threshold: float = Field(default=75.0, description="Match score threshold (e.g., 75.0 for 75%)") # API request uses 75.0, state uses 0.8. Be consistent. Let's use 0-100 scale.

    # class Config:
    #     arbitrary_types_allowed = True # If you use non-Pydantic types directly in state



# ---Product Analysis State ---
class ProductAnalysisState(BaseModel):
    product_info: Dict[str, Any] = Field(..., description="Detailed product information as a dictionary.")
    product_tags: Optional[ProductTags] = None
    error_message: Optional[str] = None

# --- Intent Analysis State ---
class IntentAnalysisState(BaseModel):
    email_subject: Optional[str] = None
    email_body: str
    analysis_result: Optional[Dict[str, Any]] = None # Structure based on email_intent_Prompt output
    error_message: Optional[str] = None


class EmailGenerationState(BaseModel): # Using Pydantic BaseModel for state
    # Inputs required by generate_emails_node
    selected_influencers: List[MatchResult] # List of influencers to generate emails for
    product_info: Dict[str, Any] # Product details as a dictionary
    product_tags: Optional[ProductTags] = None # Product tags (can be optional if email gen can work without)
    influencer_profiles: Dict[str, InfluencerProfile] # Profiles map, key is influencerId
    
    # Output of the node
    generated_emails: Optional[List[GeneratedEmail]] = None
    
    # Common field for errors
    error_messages: List[str] = Field(default_factory=list)