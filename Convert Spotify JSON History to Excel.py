import json
import pandas as pd
import glob
from pathlib import Path

def convert_spotify_json_to_excel(input_folder, output_file):
    """
    Convert Spotify JSON streaming history files to Excel with proper formatting.
    
    Parameters:
    input_folder (str): Path to folder containing Spotify JSON files
    output_file (str): Path for output Excel file
    """
    all_data = []
    
    json_files = glob.glob(str(Path(input_folder) / "*.json"))
    
    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            all_data.extend(data)
    

    df = pd.DataFrame(all_data) 
    df['ts'] = pd.to_datetime(df['ts']).dt.tz_localize(None)
    df['minutes_played'] = df['ms_played'] / 60000
    
    column_rename = {
        'ts': 'Timestamp',
        'platform': 'Platform',
        'ms_played': 'Milliseconds Played',
        'minutes_played': 'Minutes Played',
        'conn_country': 'Country',
        'ip_addr': 'IP Address',
        'master_metadata_track_name': 'Track Name',
        'master_metadata_album_artist_name': 'Artist',
        'master_metadata_album_album_name': 'Album',
        'spotify_track_uri': 'Track URI',
        'episode_name': 'Podcast Episode',
        'episode_show_name': 'Podcast Show',
        'spotify_episode_uri': 'Episode URI',
        'reason_start': 'Start Reason',
        'reason_end': 'End Reason',
        'shuffle': 'Shuffle Mode',
        'skipped': 'Skipped',
        'offline': 'Offline Mode',
        'offline_timestamp': 'Offline Timestamp',
        'incognito_mode': 'Private Session'
    }
    
    df = df.rename(columns=column_rename)
    

    boolean_columns = ['Shuffle Mode', 'Skipped', 'Offline Mode', 'Private Session']
    for col in boolean_columns:
        df[col] = df[col].map({True: 'Yes', False: 'No'})
    

    df['Offline Timestamp'] = pd.to_datetime(df['Offline Timestamp']).dt.tz_localize(None)
    
 
    column_order = [
        'Timestamp',
        'Track Name',
        'Artist',
        'Album',
        'Minutes Played',
        'Milliseconds Played',
        'Platform',
        'Country',
        'Start Reason',
        'End Reason',
        'Shuffle Mode',
        'Skipped',
        'Offline Mode',
        'Private Session',
        'Track URI',
        'Podcast Episode',
        'Podcast Show',
        'Episode URI',
        'IP Address',
        'Offline Timestamp'
    ]
    
  
    existing_columns = [col for col in column_order if col in df.columns]
    df = df[existing_columns]
    
   
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        
        df.to_excel(writer, index=False, sheet_name='Streaming History')
        
        worksheet = writer.sheets['Streaming History']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            ) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
    
    print(f"Processed {len(json_files)} files with {len(df)} total records")
    print(f"Excel file saved as: {output_file}")
    
  
    print("\nQuick Statistics:")
    print(f"Total listening time: {df['Minutes Played'].sum():.2f} minutes")
    print(f"Number of unique tracks: {df['Track Name'].nunique()}")
    print(f"Number of unique artists: {df['Artist'].nunique()}")
    print(f"Date range: {df['Timestamp'].min()} to {df['Timestamp'].max()}")

if __name__ == "__main__":
    input_folder = "C:/Users/Admin/Desktop/Spotify Project/input_folder"  
    output_file = "spotify_streaming_history.xlsx" 
    convert_spotify_json_to_excel(input_folder, output_file)
