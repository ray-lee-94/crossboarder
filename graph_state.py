# %%
from typing import List, Optional, Dict, Any
from pydantic import BaseModel 


# Define structure for clarity
class PlatformContentData(BaseModel):
    """
    Args:
        BaseModel (_type_): _description_
    """
    content_title: Optional[str]
    promo_category: Optional[str]
    enhanced_tag: Optional[str]
    cover_image_url: Optional[str]
    content_url : Optional[str]
    like_count: Optional[int]
    comment_count: Optional[int]
    publish_date: Optional[str]


class PlatformAnalysisResult(BaseModel):
    """
    Args:
        BaseModel (_type_): _description_
    """
    audienceGender: str # 
    audienceAge: str
    regionCountry: str
    language: str
    contentFormat: List[str]
    recentContentSummary: str
    videoStyle: str
    contentTone: str
    categoryDepth: str
    promotionAbility: str
    brandRepetitionRate: str
    contentScene: List[str]
    platform: str

class InfluencerProfile(BaseModel):
    # Matches the output structure of analysisPromt
    核心内容方向: List[str]
    综合人设_风格: str # Renamed
    主要受众画像: str
    商业化程度评估: str
    跨平台内容一致性: str
    潜在合作品牌类型: List[str]
    达人总体评价: str
    带货能力评级: str

class ProductTags(BaseModel):
    # Matches the output structure of productPromt
    FeatureTags: List[str]
    AudienceTags: List[str]
    UsageScenarioTags: List[str]

class MatchResult(BaseModel):
     # Matches the output structure of matcherPromt
    influencerId: str
    influencerName: str
    match_score: str # Keeping as string ('88%') as per prompt output example
    match_rationale: str

class GeneratedEmail(BaseModel):
    # Matches the output structure of EmailPromt
    influencerId: str
    influencerName: str
    email_subject: str
    email_body: str


# --- Main WorkFlow State ---
class MarketingWorkFlowState(BaseModel):
    # Input Data (Shoud be provied when invoking the graph)
    product_info: Dict[str, Any]
    influencer_data: List[Dict[str, Any]] # List of {"id": str， "platforms":{"platform_name": [PlatformContentData}]}

    # Intermediate & Output Data ( Managed by the graph)
    product_tags: Optional[ProductTags]
    platform_analysis: Dict[str,Dict[str, PlatformAnalysisResult]] # ["influencer_id":{platform_name:analysis_result}]
    influencer_profiles: Dict[str, InfluencerProfile] # ["influencer_id":profile]
    match_results: List[MatchResult]
    selected_influencers: Optional[list[MatchResult]] # Influcencer passing the match threshold
    generated_emails: Optional[list[GeneratedEmail]] # Generated emails for the selected influencers
    error_messages: List[str] # To collect error messages during workflow execution
    match_threshold: float = 0.8 # Default match threshold


class IntentAnalysisState(BaseModel):
    email_subject: Optional[str]
    email_body: str
    analysis_result: Optional[Dict[str, Any]]
    error_message: Optional[str]
