#!/usr/bin/env python3
"""
Script to generate individual company detail JSON files from CSV data
"""

import pandas as pd
import json
import os
import glob
from datetime import datetime
import re

def parse_date_from_filename(filename):
    """Extract date from filename like 23.08.2025.csv"""
    try:
        date_part = filename.replace('.csv', '')
        parts = date_part.split('.')
        if len(parts) == 3:
            day, month, year = parts
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except:
        pass
    return None

def process_links(links_str):
    """Process and clean links from CSV"""
    if not links_str or pd.isna(links_str):
        return []
        
    links_str = str(links_str).strip()
    if not links_str or links_str.lower().startswith('no links found'):
        return []
    
    processed_links = []
    
    # Try different delimiters
    potential_links = []
    for delimiter in [',', ';', '\n', '|', '\t']:
        if delimiter in links_str:
            potential_links = [link.strip() for link in links_str.split(delimiter)]
            break
    
    if not potential_links:  # Single link
        potential_links = [links_str]
    
    # Clean and validate each link
    for link in potential_links:
        link = link.strip()
        if link and len(link) > 10:
            # Add protocol if missing
            if not link.startswith(('http://', 'https://')):
                if link.startswith('www.'):
                    link = 'https://' + link
                elif '.' in link and not link.startswith('no '):
                    link = 'https://' + link
            
            # Validate it looks like a URL
            if any(domain in link for domain in ['http', 'www.', '.com', '.org', '.net', '.in']):
                processed_links.append(link)
    
    return processed_links

def generate_company_json_files(csv_folder='scrapped_output', api_folder='api'):
    """Generate individual JSON files for each company from CSV data"""
    
    # Create api folder if it doesn't exist
    os.makedirs(api_folder, exist_ok=True)
    
    # Find all CSV files
    csv_files = glob.glob(os.path.join(csv_folder, '*.csv'))
    
    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        parsed_date = parse_date_from_filename(filename)
        
        if not parsed_date:
            print(f"Could not parse date from {filename}")
            continue
            
        print(f"Processing {filename} (Date: {parsed_date})")
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            df.columns = df.columns.str.strip()
            
            companies_processed = 0
            
            # Process each company
            for _, row in df.iterrows():
                company_name = str(row['Company_Name']).strip()
                extracted_text = str(row['Extracted_Text']) if 'Extracted_Text' in row and not pd.isna(row['Extracted_Text']) else ''
                extracted_links = str(row['Extracted_Links']) if 'Extracted_Links' in row and not pd.isna(row['Extracted_Links']) else ''
                
                # Process links
                processed_links = process_links(extracted_links)
                
                # Create JSON data matching the existing structure
                json_data = {
                    "company_name": company_name,
                    "extracted_text": extracted_text,
                    "links_raw": extracted_links,
                    "processed_links": processed_links,
                    "date": parsed_date
                }
                
                # Generate filename: company-details-2025-08-23-RELIANCE LTD.json
                safe_company_name = company_name.replace('/', '-').replace('\\', '-')
                json_filename = f"company-details-{parsed_date}-{safe_company_name}.json"
                json_filepath = os.path.join(api_folder, json_filename)
                
                # Write JSON file
                with open(json_filepath, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                
                companies_processed += 1
            
            print(f"Generated {companies_processed} JSON files for {parsed_date}")
            
            # Generate the company news summary file that the frontend expects
            companies_with_news = []
            companies_no_news = []
            
            # Re-read the CSV to categorize companies
            for _, row in df.iterrows():
                company_name = str(row['Company_Name']).strip()
                extracted_text = str(row['Extracted_Text']) if 'Extracted_Text' in row and not pd.isna(row['Extracted_Text']) else ''
                extracted_links = str(row['Extracted_Links']) if 'Extracted_Links' in row and not pd.isna(row['Extracted_Links']) else ''
                
                # Use the same categorization logic as the Flask app
                text_str = extracted_text.lower()
                if "no significant news" in text_str or "no news" in text_str or "no significant corporate developments" in text_str:
                    news_category = "no_news"
                else:
                    news_category = "has_news"
                
                company_data = {
                    'name': company_name,
                    'text': extracted_text,
                    'links_raw': extracted_links,
                    'has_content': len(extracted_text.strip()) > 0
                }
                
                if news_category == "has_news":
                    companies_with_news.append(company_data)
                else:
                    companies_no_news.append(company_data)
            
            # Sort alphabetically within each category
            companies_with_news.sort(key=lambda x: x['name'])
            companies_no_news.sort(key=lambda x: x['name'])
            
            summary_data = {
                'date': parsed_date,
                'companies_with_news': companies_with_news,
                'companies_no_news': companies_no_news,
                'total_companies': len(companies_with_news) + len(companies_no_news),
                'news_count': len(companies_with_news),
                'no_news_count': len(companies_no_news)
            }
            
            summary_filename = f"company-news-{parsed_date}.json"
            summary_filepath = os.path.join(api_folder, summary_filename)
            
            with open(summary_filepath, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            
            print(f"Generated summary file: {summary_filename}")
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    # Generate available-dates.json
    generate_available_dates(api_folder)

def generate_available_dates(api_folder):
    """Generate available-dates.json file"""
    try:
        # Find all company-details JSON files
        json_files = glob.glob(os.path.join(api_folder, 'company-details-*.json'))
        dates = set()
        
        for json_file in json_files:
            filename = os.path.basename(json_file)
            # Extract date from filename: company-details-2025-08-23-COMPANY.json
            parts = filename.split('-')
            if len(parts) >= 4:
                try:
                    date_str = f"{parts[2]}-{parts[3]}-{parts[4]}"
                    datetime.strptime(date_str, '%Y-%m-%d')  # Validate date
                    dates.add(date_str)
                except:
                    continue
        
        # Convert to list and sort
        dates_list = []
        for date_str in sorted(dates, reverse=True):
            try:
                display_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%A, %B %d, %Y')
                dates_list.append({
                    'date': date_str,
                    'display_date': display_date,
                    'filename': f"{date_str.split('-')[2]}.{date_str.split('-')[1]}.{date_str.split('-')[0]}.csv"
                })
            except:
                continue
        
        # Write available-dates.json
        available_dates_file = os.path.join(api_folder, 'available-dates.json')
        with open(available_dates_file, 'w', encoding='utf-8') as f:
            json.dump(dates_list, f, indent=2, ensure_ascii=False)
        
        print(f"Generated available-dates.json with {len(dates_list)} dates")
        
    except Exception as e:
        print(f"Error generating available-dates.json: {e}")

if __name__ == "__main__":
    print("Starting JSON file generation...")
    generate_company_json_files()
    print("JSON file generation completed!")