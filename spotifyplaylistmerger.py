from dotenv import load_dotenv
load_dotenv()

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

print("SPOTIPY_CLIENT_ID:", os.getenv("SPOTIPY_CLIENT_ID"))
print("SPOTIPY_REDIRECT_URI:", repr(os.getenv("SPOTIPY_REDIRECT_URI")))

# Load environment variables from .env file
load_dotenv()

# Set up Spotify authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv('SPOTIPY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
    redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'),
    scope="playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private"
))

def get_all_playlists():
    """Fetch all playlists for the current user"""
    playlists = []
    results = sp.current_user_playlists(limit=50)
    
    while results:
        playlists.extend(results['items'])
        if results['next']:
            results = sp.next(results)
        else:
            break
    
    return playlists

def get_playlist_tracks(playlist_id):
    """Get all tracks from a specific playlist"""
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    
    while results:
        tracks.extend(results['items'])
        if results['next']:
            results = sp.next(results)
        else:
            break
    
    return tracks

def merge_playlists(playlist_ids, new_playlist_name):
    """Merge multiple playlists into one new playlist with error handling for invalid URIs."""
    user_id = sp.current_user()['id']
    
    # Create new playlist
    new_playlist = sp.user_playlist_create(
        user=user_id,
        name=new_playlist_name,
        public=True,
        description="Merged playlist created with Playlist Merger"
    )
    
    print(f"Created new playlist: {new_playlist_name}")
    
    # Collect all unique track URIs
    all_track_uris = set()
    
    for playlist_id in playlist_ids:
        print(f"Processing playlist...")
        tracks = get_playlist_tracks(playlist_id)
        
        for item in tracks:
            # Extract and validate URI
            uri = (item.get('track') or {}).get('uri')
            if uri and isinstance(uri, str) and uri.startswith('spotify:track:'):
                all_track_uris.add(uri)
            else:
                print("Skipping unsupported URI:", uri)  # Debug output
    
    # Convert set to list
    track_list = list(all_track_uris)
    print(f"Found {len(track_list)} unique valid tracks")
    
    # Add tracks to new playlist (Spotify limits to 100 tracks per request)
    for i in range(0, len(track_list), 100):
        batch = track_list[i:i+100]
        try:
            sp.playlist_add_items(new_playlist['id'], batch)
            print(f"Added {len(batch)} tracks")
        except Exception as e:
            print(f"Error adding tracks batch {i}: {e}")
    
    print(f"\nSuccess! Merged playlist created: {new_playlist['external_urls']['spotify']}")
    return new_playlist

def main():
    print ("Spotify Playlist Merger 🎵\n")
    
    # Get user info
    user = sp.current_user()
    print(f"Logged in as: {user['display_name']}\n")
    
    # Get all playlists
    print("Fetching your playlists...\n")
    playlists = get_all_playlists()
    
    # Display playlists
    print("Your playlists:")
    for i, playlist in enumerate(playlists, 1):
        track_count = playlist['tracks']['total']
        print(f"{i}. {playlist['name']} ({track_count} tracks)")
    
    # Get user input for which playlists to merge
    print("\nEnter the numbers of playlists you want to merge (comma-separated)")
    print("Example: 1,3,5")
    selection = input("Your selection: ")
    
    # Parse selection
    selected_indices = [int(x.strip()) - 1 for x in selection.split(',')]
    selected_playlist_ids = [playlists[i]['id'] for i in selected_indices]
    
    # Get name for new playlist
    new_name = input("\nEnter a name for the merged playlist: ")
    
    # Merge playlists
    print("\nMerging playlists...\n")
    merge_playlists(selected_playlist_ids, new_name)

if __name__ == "__main__":
    main()