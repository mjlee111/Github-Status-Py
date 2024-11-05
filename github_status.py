import requests
from datetime import datetime, timedelta
from getpass import getpass
from collections import Counter
from tqdm import tqdm
from colorama import init, Fore, Style
import matplotlib.pyplot as plt
import seaborn as sns

# Initialize colorama and set plot style
init()
plt.style.use('seaborn')
sns.set_palette("husl")

class GitHubStats:
    def __init__(self, username, token):
        self.username = username
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'
        self.start_date = datetime.now()
        self.end_date = self.start_date - timedelta(days=90)

    def get_user_stats(self):
        print(f"\n{Fore.CYAN}Fetching repository information...{Style.RESET_ALL}")
        repos_url = f'{self.base_url}/users/{self.username}/repos'
        repos = requests.get(repos_url, headers=self.headers).json()

        # Initialize statistics
        total_stars = 0
        fork_count = 0
        repo_views = []
        repo_stats = []

        # Progress bar for repository analysis
        for repo in tqdm(repos, desc="Analyzing repositories"):
            total_stars += repo['stargazers_count']
            fork_count += repo['forks_count']

            views_url = f'{self.base_url}/repos/{self.username}/{repo["name"]}/traffic/views'
            views_data = requests.get(views_url, headers=self.headers).json()
            
            view_count = sum(view['count'] for view in views_data.get('views', []))
            repo_views.append({'name': repo['name'], 'views': view_count})
            repo_stats.append({'name': repo['name'], 'stars': repo['stargazers_count']})

        print(f"\n{Fore.CYAN}Fetching contribution data...{Style.RESET_ALL}")
        contributions_url = f'{self.base_url}/search/commits?q=author:{self.username}'
        contributions = requests.get(contributions_url, headers=self.headers).json()
        contribution_count = contributions.get('total_count', 0)

        print(f"{Fore.CYAN}Analyzing code changes...{Style.RESET_ALL}")
        total_lines_changed = self._get_total_lines_changed()

        languages = self._get_language_stats(repos)
        
        return {
            'total_stars': total_stars,
            'top_starred_repos': sorted(repo_stats, key=lambda x: x['stars'], reverse=True)[:5],
            'total_forks': fork_count,
            'contribution_count': contribution_count,
            'total_lines_changed': total_lines_changed,
            'total_views': sum(repo['views'] for repo in repo_views),
            'top_viewed_repos': sorted(repo_views, key=lambda x: x['views'], reverse=True)[:5],
            'languages': languages
        }

    def _get_total_lines_changed(self):
        events_url = f'{self.base_url}/users/{self.username}/events'
        events = requests.get(events_url, headers=self.headers).json()
        
        total_lines = 0
        for event in tqdm(events, desc="Analyzing commits"):
            if event['type'] == 'PushEvent':
                for commit in event['payload']['commits']:
                    commit_url = f'{self.base_url}/repos/{event["repo"]["name"]}/commits/{commit["sha"]}'
                    commit_data = requests.get(commit_url, headers=self.headers).json()
                    if 'stats' in commit_data:
                        total_lines += commit_data['stats'].get('total', 0)
        
        return total_lines

    def _get_language_stats(self, repos):
        language_stats = Counter()
        print(f"\n{Fore.CYAN}Analyzing programming languages...{Style.RESET_ALL}")
        for repo in tqdm(repos, desc="Fetching language data"):
            if repo['language']:
                language_stats[repo['language']] += 1
        return dict(language_stats.most_common())

def create_visualizations(result, username):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    end_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    plt.figure(figsize=(15, 10))
    plt.suptitle(f'GitHub Statistics for {username}\nData collected: {end_date} to {current_time}', 
                 fontsize=16, y=1.02)

    # 1. Top Starred Repositories Bar Chart
    plt.subplot(2, 2, 1)
    repos = [repo['name'] for repo in result['top_starred_repos']]
    stars = [repo['stars'] for repo in result['top_starred_repos']]
    
    sns.barplot(x=stars, y=repos)
    plt.title('Top Starred Repositories')
    plt.xlabel('Stars')
    
    # 2. Top Viewed Repositories Bar Chart
    plt.subplot(2, 2, 2)
    view_repos = [repo['name'] for repo in result['top_viewed_repos']]
    views = [repo['views'] for repo in result['top_viewed_repos']]
    sns.barplot(x=views, y=view_repos)
    plt.title('Most Viewed Repositories (Last 14 days)')
    plt.xlabel('Views')

    # 3. Programming Languages Pie Chart
    plt.subplot(2, 2, 3)
    languages = result['languages']
    if languages:
        plt.pie(languages.values(), labels=languages.keys(), autopct='%1.1f%%')
        plt.title('Programming Languages Distribution')

    # 4. General Statistics Bar Chart
    plt.subplot(2, 2, 4)
    metrics = ['Stars', 'Forks', 'Contributions']
    values = [result['total_stars'], result['total_forks'], result['contribution_count']]
    sns.barplot(x=metrics, y=values)
    plt.title('General Statistics')
    plt.yscale('log')

    plt.tight_layout()
    
    filename = f'github_stats_{username}_{datetime.now().strftime("%Y%m%d_%H%M")}.png'
    plt.savefig(filename, bbox_inches='tight', dpi=300)
    print(f"\n{Fore.GREEN}Visualizations saved as '{filename}'{Style.RESET_ALL}")
    print(f"Data collection period: {end_date} to {current_time}")

def display_results(result):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    end_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    print(f"\n{Fore.GREEN}=== GitHub Statistics ==={Style.RESET_ALL}")
    print(f"Data collection period: {end_date} to {current_time}")
    
    # General stats
    print(f"\n{Fore.YELLOW}General Statistics:{Style.RESET_ALL}")
    print(f"Total Stars: {result['total_stars']}")
    print(f"Total Forks: {result['total_forks']}")
    print(f"Total Contributions: {result['contribution_count']}")
    print(f"Total Lines Changed: {result['total_lines_changed']}")
    print(f"Total Repository Views (Last 14 days): {result['total_views']}")
    
    # Top starred repositories
    print(f"\n{Fore.YELLOW}Top 5 Starred Repositories:{Style.RESET_ALL}")
    for idx, repo in enumerate(result['top_starred_repos'], 1):
        print(f"{idx}. {repo['name']}: {repo['stars']} stars")
    
    # Top viewed repositories
    print(f"\n{Fore.YELLOW}Top 5 Viewed Repositories (Last 14 days):{Style.RESET_ALL}")
    for idx, repo in enumerate(result['top_viewed_repos'], 1):
        print(f"{idx}. {repo['name']}: {repo['views']} views")
    
    # Language distribution
    print(f"\n{Fore.YELLOW}Programming Languages Distribution:{Style.RESET_ALL}")
    for lang, count in result['languages'].items():
        print(f"{lang}: {count} repositories")

def main():
    print(f"{Fore.GREEN}=== GitHub Statistics Analyzer ==={Style.RESET_ALL}")
    username = input("Enter GitHub username: ")
    token = getpass("Enter GitHub token: ")

    try:
        stats = GitHubStats(username, token)
        result = stats.get_user_stats()
        
        # Display text results
        display_results(result)
        
        # Create and save visualizations
        print(f"\n{Fore.CYAN}Generating visualizations...{Style.RESET_ALL}")
        create_visualizations(result, username)

    except Exception as e:
        print(f"\n{Fore.RED}Error occurred: {str(e)}")
        print("Please check if your GitHub token is valid.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()