# We no longer need asyncio or playwright for this script
from collepedia import CollepediaClient, CollepediaConnectionError

def fetch_and_save_links():
    """
    Uses the CollepediaClient to fetch all post links and save them to a file.
    """
    print("Initializing Collepedia client...")
    client = CollepediaClient()
    
    try:
        # Fetch all posts. Set a high limit to ensure we get everything.
        print("Fetching all posts from the feed... this may take a moment.")
        fetched_count = client.fetch_posts(max_posts=10000)
        print(f"Successfully fetched metadata for {fetched_count} posts.")

        # Get the list of post dictionaries
        all_posts = client.get_all_posts()

        # Extract just the 'link' from each post
        all_links = [post['link'] for post in all_posts if post.get('link')]

        if not all_links:
            print("❗️ No links were found.")
            return

        # Save the links to the file, which will be used by the visitor script
        with open("links.txt", "w", encoding="utf-8") as f:
            for link in all_links:
                f.write(link + "\n")
        
        print(f"✅ Successfully saved {len(all_links)} unique links to links.txt")

    except CollepediaConnectionError as e:
        print(f"❗️ A connection error occurred: {e}")
    except Exception as e:
        print(f"❗️ An unexpected error occurred: {e}")

if __name__ == "__main__":
    fetch_and_save_links()
