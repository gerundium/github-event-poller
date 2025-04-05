import requests
import time
import os
from datetime import datetime
from typing import Optional

def check_required_variables():
    """Check if required environment variables are set and not empty."""
    required_vars = {
        "GITHUB_REPO": GITHUB_REPO,
        "GITHUB_BRANCH": GITHUB_BRANCH,
        "GITHUB_TOKEN": GITHUB_TOKEN,
        "GITHUB_API_URL": GITHUB_API_URL,
        "TRIGGER_URL": TRIGGER_URL,
        "DOCKER_IMAGE_URL": DOCKER_IMAGE_URL,
        "CHECK_INTERVAL": CHECK_INTERVAL,
    }
    
    for var_name, var_value in required_vars.items():
        if not var_value:
            raise ValueError(f"Environment variable {var_name} is not set or is empty.")
        
# Function to strip both single and double quotes safely
def strip_quotes(value: Optional[str]) -> Optional[str]:
    return value.strip('"') if value else value

# GitHub repo details
GITHUB_REPO = strip_quotes(os.getenv("GITHUB_REPO_ENV", ""))  # Get from env or default
GITHUB_BRANCH = strip_quotes(os.getenv("GITHUB_BRANCH_ENV", ""))  # Get from env or default
GITHUB_TOKEN = strip_quotes(os.getenv("GITHUB_TOKEN_ENV", ""))  # Get from env or default
# Ensure CHECK_INTERVAL is always a valid integer
CHECK_INTERVAL_STR = strip_quotes(os.getenv("CHECK_INTERVAL_ENV", "60"))
try:
    CHECK_INTERVAL = int(CHECK_INTERVAL_STR)
except ValueError:
    raise ValueError(f"Invalid CHECK_INTERVAL value: {CHECK_INTERVAL_STR}. Must be an integer.")

# GitHub API URL
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/commits?sha={GITHUB_BRANCH}"
TRIGGER_URL = strip_quotes(os.getenv("TRIGGER_URL_ENV", f"http://localhost:12001/github"))
DOCKER_IMAGE_URL = strip_quotes(os.getenv("DOCKER_IMAGE_URL_ENV", "https://hub.docker.com/v2/repositories/gerundium/brand-voting-app/tags/"))

def get_latest_commit() -> Optional[dict]:
    """Fetch the latest commit from the GitHub repository."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(GITHUB_API_URL, headers=headers)
    
    if response.status_code == 200:
        commits = response.json()
        return commits[0] if commits else None
    elif response.status_code == 401:
        print("Error: Unauthorized. Check your GitHub token.")
        print(f"GITHUB_API_URL: {GITHUB_API_URL}")
        return None
    else:
        print(f"Error fetching commits: {response.status_code}, {response.text}")
        return None

def check_docker_image_exists(commit_sha: str) -> bool:
    """Check if the Docker image exists for the given commit SHA."""
    response = requests.get(DOCKER_IMAGE_URL)
    if response.status_code == 200:
        tags = response.json().get("results", [])
        for tag in tags:
            if tag.get("name") == commit_sha:
                return True
    return False

def main():
    check_required_variables()  # Ensure all necessary variables are set
    last_checked_commit = None
    
    while True:
        commit = get_latest_commit()
        
        if commit:
            commit_sha = commit['sha'][:7]  # Shorten SHA like `git rev-parse --short HEAD`
            commit_message = commit['commit']['message']
            commit_date = commit['commit']['committer']['date']
            
            if commit_sha != last_checked_commit:
                print(f"Analyzing commit: {commit_date} {commit_sha} {commit_message}")
                last_checked_commit = commit_sha
                
                if commit_message.strip() == "trigger: Build new image":
                    print("Checking if Docker image exists...")
                    if not check_docker_image_exists(commit_sha):
                        print("Image does not exist. Triggering build...")
                        print(f"Connecting to trigger URL...", {TRIGGER_URL})
                        response = requests.post(TRIGGER_URL, timeout=5, json={'message': 'KickIT'}, headers={"Content-Type":"application/json"})
                        print(f"Trigger response: {response.status_code}, {response.text}")
                    else:
                        print("Image exists. Skipping trigger.")
                else:
                    print(f"Nothing to do. Going to sleep. Last checked commit: {last_checked_commit}")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
