def map_topic_ids_from_db(session, user_keyword_id, results):
    """
    Enhanced topic mapping with:
    - Fuzzy string matching
    - Synonym support
    - Better normalization
    - Detailed debug logging
    - Performance optimizations
    """
    import logging
    import re
    from sqlalchemy.exc import IntegrityError
    from fuzzywuzzy import fuzz
    from models import UserTopicDistribution
    from collections import defaultdict
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Enable debug logging

    # --- Constants ---
    UNCategorized_UUID = "00000000-0000-0000-0000-000000000000"
    MIN_MATCH_SCORE = 70  # Fuzzy matching threshold
    TOPIC_SYNONYMS = {
        "ai": "artificial intelligence",
        "ml": "machine learning",
        "nlp": "natural language processing"
    }

    # --- Ensure Uncategorized Topic Exists ---
    try:
        uncategorized_topic = session.query(UserTopicDistribution).filter_by(
            id=UNCategorized_UUID,
            user_keyword_id=user_keyword_id
        ).first()
        
        if not uncategorized_topic:
            uncategorized_topic = UserTopicDistribution(
                id=UNCategorized_UUID,
                user_keyword_id=user_keyword_id,
                topic_name="Uncategorized",
                percentage=0.0
            )
            session.add(uncategorized_topic)
            session.flush()
    except IntegrityError:
        session.rollback()
        logger.debug("Uncategorized topic already exists")

    # --- Load Topics from DB ---
    db_topics = session.query(UserTopicDistribution).filter_by(
        user_keyword_id=user_keyword_id
    ).all()

    # --- Preprocess Topics ---
    def normalize_text(text):
        """Enhanced normalization with synonym handling"""
        if not text:
            return ""
            
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        text = re.sub(r'\s+', ' ', text)     # Normalize whitespace
        
        # Handle common synonyms
        for short, long in TOPIC_SYNONYMS.items():
            text = re.sub(rf'\b{short}\b', long, text)
            
        return text

    # Create lookup structures
    topic_map = {}          # Normalized name -> ID
    keyword_map = {}        # Individual keywords -> [topic_ids]
    topic_keywords = {}     # topic_id -> [keywords]
    
    for topic in db_topics:
        norm_name = normalize_text(topic.topic_name)
        topic_map[norm_name] = topic.id
        
        # Extract keywords from topic name
        keywords = set(norm_name.split())
        for kw in keywords:
            if len(kw) > 3:  # Ignore short words
                keyword_map.setdefault(kw, []).append(topic.id)
        
        topic_keywords[topic.id] = keywords

    # Add uncategorized fallback
    topic_map["uncategorized"] = UNCategorized_UUID

    # --- Debug Logging ---
    logger.debug(f"Loaded {len(db_topics)} topics for keyword {user_keyword_id}:")
    for topic in db_topics:
        logger.debug(f"  - {topic.topic_name} (ID: {topic.id})")

    # --- Matching Logic ---
    def find_best_topic(topic_name):
        """Find best matching topic with scoring"""
        if not topic_name:
            return UNCategorized_UUID, "empty"
            
        norm_input = normalize_text(topic_name)
        
        # 1. Check exact match
        if norm_input in topic_map:
            return topic_map[norm_input], "exact"
        
        # 2. Check individual keywords
        input_keywords = set(kw for kw in norm_input.split() if len(kw) > 3)
        keyword_matches = defaultdict(int)
        
        for kw in input_keywords:
            for topic_id in keyword_map.get(kw, []):
                keyword_matches[topic_id] += 1
        
        if keyword_matches:
            best_topic = max(keyword_matches.items(), key=lambda x: x[1])
            if best_topic[1] >= 2:  # Require at least 2 keyword matches
                return best_topic[0], "keyword"

        # 3. Fuzzy match against all topics
        best_score = 0
        best_topic = None
        
        for norm_db_name, topic_id in topic_map.items():
            if norm_db_name == "uncategorized":
                continue
                
            score = fuzz.token_set_ratio(norm_input, norm_db_name)
            if score > best_score and score >= MIN_MATCH_SCORE:
                best_score = score
                best_topic = topic_id
        
        if best_topic:
            return best_topic, f"fuzzy ({best_score}%)"

        return UNCategorized_UUID, "no_match"

    # --- Process Results ---
    stats = defaultdict(int)
    
    for result in results:
        original_name = result.get("topic_name", "")
        topic_id, match_type = find_best_topic(original_name)
        
        result["topic_id"] = topic_id
        stats[match_type] += 1
        
        # Update name if uncategorized
        if match_type == "no_match":
            result["topic_name"] = "Uncategorized"
            
        logger.debug(f"Mapped '{original_name}' → {topic_id} ({match_type})")

    # --- Log Statistics ---
    logger.info(f"Topic mapping completed for {len(results)} results:")
    logger.info(f"- Exact matches: {stats.get('exact', 0)}")
    logger.info(f"- Keyword matches: {stats.get('keyword', 0)}")
    logger.info(f"- Fuzzy matches: {stats.get('fuzzy', 0)}")
    logger.info(f"- Uncategorized: {stats.get('no_match', 0) + stats.get('empty', 0)}")
    
    return stats