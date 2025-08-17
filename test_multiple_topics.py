#!/usr/bin/env python3
"""
Temp Test Program - Multiple Topic Scraping
"""

from get_laws_on_topic_scraper import get_laws_from_multiple_topics

def test_multiple_topics():
    """Test scraping multiple topic pages"""
    
    # Define topic URLs to scrape
    topic_urls = [
        "https://www.lagboken.se/lagboken/start/arbetsratt-och-arbetsmiljoratt/",
        # Add more topic URLs here when needed
    ]
    
    print("Testing multiple topic scraping...")
    print(f"Topic URLs: {topic_urls}")
    
    # Test with limited laws for quick testing
    result = get_laws_from_multiple_topics(
        topic_urls=topic_urls,
        scrape_individual_laws=True,
        max_laws_per_topic=2,  # Only 2 laws per topic
        max_total_laws=3       # Total max 3 laws
    )
    
    if result:
        print("\n✅ Test successful!")
        print(f"Topics scraped: {result.get('total_topics_scraped', 0)}")
        print(f"Total laws scraped: {result.get('total_laws_scraped', 0)}")
        
        # Show what we got
        all_laws = result.get('all_laws', [])
        if all_laws:
            print("\nLaws scraped:")
            for i, law in enumerate(all_laws, 1):
                topic_info = law.get('topic_page_info', {})
                topic_title = topic_info.get('title', 'Unknown')
                law_title = law.get('title', 'Unknown')
                law_ref = law.get('reference', 'Unknown')
                print(f"  {i}. {law_title} ({law_ref}) - from {topic_title}")
    else:
        print("\n❌ Test failed!")

if __name__ == "__main__":
    test_multiple_topics() 